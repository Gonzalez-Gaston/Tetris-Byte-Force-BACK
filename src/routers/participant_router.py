from datetime import date
from typing import List
from fastapi import APIRouter, Depends, File, Form, UploadFile, status
from sqlmodel.ext.asyncio.session import AsyncSession
from src.config.decorators import authorization
from src.database.db import db
from src.models.user_model import RoleUser
from src.schemas.participant_schemas.participant_update import ParticipantUpdate
from src.schemas.user_schema.user_full import UserFull
from src.services.auth_service import AuthService
from src.services.participant_service import ParticipantService

participant_router = APIRouter(prefix='/participant', tags=['Participant'])

auth = AuthService()

############################### POST ###############################

@participant_router.post('/register_tournament/{tournament_id}', status_code= status.HTTP_201_CREATED)
@authorization(roles=[RoleUser.PARTICIPANT])
async def register_tournament(
    tournament_id: str,
    user: UserFull = Depends(auth.get_current_user),
    session: AsyncSession = Depends(db.get_session),
):
    return await ParticipantService(session).register_tournament(tournament_id, user)


############################### DELTE ###############################

@participant_router.delete('/cancel_register_tournament/{tournament_id}', status_code= status.HTTP_204_NO_CONTENT)
@authorization(roles=[RoleUser.PARTICIPANT])
async def cancel_register_tournament(
    tournament_id: str,
    user: UserFull = Depends(auth.get_current_user),
    session: AsyncSession = Depends(db.get_session),
):
    return await ParticipantService(session).cancel_register_tournament(tournament_id, user)

############################### GET ###############################

@participant_router.get('/registered_tournaments_ids', status_code= status.HTTP_200_OK, response_model= List[str])
@authorization(roles=[RoleUser.PARTICIPANT])
async def registered_tournaments_ids(
    user: UserFull = Depends(auth.get_current_user),
    session: AsyncSession = Depends(db.get_session),
):
    return await ParticipantService(session).registered_tournaments_ids(user)


@participant_router.put('/participant_update')
@authorization(roles=[RoleUser.PARTICIPANT])
async def participant_update(
    first_name: str = Form(...),
    last_name: str = Form(...),
    date_of_birth: date = Form(...),
    image: UploadFile | None = File(None),
    user: UserFull = Depends(auth.get_current_user),
    session: AsyncSession = Depends(db.get_session),
):
    return await ParticipantService(session).participant_update(user, image, ParticipantUpdate(first_name=first_name, last_name=last_name, date_of_birth=date_of_birth))

############################### PUT ###############################

@participant_router.put('/confirm_participation/{tournament_id}', status_code= status.HTTP_204_NO_CONTENT)
@authorization(roles=[RoleUser.PARTICIPANT])
async def confirm_participation(
    tournament_id: str,
    user: UserFull = Depends(auth.get_current_user),
    session: AsyncSession = Depends(db.get_session),
):
    return await ParticipantService(session).confirm_participation(tournament_id, user)