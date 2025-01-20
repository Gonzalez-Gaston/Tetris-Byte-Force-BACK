from fastapi import APIRouter, Depends, status
from sqlmodel.ext.asyncio.session import AsyncSession
from src.config.decorators import authorization
from src.database.db import db
from src.models.user_model import RoleUser
from src.schemas.user_schema.user_full import UserFull
from src.services.auth_service import AuthService
from src.services.participant_service import ParticipantService

participant_router = APIRouter(prefix='/participant', tags=['Participant'])

auth = AuthService()

@participant_router.post('/register_tournament/{tournament_id}', status_code= status.HTTP_201_CREATED)
@authorization(roles=[RoleUser.PARTICIPANT])
async def register_tournament(
    tournament_id: str,
    user: UserFull = Depends(auth.get_current_user),
    session: AsyncSession = Depends(db.get_session),
):
    return await ParticipantService(session).register_tournament(tournament_id, user)

@participant_router.post('/cancel_register_tournament/{tournament_id}', status_code= status.HTTP_204_NO_CONTENT)
@authorization(roles=[RoleUser.PARTICIPANT])
async def cancel_register_tournament(
    tournament_id: str,
    user: UserFull = Depends(auth.get_current_user),
    session: AsyncSession = Depends(db.get_session),
):
    return await ParticipantService(session).cancel_register_tournament(tournament_id, user)