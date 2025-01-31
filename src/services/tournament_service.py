from asyncio import to_thread
import base64
from datetime import datetime
import json
from typing import List
import uuid
import zlib
from fastapi import HTTPException, UploadFile, status
from src.models.cloudinary_model import CloudinaryModel
from src.models.participant_model import Participant
from src.models.tournament_participants import TournamentParticipants
from src.models.tournaments import StatusTournament, Tournament, TypeTournament
from src.models.user_model import User
from src.schemas.organizer_schemas.organizer_dto import OrganizerDTO
from src.schemas.participant_schemas.participant_dto import ConjuntInscriptionDTO, ParticipantDTO, TournamentParticipantDTO
from src.schemas.participant_schemas.participant_result_tour import ParticipantResultTour
from src.schemas.tournament_schemas.data_update import DataUpdate
from src.schemas.tournament_schemas.tournament_create import TournamentCreate
from src.schemas.tournament_schemas.tournament_dto import TournamentDTO
from src.schemas.tournament_schemas.tournament_response import TournamentResponse
from sqlmodel import select, or_
from sqlmodel.ext.asyncio.session import AsyncSession
from fastapi.responses import JSONResponse
from sqlalchemy.orm import selectinload, joinedload
import random
from src.routers.websocket_router import manager
from src.schemas.tournament_schemas.tournament_socket import TournamentSocket
from src.schemas.tournament_schemas.tournament_update import TournamentUpdate
from src.schemas.user_schema.user_full import UserFull


