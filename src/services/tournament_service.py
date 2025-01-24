from asyncio import to_thread
from datetime import datetime
import json
from typing import List
import uuid
from fastapi import HTTPException, UploadFile, status
from src.models.cloudinary_model import CloudinaryModel
from src.models.participant_model import Participant
from src.models.tournament_participants import TournamentParticipants
from src.models.tournaments import StatusTournament, Tournament
from src.models.user_model import User
from src.schemas.organizer_schemas.organizer_dto import OrganizerDTO
from src.schemas.participant_schemas.participant_dto import ParticipantDTO
from src.schemas.tournament_schemas.data_update import DataUpdate
from src.schemas.tournament_schemas.tournament_create import TournamentCreate
from src.schemas.tournament_schemas.tournament_dto import TournamentDTO
from src.schemas.tournament_schemas.tournament_response import TournamentResponse
from sqlmodel import select, or_
from sqlmodel.ext.asyncio.session import AsyncSession
from fastapi.responses import JSONResponse
from sqlalchemy.orm import selectinload, joinedload
import random

from src.schemas.tournament_schemas.tournament_update import TournamentUpdate
from src.schemas.user_schema.user_full import UserFull


class TournamentService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_tournament(self, tournament: TournamentCreate, user: UserFull, image: UploadFile | None):
        try:

            data = await self.generate_matchups_simple(tournament.number_participants)

            new_tournament: Tournament = Tournament(**tournament.model_dump(), data = data, organizer_id= user.full.id)
            
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
            stmt = select(Tournament).options(
                    joinedload(Tournament.organizer), joinedload(Tournament.participants)
                    ).where(Tournament.id == id)
            
            tournament = (await self.session.exec(stmt)).unique().first()

            if tournament is None:
                return JSONResponse(
                    content={
                        "detail": "Torneo no entontrado", 
                    },
                    status_code= status.HTTP_404_NOT_FOUND
                )
            


            list_participants: List[ParticipantDTO] = []

            for participant in tournament.participants:
                part: Participant = await self.session.get(Participant, participant.participant_id)
                list_participants.append(ParticipantDTO(**part.model_dump()))

            tour_resp: TournamentResponse = TournamentResponse(
                **tournament.model_dump(), 
                number_registered= len(tournament.participants),
                organizer= OrganizerDTO(
                    **tournament.organizer.model_dump()
                ),
                list_participants= list_participants
            )

            return JSONResponse(
                content={
                    "tournament": tour_resp.model_dump(mode='json')
                },
                status_code= status.HTTP_200_OK
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

            tournament.data = data.data

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
                
                new_data = await self.shuffle_participants(tournament.data, participants, tournament.number_participants)
                
                tournament.data = new_data
            tournament.is_open = False

            await self.session.commit()

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
        
    async def generate_matchups_simple(self, num_participants):
        if num_participants not in [8, 16, 32, 64]:
            raise ValueError("La cantidad de participantes debe ser 8, 16, 32 o 64.")

        rounds = {
            2: 'Final',
            4: 'Semifinal',
            8: '4tos de Final',
            16: '8vos de Final',
            32: '16vos de Final',
            64: '32vos de Final'
        }

        matchups = []
        round_number = 1
        round_id = 2

        while num_participants >= round_id:

            for i in range(0, round_id, 2):
                match = {
                    "id": str(uuid.uuid4()),
                    "name": rounds[round_id],
                    "nextMatchId": None,
                    "tournamentRoundText": str(round_number),
                    "startTime": str(round_number),
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

                if len(matchups) > 0:
                    match['nextMatchId'] = matchups[((len(matchups)+1)//2)-1]['id']
                
                matchups.append(match)
                round_number += 1

            round_id = round_id * 2
        return json.dumps(matchups[::-1], indent=2)


    async def shuffle_participants(self, data: str, participants: TournamentParticipants, number_participants: int):
        try:
            matchups = json.loads(data)
            array_generated = await self.generate_array(number_participants//2)
            # list_participants = participants.model_copy()
            random.shuffle(participants)

            index = 0
            count_part = 0
            
            while index < 2 and count_part < len(participants):
                for i in array_generated:
                    matchups[i-1]['participants'][index]['id'] = participants[count_part].participant.id
                    matchups[i-1]['participants'][index]['name'] = participants[count_part].participant.username
                    count_part += 1
                index += 1

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

