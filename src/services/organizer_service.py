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

    async def create_participant(self, user: ParticipantCreate):
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

                new_participant: Participant = Participant(
                    first_name= user.first_name,
                    last_name= user.last_name,
                    date_of_birth= user.date_of_birth,
                    user_id= new_user.id
                )

                self.session.add(new_participant)
                await self.session.commit()

                return JSONResponse(
                            status_code=status.HTTP_201_CREATED, 
                            content={"detail": "Usuario creado exitosamente."}
                            )
            except Exception as e:
                raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, 'Error al crear usuario.')
            
    async def create_organizer(self, user: OrganizerCreate):
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

                new_user: User = User(**user.model_dump(), role= RoleUser.ORGANIZER)

                self.session.add(new_user)
                await self.session.commit()

                new_organizer: Organizer = Organizer(
                    name= user.name,
                    description= user.description,
                    user_id= new_user.id
                )

                self.session.add(new_organizer)
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
    
    async def refresh_token(self, user: User, token: str, refresh_token: str):
        try:
            statement = select(HistorialRefreshToken).where(
                HistorialRefreshToken.user_id == user.id,
                HistorialRefreshToken.refresh_token == refresh_token,
                HistorialRefreshToken.token == token
            )
            historial_rt: HistorialRefreshToken | None = (await self.session.exec(statement)).first()

            if not historial_rt:
                return JSONResponse(
                    status_code=status.HTTP_401_UNAUTHORIZED, 
                    content={'detail':'Credenciales no encontradas'}
                )

            rt_decode = await AuthService().decode_token(refresh_token)

            if rt_decode == False:
                await self.session.delete(historial_rt)
                await self.session.commit()

                return JSONResponse(
                    status_code=status.HTTP_401_UNAUTHORIZED, 
                    content={'detail':'Refresh token expirado.'}
                )

            new_token = await AuthService().create_token(user)
            new_refresh_token = await AuthService().create_refresh_token(user)

            historial_rt.token = new_token
            historial_rt.refresh_token = new_refresh_token

            await self.session.commit()

            return {"token": new_token, "refresh_token": new_refresh_token}

        except Exception as e:
            raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, 'Error al actualizar el token.')



