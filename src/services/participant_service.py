from fastapi import APIRouter, HTTPException, status
from src.models.organizer_model import Organizer
from src.models.participant_model import Participant
from src.models.tournament_participants import TournamentParticipants
from src.models.tournaments import Tournament
from src.models.user_model import User
from src.schemas.tournament_schemas.tournament_create import TournamentCreate
from sqlmodel import select, or_
from sqlmodel.ext.asyncio.session import AsyncSession
from fastapi.responses import JSONResponse

from src.schemas.user_schema.user_full import UserFull

user_router = APIRouter()

class ParticipantService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def register_tournament(self, tournament_id: str, user: UserFull):
        try:
            sttmt = select(TournamentParticipants).where(
                TournamentParticipants.tournament_id == tournament_id,
                TournamentParticipants.participant_id == user.full.id
            )
            register: TournamentParticipants | None = (await self.session.exec(sttmt)).first()

            if register is not None:
                return JSONResponse(
                    content={
                        "detail": "Ya se encuentra registrado", 
                    },
                    status_code= status.HTTP_400_BAD_REQUEST
                )

            new_register: TournamentParticipants = TournamentParticipants(
                participant_id= user.full.id,
                tournament_id= tournament_id
            )

            self.session.add(new_register)

            await self.session.commit()

            return JSONResponse(
                content={"detail":"Registrado con éxito!"},
                status_code=status.HTTP_201_CREATED
            )

        except Exception as e:
            raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, "Error al intentar crear torneo")
   
    async def cancel_register_tournament(self, tournament_id: str, user: UserFull):
        try:
            sttmt = select(TournamentParticipants).where(
                TournamentParticipants.tournament_id == tournament_id,
                TournamentParticipants.participant_id == user.full.id
            )
            register: TournamentParticipants | None = (await self.session.exec(sttmt)).first()

            if register is None:
                return JSONResponse(
                    content={
                        "detail": "Registro no entontrado", 
                    },
                    status_code= status.HTTP_404_NOT_FOUND
                )

            self.session.delete(register)

            await self.session.commit()

            return JSONResponse(
                content={"detail":"Registro cancelado con éxito!"},
                status_code=status.HTTP_204_NO_CONTENT
            )

        except Exception as e:
            raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, "Error al intentar crear torneo")