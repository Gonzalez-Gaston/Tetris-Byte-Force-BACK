from datetime import date, datetime, timedelta, timezone
from uuid import UUID
import bcrypt
from fastapi import APIRouter, HTTPException, status
from src import db
from src.models.refresh_token import HistorialRefreshToken
from src.models.user_model import User
from src.schemas.user_schema.user_create import UserCreate
from sqlmodel import select, or_
from sqlmodel.ext.asyncio.session import AsyncSession
from fastapi.responses import JSONResponse
from src.schemas.user_schema.user_credentials import UserCredentials
from src.services.auth_service import AuthService

user_router = APIRouter()

class UserService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def login(self, credentials:UserCredentials):
        try:
            statement = select(User).where(User.email == credentials.email)
            user: User | None = (await self.session.exec(statement)).first()

            if user is None:
                return JSONResponse(
                    content={"detail": "Credenciales incorrectas"},
                    status_code=status.HTTP_404_NOT_FOUND
                )
            
            if self.verify_password(credentials.password, user.password_hash) == False:
                return JSONResponse(
                    content={"detail": "Credenciales incorrectas"},
                    status_code=status.HTTP_404_NOT_FOUND
                )
            
            token = await AuthService().get_token(user)

            sttmt_rt =  token
            sttmt_rt['user_id'] = user.id
            sttmt_rt['expired_at'] = datetime.now(timezone.utc) + timedelta(days=7)

            self.session.add(HistorialRefreshToken(**sttmt_rt))

            return JSONResponse(
                content={"token": token},
                status_code=status.HTTP_200_OK
            )

        except Exception as e:
            raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, "Error al intentar loguear")

    async def create_user(self, user: UserCreate):
            try:
                statement= select(User).where(or_(User.username == user.username , User.email == user.email))
                                            
                result = await self.session.exec(statement)
                user_exist: User | None = result.first()
                
                if(user_exist != None):
                    if user_exist.username == user.username:
                        return JSONResponse(
                            status_code=status.HTTP_409_CONFLICT, 
                            content={"detail": "El username ya se encuentra en uso"}
                            )
                    if user_exist.email == user.email:
                        return JSONResponse(
                            status_code=status.HTTP_409_CONFLICT, 
                            content={"detail": "El email ya existe."}
                            )

                new_user: User = User(**user.model_dump())

                self.session.add(new_user)
                await self.session.commit()

                return JSONResponse(
                            status_code=status.HTTP_201_CREATED, 
                            content={"detail": "Usuario creado exitosamente."}
                            )
            except Exception as e:
                raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, 'Error al crear usuario.')
    
    @classmethod
    def verify_password(cls, password: str, hashed_password: str) -> bool:
        return bcrypt.checkpw(password.encode('utf-8'), hashed_password.encode('utf-8'))
    
    async def me(self, user: User):
        # Convertir campos de tipo date a string
        user_dict = user.model_dump()
        for key, value in user_dict.items():
            if isinstance(value, date):
                user_dict[key] = value.isoformat()
            
            if isinstance(value, UUID):
                user_dict[key] = str(value)

        return JSONResponse(
            status_code=status.HTTP_200_OK, 
            content=user_dict
        )
    
    async def validate_email(self, email: str):
        statement = select(User).where(User.email == email)
        exist = await self.session.exec(statement)
        user: User | None = exist.first()
        return user is None 
    
    async def validate_username(self, username: str):
        statement = select(User).where(User.username == username)
        exist = await self.session.exec(statement)
        user: User | None = exist.first()
        return user is None 

    
    
    