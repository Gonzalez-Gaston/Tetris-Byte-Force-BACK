from datetime import date, datetime, timedelta, timezone
from uuid import UUID
import bcrypt
from fastapi import APIRouter, HTTPException, status
from src import db
from src.models.organizer_model import Organizer
from src.models.participant_model import Participant
from src.models.refresh_token import HistorialRefreshToken
from src.models.tournaments import Tournament
from src.models.user_model import RoleUser, User
from src.schemas.organizer_schemas.organizer_create import OrganizerCreate
from src.schemas.participant_schemas.participant_create import ParticipantCreate
from src.schemas.tournament_schemas.tournament_create import TournamentCreate
from src.schemas.user_schema.user_create import UserCreate
from sqlmodel import select, or_
from sqlmodel.ext.asyncio.session import AsyncSession
from fastapi.responses import JSONResponse
from src.schemas.user_schema.user_credentials import UserCredentials
from src.services.auth_service import AuthService

user_router = APIRouter()

class OrganizerService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_tournament(self, tournament: TournamentCreate, user: User):
        try:
            sttmt = select(Organizer).where(Organizer.user_id == user.id)
            result = await self.session.exec(sttmt)
            organizer: Organizer | None = result.first()

            new_tournament: Tournament = Tournament(**tournament.model_dump(), data = "", organizer_id= organizer.id)

            self.session.add(new_tournament)

            await self.session.commit()

            return JSONResponse(
                content={"detail":"Torneo creado con éxito!"},
                status_code=status.HTTP_201_CREATED
            )

        except Exception as e:
            raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, "Error al intentar crear torneo")

    # async def update_data_tournamen(self, tournament_id: str, data: str, user_id: str):
    #     try:
    #         sttmt_org = select(Organizer).where(Organizer.user_id == user_id)
    #         organizer: Organizer | None = (await self.session.exec(sttmt_org)).first()

    #         if organizer is None:
                

    #         sttmt = select(Tournament).where(Tournament.id == tournament_id, Tournament.organizer_id == organizer.id)
    #         tournament: Tournament | None = (await self.session.exec(sttmt)).first()
        
    #     except Exception as e:
    #         raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, "Error al intentar actualizar torneo")

    