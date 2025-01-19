import json
from typing import List
from fastapi import HTTPException, status
from src.models.participant_model import Participant
from src.models.tournament_participants import TournamentParticipants
from src.models.tournaments import StatusTournament, Tournament
from src.models.user_model import User
from src.schemas.tournament_schemas.tournament_create import TournamentCreate
from src.schemas.tournament_schemas.tournament_dto import TournamentDTO
from src.schemas.tournament_schemas.tournament_response import TournamentResponse
from sqlmodel import select, or_
from sqlmodel.ext.asyncio.session import AsyncSession
from fastapi.responses import JSONResponse
from sqlalchemy.orm import selectinload

from src.schemas.user_schema.user_full import UserFull


class TournamentService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_tournament(self, tournament: TournamentCreate, user: UserFull):
        try:
            new_tournament: Tournament = Tournament(**tournament.model_dump(), data = "", organizer_id= user.full.id)

            self.session.add(new_tournament)

            await self.session.commit()

            return JSONResponse(
                content={"detail":"Torneo creado con éxito!"},
                status_code=status.HTTP_201_CREATED
            )
        except Exception as e:
            raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, "Error al intentar crear torneo")

    async def get_all_tournaments(self, status_filter: StatusTournament | None):
        try:
            if status_filter is None:
                stmt = select(Tournament)
            else:
                stmt = select(Tournament).where(Tournament.status == status_filter)

            tournaments: List[Tournament] = (await self.session.exec(stmt)).all()

            list_tour = [TournamentDTO.model_validate(tour).model_dump(mode="json") for tour in tournaments]

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
            stmt = select(Tournament).where(Tournament.name.like(f"%{name_filter}%"))
            tournaments: List[Tournament] = (await self.session.exec(stmt)).all()

            list_tour = [TournamentDTO.model_validate(tour).model_dump(mode="json") for tour in tournaments]

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
                .where(Tournament.id == id)
                .options(selectinload(Tournament.participants).selectinload(TournamentParticipants.participant))
            )
            tournament = (await self.session.exec(stmt)).first()

            if tournament is None:
                return JSONResponse(
                    content={
                        "detail": "Torneo no entontrado", 
                    },
                    status_code= status.HTTP_404_NOT_FOUND
                )
            
            list_participants: List[UserFull] = []

            for participant in tournament.participants:
                part: Participant = await self.session.get(Participant, participant.participant_id)
                user: User = await self.session.get(User, part.user_id)
                list_participants.append(UserFull(user= user, full= part))

            tour_resp: TournamentResponse = TournamentResponse(**tournament.model_dump(), list_participants=list_participants)

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