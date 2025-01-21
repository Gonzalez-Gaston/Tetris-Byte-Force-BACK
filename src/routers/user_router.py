from fastapi import APIRouter, Depends, File, Request, UploadFile, status, Form
from fastapi.responses import JSONResponse
from sqlmodel.ext.asyncio.session import AsyncSession
from src.config.decorators import authorization
from src.database.db import db
from src.models.user_model import RoleUser, User
from src.schemas.organizer_schemas.organizer_create import OrganizerCreate
from src.schemas.participant_schemas.participant_create import ParticipantCreate
from src.schemas.user_schema.user_credentials import UserCredentials
from src.schemas.user_schema.user_full import UserFull
from src.schemas.user_schema.user_update import UserUpdate
from src.services.auth_service import AuthService, oauth_scheme
from src.services.user_service import UserService

user_router = APIRouter(prefix='/users', tags=['User'])

auth = AuthService()

############################### POST ###############################

@user_router.post('/create_participant')
async def create_user(
    user: ParticipantCreate,
    session: AsyncSession = Depends(db.get_session),
):
    return await UserService(session).create_participant(user)

@user_router.post('/create_organizer')
async def create_user(
    user: OrganizerCreate,
    session: AsyncSession = Depends(db.get_session),
):
    return await UserService(session).create_organizer(user)

@user_router.post('/login')
async def login(
    credentials:UserCredentials,
    session: AsyncSession = Depends(db.get_session),
):
    return await UserService(session).login(credentials)

@user_router.post('/refresh_token')
async def refresh_token(
    refresh_token: str =  Form(),
    user: tuple | bool = Depends(auth.get_user_refresh_token), 
    session: AsyncSession = Depends(db.get_session),
):
    if user == False:
        return JSONResponse(
            headers={"WWW-Authenticate": "Bearer"},
            status_code=status.HTTP_400_BAD_REQUEST,
            content={'detail':'Token no caducado'}
        )
    return await UserService(session).refresh_token(user[0], user[1], refresh_token)

############################### GET ###############################

@user_router.get('/me') 
@authorization(roles=[RoleUser.PARTICIPANT, RoleUser.ORGANIZER])
async def user( 
    user: UserFull = Depends(auth.get_current_user), 
): 
    user_data = user
    return user_data

@user_router.get('/validate_email')
async def validate_email(
    email: str,
    session: AsyncSession = Depends(db.get_session),
):
    return await UserService(session).validate_email(email)

@user_router.get('/validate_username')
async def validate_email(
    username: str,
    session: AsyncSession = Depends(db.get_session),
):
    return await UserService(session).validate_username(username)


############################### PUT ###############################


@user_router.put('/user_update')
@authorization(roles=[RoleUser.PARTICIPANT])
async def user_update(
    user_update: UserUpdate,
    image: UploadFile = File(None),
    user: UserFull = Depends(auth.get_current_user),
    session: AsyncSession = Depends(db.get_session),
):
    return await UserService(session).user_update(user, image, user_update)
