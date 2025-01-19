from typing import List
from fastapi import APIRouter, Depends, Query, Request, status, Form
from fastapi.responses import JSONResponse
from sqlmodel.ext.asyncio.session import AsyncSession
from src.config.decorators import authorization
from src.database.db import db
from src.models.tournaments import Tournament, StatusTournament
from src.models.user_model import RoleUser, User
from src.schemas.organizer_schemas.organizer_create import OrganizerCreate
from src.schemas.participant_schemas.participant_create import ParticipantCreate
from src.schemas.tournament_schemas.tournament_create import TournamentCreate
from src.schemas.tournament_schemas.tournament_response import TournamentResponse
from src.schemas.user_schema.user_credentials import UserCredentials
from src.schemas.user_schema.user_full import UserFull
from src.services.auth_service import AuthService, oauth_scheme
from src.services.tournament_service import TournamentService
from src.services.user_service import UserService

tournament_router = APIRouter(prefix='/tournament', tags=['Tournament'])

auth = AuthService()

############################### POST ###############################

@tournament_router.post('/create_tournament')
@authorization(roles=[RoleUser.ORGANIZER])
async def create_user(
    tournament: TournamentCreate,
    user: UserFull = Depends(auth.get_current_user),
    session: AsyncSession = Depends(db.get_session),
):
    return await TournamentService(session).create_tournament(tournament, user)


############################### GET ###############################

@tournament_router.get('/get_all_tournaments')
@authorization(roles=[RoleUser.ORGANIZER, RoleUser.PARTICIPANT])
async def get_all_tournaments(
    user: UserFull = Depends(auth.get_current_user),
    session: AsyncSession = Depends(db.get_session),
    status_filter: StatusTournament | None = Query(None)
):
    return await TournamentService(session).get_all_tournaments(status_filter)

@tournament_router.get('/get_name_tournaments')
@authorization(roles=[RoleUser.ORGANIZER, RoleUser.PARTICIPANT])
async def get_name_tournaments(
    user: UserFull = Depends(auth.get_current_user),
    session: AsyncSession = Depends(db.get_session),
    name_filter: str = Query(None, min_length=3, description="El nombre debe tener al menos 3 caracteres")
):
    return await TournamentService(session).get_name_tournaments(name_filter)

@tournament_router.get('/get_tournament/{id}')
@authorization(roles=[RoleUser.ORGANIZER, RoleUser.PARTICIPANT])
async def get_name_tournaments(
    id: str,
    user: UserFull = Depends(auth.get_current_user),
    session: AsyncSession = Depends(db.get_session),
):
    return await TournamentService(session).get_tournament(id)

############################### PUT ###############################

@tournament_router.put('/update_status/{tournament_id}')
@authorization(roles=[RoleUser.ORGANIZER])
async def update_status(
    tournament_id: str,
    status_tour: StatusTournament = Query(...),
    user: UserFull = Depends(auth.get_current_user),
    session: AsyncSession = Depends(db.get_session),
):
    return await TournamentService(session).update_status(status_tour, tournament_id, user)