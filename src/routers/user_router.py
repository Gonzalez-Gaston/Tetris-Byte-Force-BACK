from fastapi import APIRouter, Depends
from sqlmodel.ext.asyncio.session import AsyncSession
from src.database.db import db
from src.models.user_model import User
from src.schemas.user_schema.user_credentials import UserCredentials
from src.services.auth_service import AuthService
from src.services.user_service import UserService
from src.schemas.user_schema.user_create import UserCreate

user_router = APIRouter(prefix='/users', tags=['User'])

auth = AuthService()

@user_router.post('/create')
async def create_user(
    user: UserCreate,
    session: AsyncSession = Depends(db.get_session),
):
    return await UserService(session).create_user(user)

@user_router.post('/login')
async def login(
    credentials:UserCredentials,
    session: AsyncSession = Depends(db.get_session),
):
    return await UserService(session).login(credentials)

@user_router.get('/me') 
async def user( 
    user: User = Depends(auth.get_current_user), 
    session: AsyncSession = Depends(db.get_session), 
): 
    user_service = UserService(session) 
    user_data = await user_service.me(user) 
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