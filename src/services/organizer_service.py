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
from src.schemas.user_schema.user_full import UserFull
from src.services.auth_service import AuthService

user_router = APIRouter()

class OrganizerService:
    def __init__(self, session: AsyncSession):
        self.session = session

    

  

    