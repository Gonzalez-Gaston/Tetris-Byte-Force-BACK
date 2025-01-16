from fastapi import APIRouter, Depends, Request, status, Form
from fastapi.responses import JSONResponse
from sqlmodel.ext.asyncio.session import AsyncSession
from src.config.decorators import authorization
from src.database.db import db
from src.models.user_model import RoleUser, User
from src.schemas.organizer_schemas.organizer_create import OrganizerCreate
from src.schemas.participant_schemas.participant_create import ParticipantCreate
from src.schemas.tournament_schemas.tournament_create import TournamentCreate
from src.schemas.user_schema.user_credentials import UserCredentials
from src.services.auth_service import AuthService, oauth_scheme
from src.services.organizer_service import OrganizerService
from src.services.user_service import UserService

organizer_router = APIRouter(prefix='/organizer', tags=['Organizer'])

auth = AuthService()

@organizer_router.post('/create_tournament')
@authorization(roles=[RoleUser.ORGANIZER])
async def create_user(
    tournament: TournamentCreate,
    user: User = Depends(auth.get_current_user),
    session: AsyncSession = Depends(db.get_session),
):
    return await OrganizerService(session).create_tournament(tournament, user)