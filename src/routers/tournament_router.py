from datetime import datetime
from typing import List
from fastapi import APIRouter, Depends, File, Query, UploadFile, status, Request, status, Form
from fastapi.responses import JSONResponse
from sqlmodel.ext.asyncio.session import AsyncSession
from src.config.decorators import authorization
from src.database.db import db
from src.models.tournaments import FormatTournament, Tournament, StatusTournament, TypeTournament
from src.models.user_model import RoleUser, User
from src.schemas.organizer_schemas.organizer_create import OrganizerCreate
from src.schemas.participant_schemas.participant_create import ParticipantCreate
from src.schemas.tournament_schemas.tournament_create import TournamentCreate
from src.schemas.tournament_schemas.tournament_dto import ListTournamentDTO, TournamentDTO
from src.schemas.tournament_schemas.tournament_response import TournamentResponse
from src.schemas.tournament_schemas.tournament_update import TournamentUpdate
from src.schemas.user_schema.user_credentials import UserCredentials
from src.schemas.user_schema.user_full import UserFull
from src.services.auth_service import AuthService, oauth_scheme
from src.services.tournament_service import TournamentService

tournament_router = APIRouter(prefix='/tournament', tags=['Tournament'])

auth = AuthService()

############################### POST ###############################

@tournament_router.post('/create_tournament', status_code= status.HTTP_201_CREATED)
@authorization(roles=[RoleUser.ORGANIZER])
async def create_tournament(
    name: str= Form(...),
    description:str = Form(...),
    type: TypeTournament= Form(...),
    format: FormatTournament= Form(...),
    number_participants: int= Form(...),
    start: datetime= Form(...),
    end: datetime= Form(...),
    image: UploadFile | None = File(None),
    user: UserFull = Depends(auth.get_current_user),
    session: AsyncSession = Depends(db.get_session),
):
    return await TournamentService(session).create_tournament(
        TournamentCreate(
            name= name,
            description= description,
            type= type,
            format= format,
            number_participants= number_participants,
            start= start,
            end= end
        ), user, image)


############################### GET ###############################

@tournament_router.get('/get_all_tournaments', response_model= ListTournamentDTO)
async def get_all_tournaments(
    session: AsyncSession = Depends(db.get_session),
    status_filter: StatusTournament | None = Query(None)
):
    return await TournamentService(session).get_all_tournaments(status_filter)

@tournament_router.get('/get_name_tournaments', response_model= ListTournamentDTO)
async def get_name_tournaments(
    session: AsyncSession = Depends(db.get_session),
    name_filter: str = Query(None, min_length=3, description="El nombre debe tener al menos 3 caracteres")
):
    return await TournamentService(session).get_name_tournaments(name_filter)

@tournament_router.get('/get_tournament/{id}', response_model= TournamentResponse)
# @authorization(roles=[RoleUser.ORGANIZER, RoleUser.PARTICIPANT])
async def get_name_tournaments(
    id: str,
    # user: UserFull = Depends(auth.get_current_user),
    session: AsyncSession = Depends(db.get_session),
):
    return await TournamentService(session).get_tournament(id)




############################### PUT ###############################

@tournament_router.put('/update_tournament/{tournament_id}', status_code= status.HTTP_204_NO_CONTENT)
@authorization(roles=[RoleUser.ORGANIZER])
async def update_tournament(
    tournament_id: str,
    name: str= Form(...),
    description:str = Form(...),
    start: datetime= Form(...),
    end: datetime= Form(...),
    image: UploadFile | None = File(None),
    user: UserFull = Depends(auth.get_current_user),
    session: AsyncSession = Depends(db.get_session),
):
    return await TournamentService(session).update_tournament(
        tournament= TournamentUpdate(
            id= tournament_id,
            name= name,
            description= description,
            start= start,
            end= end
        ), user= user, image= image)

@tournament_router.put('/update_status/{tournament_id}', status_code= status.HTTP_201_CREATED)
@authorization(roles=[RoleUser.ORGANIZER])
async def update_status(
    tournament_id: str,
    status_tour: StatusTournament = Query(...),
    user: UserFull = Depends(auth.get_current_user),
    session: AsyncSession = Depends(db.get_session),
):
    return await TournamentService(session).update_status(status_tour, tournament_id, user)