class TournamentService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_tournament(self, tournament: TournamentCreate, user: UserFull, image: UploadFile | None):
        try:
            if tournament.type == TypeTournament.SIMPLE:
                data = await self.generate_matchups_simple(tournament.number_participants)
            if tournament.type == TypeTournament.DOUBLE:
                data = await self.generate_matchups_double(tournament.number_participants)

            new_tournament: Tournament = Tournament(**tournament.model_dump(), data = await self.compress_string(data= data), organizer_id= user.full.id)
            
            result = {}
            if image is not None:
                result = await to_thread(
                    CloudinaryModel().upload_image, 
                    image,
                    "tournament",
                    new_tournament.id
                )

            if image is not None:
                new_tournament.url_image = result.get('secure_url', None)

            self.session.add(new_tournament)

            await self.session.commit()

            await manager.broadcast(
                        {
                            "event": "create_tournament", 
                            "tournament":{
                                "id": new_tournament.id,
                                "name": new_tournament.name,
                                "start": new_tournament.start.isoformat()
                            },
                            "message": "Nuevo torneo creado",
                        }
                    )
            
            await manager.add_tournament(TournamentSocket(
                id= new_tournament.id,
                name= new_tournament.name,
                start= new_tournament.start
            ))

            return JSONResponse(
                content={
                    "tournament_id": new_tournament.id
                    },
                status_code=status.HTTP_201_CREATED
            )
        except Exception as e:
            raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, "Error al intentar crear torneo")

    async def get_all_tournaments(self, status_filter: StatusTournament | None):
        try:
            if status_filter is None:
                stmt = select(Tournament).options(
                    joinedload(Tournament.organizer), joinedload(Tournament.participants))
            else:
                stmt = select(Tournament).options(
                    joinedload(Tournament.organizer), joinedload(Tournament.participants)
                    ).where(Tournament.status == status_filter)

            tournaments: List[Tournament] = (await self.session.exec(stmt)).unique().all()

            list_tour: List[TournamentDTO] = [
                TournamentDTO(
                    **tour.model_dump(),
                    number_registered= len(tour.participants),
                    organizer= OrganizerDTO(
                        **tour.organizer.model_dump()
                    )
                ).model_dump(mode='json')
                for tour in tournaments
            ]

            return JSONResponse(
                content={
                    "tournaments": list_tour, 
                    "length": len(list_tour)
                },
                status_code= status.HTTP_200_OK
            )

        except Exception as e:
            print(f"Error al obtener torneos: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error al intentar obtener torneos"
            )
        
    async def get_name_tournaments(self, name_filter: str):
        try:
            stmt = select(Tournament).options(joinedload(Tournament.organizer), joinedload(Tournament.participants)).where(Tournament.name.like(f"%{name_filter}%"))
            tournaments: List[Tournament] = (await self.session.exec(stmt)).unique().all()

            list_tour: List[TournamentDTO] = [
                TournamentDTO(
                    **tour.model_dump(),
                    number_registered= len(tour.participants),
                    organizer= OrganizerDTO(
                        **tour.organizer.model_dump()
                    )
                ).model_dump(mode='json')
                for tour in tournaments
            ]

            return JSONResponse(
                content={
                    "tournaments": list_tour, 
                    "length": len(list_tour)
                },
                status_code= status.HTTP_200_OK
            )

        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error al intentar obtener torneos"
            )
        
    async def get_tournament(self, id: str):
        try:
            stmt = (
                select(Tournament)
                .options(
                    joinedload(Tournament.organizer),
                    joinedload(Tournament.participants).joinedload(TournamentParticipants.participant)
                )
                .where(Tournament.id == id)
            )

            tournament = (await self.session.exec(stmt)).unique().first()
            tournament.data = await self.decompress_string(tournament.data)

            if tournament is None:
                return JSONResponse(
                    content={"detail": "Torneo no encontrado"},
                    status_code=status.HTTP_404_NOT_FOUND
                )

            list_participants: List[ConjuntInscriptionDTO] = [
                ConjuntInscriptionDTO(
                    participant=ParticipantDTO(**participant.participant.model_dump()),
                    tournament_participant=TournamentParticipantDTO(**participant.model_dump())
                )
                for participant in tournament.participants
            ]

            tour_resp = TournamentResponse(
                **tournament.model_dump(),
                number_registered=len(tournament.participants),
                organizer=OrganizerDTO(**tournament.organizer.model_dump()),
                list_participants=list_participants
            )

            return JSONResponse(
                content={"tournament": tour_resp.model_dump(mode='json')},
                status_code=status.HTTP_200_OK
            )

        except Exception as e:
            print(f"Error al obtener torneos: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error al intentar obtener torneos"
            )
        
    async def update_data(self, tournament_id: str, data: DataUpdate, user: UserFull):
        try:
            sttmt = select(Tournament).where(Tournament.id == tournament_id, Tournament.organizer_id == user.full.id)
            tournament: Tournament | None = (await self.session.exec(sttmt)).first()

            if tournament is None:
                return JSONResponse(
                    content={
                        "detail": "Torneo no entontrado", 
                    },
                    status_code= status.HTTP_404_NOT_FOUND
                )
            
            if tournament.organizer_id != user.full.id:
                return JSONResponse(
                    content={
                        "detail": "Solo el creador puedo actualizar el torneo", 
                    },
                    status_code= status.HTTP_401_UNAUTHORIZED
                )

            tournament.data = await self.compress_string(data.data)

            await self.session.commit()

            return JSONResponse(
                content={
                    "detail": "Datos del torneo actualizdo con éxito!",
                },
                status_code= status.HTTP_204_NO_CONTENT
            )
        except Exception as e:
            raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, "Error al intentar actualizar torneo")
        
    async def update_status(self, status_tour: StatusTournament, tournament_id: str, user: UserFull):
        try:
            sttmt = select(Tournament).where(Tournament.id == tournament_id, Tournament.organizer_id == user.full.id)
            tournament: Tournament | None = (await self.session.exec(sttmt)).first()

            if tournament is None:
                return JSONResponse(
                    content={
                        "detail": "Torneo no entontrado", 
                    },
                    status_code= status.HTTP_404_NOT_FOUND
                )
            
            if tournament.organizer_id != user.full.id:
                return JSONResponse(
                    content={
                        "detail": "Solo el creador puedo actualizar el torneo", 
                    },
                    status_code= status.HTTP_403_FORBIDDEN
                )
            
            if tournament.status == StatusTournament.CANCELADO or tournament.status == StatusTournament.FINALIZADO:
                return JSONResponse(
                    content={
                        "detail": "No es posible actualizar el torneo", 
                    },
                    status_code= status.HTTP_400_BAD_REQUEST
                )
            
            tournament.status = status_tour
            if status_tour == StatusTournament.CURSO:
                sttmt_parts = select(TournamentParticipants).where(
                    TournamentParticipants.tournament_id == tournament_id, TournamentParticipants.confirm == True
                    ).join(Participant, Participant.id == TournamentParticipants.participant_id
                           ).options(selectinload(TournamentParticipants.participant))
                 
                participants: List[TournamentParticipants] = (await self.session.exec(sttmt_parts)).unique().all()

                if len(participants) == 0:
                    return JSONResponse(
                        content={
                            "detail": "No hay participantes confirmados", 
                        },
                        status_code= status.HTTP_400_BAD_REQUEST
                    )
                # tournament.data = await self.generate_matchups_double(tournament.number_participants)## sacar esto
                new_data = await self.shuffle_participants(await self.decompress_string(tournament.data), participants, tournament.number_participants, tournament.type)
                
                tournament.data = await self.compress_string(new_data)

            if status_tour == StatusTournament.FINALIZADO:
                data = tournament.data
                data_tournament = await self.decompress_string(data)
                results = await self.finished_tournament(number_participants= tournament.number_participants, data= data_tournament, type= tournament.type)

                for participant in results:
                    if participant is None: continue

                    sttmt = select(TournamentParticipants).where(TournamentParticipants.participant_id == participant, TournamentParticipants.tournament_id == tournament_id)
                    participant_tour: TournamentParticipants | None = (await self.session.exec(sttmt)).first()

                    if participant_tour is None: continue

                    participant_tour.points = results[participant]['points']
                    participant_tour.win = results[participant]['win']
                    participant_tour.lose = results[participant]['lose']
                    participant_tour.final_position = results[participant]['position']

            tournament.is_open = False

            await self.session.commit()

            await manager.broadcast(
                        {
                            "event": "update_tournament", 
                            "tournament":{
                                "id": tournament.id,
                                "name": tournament.name,
                                "start": tournament.start.isoformat()
                            },
                            "message": f"Actualización: {status_tour}",
                        }
                    )

            return JSONResponse(
                content={
                    "detail": "Datos del torneo actualizdo con éxito!",
                },
                status_code= status.HTTP_204_NO_CONTENT
            )
        except Exception as e:
            raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, "Error al intentar actualizar torneo")
        
    async def update_tournament(self, tournament_update: TournamentUpdate, user: UserFull, image: UploadFile | None):
        try:
            sttmt = select(Tournament).where(Tournament.id == tournament_update.id, Tournament.organizer_id == user.full.id)
            tournament: Tournament | None = (await self.session.exec(sttmt)).first()

            if tournament is None:
                return JSONResponse(
                    content={
                        "detail": "Torneo no entontrado", 
                    },
                    status_code= status.HTTP_404_NOT_FOUND
                )
            
            if tournament.organizer_id != user.full.id:
                return JSONResponse(
                    content={
                        "detail": "Solo el creador puedo actualizar el torneo", 
                    },
                    status_code= status.HTTP_403_FORBIDDEN
                )
            
            if tournament.status != StatusTournament.PROXIMO:
                return JSONResponse(
                    content={
                        "detail": "No es posible actualizar el torneo", 
                    },
                    status_code= status.HTTP_400_BAD_REQUEST
                )
            
            tournament.name = tournament_update.name
            tournament.description = tournament_update.description
            tournament.start = tournament_update.start
            tournament.end = tournament_update.end

            result = {}
            if image is not None:
                result = await to_thread(
                    CloudinaryModel().upload_image, 
                    image,
                    "tournament",
                    tournament_update.id
                )

            if image is not None:
                tournament.url_image = result.get('secure_url', None)

            await self.session.commit()

            return JSONResponse(
                content={
                    "detail": "Torneo actualizado correctamente",
                },
                status_code= status.HTTP_204_NO_CONTENT
            )
        except Exception as e:
            raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, "Error al intentar actualizar torneo")
        
    async def generate_matchups_simple(self, num_participants, double=False):
        if num_participants not in [4, 8, 16, 32, 64]:
            raise ValueError("La cantidad de participantes debe ser 8, 16, 32 o 64.")

        list_uuid = [str(uuid.uuid4())  for i in range(num_participants-1)]

        matchups = []
        round_number = 1
        lap = 0
        base_num = num_participants//2
        base_index = num_participants//2

        for index, value in enumerate(list_uuid):
            if index != 0 and index % base_num == 0:
                base_num = base_num // 2
                round_number += 1

            if double == True:
                if base_num == 1:
                    name = 'Semifinal'
            else: 
                if base_num == 2:
                    name = 'Semifinal'
                if base_num == 1:
                    name = 'Final'

            if lap == 2:
                lap = 0
            if lap == 0:
                get_uuid = None if index == len(list_uuid)-1 else list_uuid[index+base_index]
            if lap == 1:
                get_uuid = None if index == len(list_uuid)-1 else list_uuid[index+base_index-lap]
                base_index -= 1
            
          
            match = {
                "id": list_uuid[index],
                "name": name if double and base_num == 1 else (name if not double and base_num in [2,1] else f"Round {round_number}"),
                "nextMatchId": get_uuid,
                "tournamentRoundText": name if double and base_num == 1 else (name if not double and base_num in [2,1] else f"Round {round_number}"),#str(index+1),
                "startTime": str(datetime.now().date()),
                "state": 'SCHEDULED',
                "participants": [
                    {
                        "id": None,
                        "resultText": None,
                        "isWinner": False,
                        "status": None,
                        "name": None
                    },
                    {
                        "id": None,
                        "resultText": None,
                        "isWinner": False,
                        "status": None,
                        "name": None
                    }
                ]
            }
            lap += 1

            matchups.append(match)

        return json.dumps(matchups, indent=2)

    async def generate_matchups_loser(self, num_participants):
        if num_participants not in [8, 16, 32, 64]:
                    raise ValueError("La cantidad de participantes debe ser 8, 16, 32 o 64.")

        list_uuid = [str(uuid.uuid4()) for i in range(num_participants-2)]

        matchups = []
        round_number = 1
        lap = 0
        top = 0
        base_num = num_participants//4
        base_index = num_participants//4
  
        for index, value in enumerate(list_uuid):
            if index != 0 and index % base_num == 0:
                round_number += 1
                lap += 1
            if lap == 2:
                lap = 0
                base_num = base_num // 2

            if top == 2:
                top = 0
                base_index -= 1

            if round_number % 2 == 0:
                get_uuid = None if index == len(list_uuid)-1 else list_uuid[index+base_index-top]
                top +=1


            if round_number % 2 == 1:
                get_uuid = None if index == len(list_uuid)-1 else list_uuid[index+base_num]
      

            match = {
                "id": list_uuid[index],
                "name": f"Losers Round {round_number}",
                "nextMatchId": get_uuid, #None if index == len(list_uuid)-1 else list_uuid[index+base_num],
                "nextLooserMatchId": None,
                "tournamentRoundText": str(index+1),
                "startTime": str(datetime.now().date()),
                "state": None, 
                "participants": [
                    {
                        "id": None,
                        "resultText": None,
                        "isWinner": False,
                        "status": None,
                        "name": None
                    },
                    {
                        "id": None,
                        "resultText": None,
                        "isWinner": False,
                        "status": None,
                        "name": None
                    }
                ]
            }

            matchups.append(match)
    
            

        return matchups, list_uuid,

    async def generate_matchups_double(self, num_participants):
        matchups_winner = json.loads(await self.generate_matchups_simple(num_participants, double=True))
        
        losers, list_uuid = await self.generate_matchups_loser(num_participants)
        lap = -1
        base_index = num_participants // 4
        
        for index, value in enumerate(matchups_winner):
            if index <= num_participants//2:
                if index % 2 == 0:
                    lap += 1
            else:
                lap += 1
                if base_index != 0 and lap % base_index == 0:
                  base_index = base_index // 2  
                  lap += base_index
            

            value['nextLooserMatchId'] = list_uuid[lap]
            if value['name'] == 'Semifinal':
                value['nextLooserMatchId'] = list_uuid[-1]

        finalisima = {
                "id": str(uuid.uuid4()),
                    "name": "Final 2",
                    "nextMatchId": None,
                    "nextLooserMatchId": None,
                    "tournamentRoundText": str(len(losers)+len(matchups_winner)+1),
                    "startTime": str(len(losers)+len(matchups_winner)),
                    "state": None,
                    "participants": [
                        {
                            "id": None,
                            "resultText": None,
                            "isWinner": False,
                            "status": None,
                            "name": None
                        },
                        {
                            "id": None,
                            "resultText": None,
                            "isWinner": False,
                            "status": None,
                            "name": None
                        }
                    ]
            }
        
        final_match = {
                    "id": str(uuid.uuid4()),
                    "name": "Final 1",
                    "nextMatchId": finalisima['id'],
                    "nextLooserMatchId": finalisima['id'],
                    "tournamentRoundText": str(len(losers)+len(matchups_winner)),
                    "startTime": str(len(losers)+len(matchups_winner)),
                    "state": None,
                    "participants": [
                        {
                            "id": None,
                            "resultText": None,
                            "isWinner": False,
                            "status": None,
                            "name": None
                        },
                        {
                            "id": None,
                            "resultText": None,
                            "isWinner": False,
                            "status": None,
                            "name": None
                        }
                    ]
                }
        
        
        
        losers[-1]['nextMatchId'] = final_match['id']
        matchups_winner[-1]['nextMatchId'] = final_match['id']

        matchups_winner.append(final_match)
        matchups_winner.append(finalisima)

        tournament = {
            'upper': matchups_winner,
            'lower': losers
        }

        return json.dumps(tournament, indent=2)
    
    async def shuffle_participants(self, data: str, participants: TournamentParticipants, number_participants: int, type: TypeTournament):
        try:
            if type == TypeTournament.SIMPLE:
                matchups = json.loads(data)
                array_generated = await self.generate_array(number_participants//2)
                random.shuffle(participants)

                index = 0
                count_part = 0
                
                while index < 2 and count_part < len(participants):
                    for i in array_generated:
                        matchups[i-1]['participants'][index]['id'] = participants[count_part].participant.id
                        matchups[i-1]['participants'][index]['name'] = participants[count_part].participant.username
                        count_part += 1
                        if count_part == len(participants):
                            break
                    index += 1

                for march in matchups[:len(participants)//2]:
                    for participant in march['participants']:
                        if participant['id'] is None:
                            participant['state'] = 'WALK_OVER'

            elif type == TypeTournament.DOUBLE:
                matchups = json.loads(data)
                upper = matchups['upper']
                lower = matchups['lower']
                array_generated = await self.generate_array(number_participants//2)
                random.shuffle(participants)

                index = 0
                count_part = 0
                
                while index < 2 and count_part < len(participants):
                    for i in array_generated:
                        upper[i-1]['participants'][index]['id'] = participants[count_part].participant.id
                        upper[i-1]['participants'][index]['name'] = participants[count_part].participant.username
                        count_part += 1
                        if count_part == len(participants):
                            break
                    index += 1

                for march in upper[:len(participants)//2]:
                    for participant in march['participants']:
                        if participant['id'] is None:
                            participant['state'] = 'WALK_OVER'

                matchups['upper'] = upper 

            return json.dumps(matchups, indent=2)
        except Exception as e:
            raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, "Error al intentar actualizar torneo")

    async def generate_array(self, n):
        if n & (n - 1) != 0: 
            raise ValueError("El número debe ser una potencia de 2")
        
        impares = [i for i in range(1, n + 1) if i % 2 != 0]
        pares = [i for i in range(1, n + 1) if i % 2 == 0]
        
        resultado = []
        for i in range(len(impares)):
            resultado.append(impares[i])
            if i < len(pares):
                resultado.append(pares[-(i + 1)])
        
        return resultado

    async def compress_string(self, data):
        compressed = zlib.compress(data.encode('utf-8'))
        return base64.b64encode(compressed).decode('utf-8')
    
    async def decompress_string(self, compressed_data):
        compressed = base64.b64decode(compressed_data.encode('utf-8'))
        return zlib.decompress(compressed).decode('utf-8')

    async def finished_tournament(self, number_participants: int, data: str, type: TypeTournament):
        try:
            participants = {}

            matchups = json.loads(data)

            if type == TypeTournament.SIMPLE:
                points = {
                    64: {'Final G': {'point': 800}, 'Final P': {'point': 400}, 'Semifinal': {'point': 200}, 'Round 4': {'point': 100}, 'Round 3': {'point': 50}, 'Round 2': {'point': 25}, 'Round 1': {'point': 0}},
                    32: {'Final G': {'point': 400}, 'Final P': {'point': 200}, 'Semifinal': {'point': 100}, 'Round 3': {'point': 50}, 'Round 2': {'point': 25}, 'Round 1': {'point': 0}},
                    16: {'Final G': {'point': 200}, 'Final P': {'point': 100}, 'Semifinal': {'point': 50}, 'Round 2': {'point': 25}, 'Round 1': {'point': 0}},
                    8: {'Final G': {'point': 100}, 'Final P': {'point': 50}, 'Semifinal': {'point': 25}, 'Round 1': {'point': 0}},
                }

                list_points = points[number_participants]

                for matchs in matchups:
                    for participant in matchs['participants']:
                        if participant['id'] is None: continue
                        if not participant['id'] in participants:
                          participants[participant['id']] = {'points': 0, 'win': 0, 'lose': 0, 'position': None}
                        participants[participant['id']]['win' if participant['isWinner'] == True else 'lose'] += 1
                        if participant['isWinner'] == False:
                            if matchs['name'] == 'Final':
                                participants[participant['id']]['points'] = list_points['Final P']['point']
                                participants[participant['id']]['position'] = 'Finalista'
                            else :
                                participants[participant['id']]['points'] = list_points[matchs['name']]['point']
                                participants[participant['id']]['position'] = matchs['name']
                        if matchs['name'] == 'Final' and participant['isWinner'] == True:
                            participants[participant['id']]['points'] = list_points['Final G']['point']
                            participants[participant['id']]['position'] = 'Ganador'

            elif type == TypeTournament.DOUBLE:
                points = {
                    64: {'Final G': {'point': 1200}, 'Final P': {'point': 1000}, 'Losers Round 10': {'point': 700}, 'Losers Round 9': {'point': 600}, 'Losers Round 8': {'point': 500}, 'Losers Round 7': {'point': 400}, 'Losers Round 6': {'point': 300}, 'Losers Round 5': {'point': 200}, 'Losers Round 4': {'point': 100}, 'Losers Round 3': {'point': 50}, 'Losers Round 2': {'point': 25}, 'Losers Round 1': {'point': 0}},
                    32: {'Final G': {'point': 1000}, 'Final P': {'point': 800}, 'Losers Round 8': {'point': 600}, 'Losers Round 7': {'point': 500}, 'Losers Round 6': {'point': 400}, 'Losers Round 5': {'point': 300}, 'Losers Round 4': {'point': 100}, 'Losers Round 3': {'point': 50}, 'Losers Round 2': {'point': 25}, 'Losers Round 1': {'point': 0}},
                    16: {'Final G': {'point': 800}, 'Final P': {'point': 600}, 'Losers Round 6': {'point': 400}, 'Losers Round 5': {'point': 300}, 'Losers Round 4': {'point': 100}, 'Losers Round 3': {'point': 50}, 'Losers Round 2': {'point': 25}, 'Losers Round 1': {'point': 0}},
                    8: {'Final G': {'point': 400}, 'Final P': {'point': 200},'Losers Round 4': {'point': 100}, 'Losers Round 3': {'point': 50}, 'Losers Round 2': {'point': 25}, 'Losers Round 1': {'point': 0}},
                }
                
                list_points = points[number_participants]
                
                for matchs in matchups['upper']:
                    for participant in matchs['participants']:
                        if participant['id'] is None: continue
                        if not participant['id'] in participants:
                            participants[participant['id']] = {'points': 0, 'win': 0, 'lose': 0, 'position': None}
                        participants[participant['id']]['win' if participant['isWinner'] == True else 'lose'] += 1
                        if matchs['name'] == 'Final 1' and matchups['upper'][-1]['state'] == 'CANCEL FINAL':
                            if participant['isWinner'] == True:
                                participants[participant['id']]['points'] = list_points['Final G']['point']
                                participants[participant['id']]['position'] = 'Ganador'
                            else:
                                participants[participant['id']]['points'] = list_points['Final P']['point']
                                participants[participant['id']]['position'] = 'Finalista'
                        if matchs['name'] == 'Final 2' and matchs['state'] == 'DONE':
                            if participant['isWinner'] == True:
                                participants[participant['id']]['points'] = list_points['Final G']['point']
                                participants[participant['id']]['position'] = 'Ganador'
                            else:
                                participants[participant['id']]['points'] = list_points['Final P']['point']
                                participants[participant['id']]['position'] = 'Finalista'
                for matchs in matchups['lower']:
                    for participant in matchs['participants']:
                        if participant['id'] is None: continue
                        participants[participant['id']]['win' if participant['isWinner'] == True else 'lose'] += 1
                        if participant['isWinner'] == False:
                            participants[participant['id']]['points'] = list_points[matchs['name']]['point']
                            participants[participant['id']]['position'] = matchs['name']

            return participants
            
        except Exception as e:
            raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, "Error al intentar finalizar torneo")
             
    async def test_tournament_register(self, tournament_id: str, limite: int):
        try:
            sttmt = select(Tournament).where(Tournament.id == tournament_id)
            tournament: Tournament | None = (await self.session.exec(sttmt)).first()

            if tournament is None:
                return JSONResponse(
                    content={
                        "detail": "Torneo no entontrado", 
                    },
                    status_code= status.HTTP_404_NOT_FOUND
                )

            sttmt_part = select(Participant).options(selectinload(Participant.tournaments)
                          )
            participants: List[Participant] = (await self.session.exec(sttmt_part)).all()

            for index, participant in enumerate(participants):
                self.session.add(TournamentParticipants(participant_id= participant.id, tournament_id= tournament_id, confirm= True))
                if index == limite-1:
                    break

            await self.session.commit()

            return JSONResponse(
                content={
                    "detail": "listo papu, registrados y confirmados!"
                },
                status_code= status.HTTP_200_OK
            )
        except Exception as e:
            raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, "Error al intentar obtener torneo")

    async def get_result_tournament(self, tournament_id: str):
        try:
            stmt = (
                select(TournamentParticipants)
                .options(
                    joinedload(TournamentParticipants.participant)
                )
                .where(TournamentParticipants.tournament_id == tournament_id)
            )

            tournament_participants: List[TournamentParticipants] = (await self.session.exec(stmt)).unique().all()

            list_participants: List[ParticipantResultTour] = [
                ParticipantResultTour(
                    **participant.participant.model_dump(),
                    final_position= participant.final_position or None,
                    points= participant.points,
                    win= participant.win,
                    lose= participant.lose,
                ).model_dump()
                for participant in tournament_participants
            ]

            return JSONResponse(
                content={"result_tournament": sorted(list_participants, key=lambda x: x['points'], reverse=True)},
                status_code=status.HTTP_200_OK
            )

        except Exception as e:
            print(f"Error al obtener torneos: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error al intentar obtener torneos"
            )
