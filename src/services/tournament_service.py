from asyncio import to_thread
from typing import List
from fastapi import HTTPException, UploadFile, status
from src.models.cloudinary_model import CloudinaryModel
from src.models.participant_model import Participant
from src.models.tournament_participants import TournamentParticipants
from src.models.tournaments import StatusTournament, Tournament
from src.models.user_model import User
from src.schemas.organizer_schemas.organizer_dto import OrganizerDTO
from src.schemas.participant_schemas.participant_dto import ParticipantDTO
from src.schemas.tournament_schemas.tournament_create import TournamentCreate
from src.schemas.tournament_schemas.tournament_dto import TournamentDTO
from src.schemas.tournament_schemas.tournament_response import TournamentResponse
from sqlmodel import select, or_
from sqlmodel.ext.asyncio.session import AsyncSession
from fastapi.responses import JSONResponse
from sqlalchemy.orm import selectinload, joinedload

from src.schemas.user_schema.user_full import UserFull


class TournamentService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_tournament(self, tournament: TournamentCreate, user: UserFull, image: UploadFile | None):
        try:

            # matchs: List = await self.generate_tournament_matches_simple(tournament.number_participants)

            new_tournament: Tournament = Tournament(**tournament.model_dump(), data = "", organizer_id= user.full.id)
            
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
        
    async def update_data(self, tournament_id: str, data: str, user: UserFull):
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

            tournament.data = data

            await self.session.commit()

            return JSONResponse(
                content={
                    "detail": "Datos del torneo actualizdo con éxito!",
                    "tournament": TournamentDTO.model_validate(tournament).model_dump(mode="json") 
                },
                status_code= status.HTTP_200_OK
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

            await self.session.commit()

            return JSONResponse(
                content={
                    "detail": "Datos del torneo actualizdo con éxito!",
                    "tournament": TournamentDTO.model_validate(tournament).model_dump(mode="json") 
                },
                status_code= status.HTTP_200_OK
            )
        except Exception as e:
            raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, "Error al intentar actualizar torneo")
        
    async def update_tournament(self, tournament: TournamentCreate, user: UserFull, image: UploadFile | None):
        try:
            sttmt = select(Tournament).where(Tournament.id == tournament.id, Tournament.organizer_id == user.full.id)
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
            
            tournament.name = tournament.name
            tournament.description = tournament.description
            tournament.start = tournament.start
            tournament.end = tournament.end

            result = {}
            if image is not None:
                result = await to_thread(
                    CloudinaryModel().upload_image, 
                    image,
                    "tournament",
                    tournament.id
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
        
    async def generate_tournament_matches_simple(self, participants):
        matches = []
        round_number = 1
        match_id = 1
        current_participants = participants[:]

        while len(current_participants) > 1:
            next_round_participants = []
            total_matches = len(current_participants) // 2

            for i in range(total_matches):
                match_participants = [
                    {"id": current_participants[i * 2]["id"], "name": current_participants[i * 2]["name"]},
                    {"id": current_participants[i * 2 + 1]["id"], "name": current_participants[i * 2 + 1]["name"]},
                ]

                match = {
                    "id": f"m{match_id}",
                    "name": f"Round {round_number} - Match {i + 1}",
                    "nextMatchId": None,  # Esto se actualizará después
                    "tournamentRoundText": str(round_number),
                    "state": "PENDING",
                    "participants": match_participants,
                }

                matches.append(match)
                next_round_participants.append({"id": f"winner-m{match_id}", "name": f"Winner of m{match_id}"})
                match_id += 1

            current_participants = next_round_participants
            round_number += 1

        # Actualizar los "nextMatchId" en los enfrentamientos
        next_match_index = len(matches)
        while next_match_index > 1:
            next_match_index //= 2
            for i in range(next_match_index):
                matches[i]["nextMatchId"] = matches[next_match_index + i]["id"]

        return matches
    