from asyncio import to_thread
from datetime import date, datetime, timedelta, timezone
import uuid
import bcrypt
from fastapi import HTTPException, status
from src.models.organizer_model import Organizer
from src.models.participant_model import Participant
from src.models.refresh_token import HistorialRefreshToken
from src.models.user_model import RoleUser, User
from src.schemas.organizer_schemas.organizer_create import OrganizerCreate
from src.schemas.organizer_schemas.organizer_update import OrganizerUpdate
from src.schemas.participant_schemas.participant_create import ParticipantCreate
from sqlmodel import select, or_
from sqlmodel.ext.asyncio.session import AsyncSession
from fastapi.responses import JSONResponse
from src.schemas.participant_schemas.participant_update import ParticipantUpdate
from src.schemas.user_schema.user_credentials import UserCredentials
from src.schemas.user_schema.user_full import UserFull
from src.services.auth_service import AuthService
from src.models.cloudinary_model import CloudinaryModel

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

            sttmt_rt = token.copy()
            sttmt_rt['user_id'] = user.id
            sttmt_rt['expire'] = datetime.now(timezone.utc) + timedelta(days=7)

            self.session.add(HistorialRefreshToken(**sttmt_rt))

            await self.session.commit()

            return JSONResponse(
                content=token,
                status_code=status.HTTP_200_OK
            )

        except Exception as e:
            raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, "Error al intentar loguear")
        
    async def logout(self, user, token, refresh_token):
        try:
            statement = select(HistorialRefreshToken).where(
                HistorialRefreshToken.user_id == user.user.id,
                HistorialRefreshToken.refresh_token == refresh_token,
                HistorialRefreshToken.token == token
                )
            token: HistorialRefreshToken | None = (await self.session.exec(statement)).first()

            if token is None:
                return JSONResponse(
                    content={"detail": "Credenciales incorrectas"},
                    status_code=status.HTTP_400_BAD_REQUEST
                )

            await self.session.delete(token)
            await self.session.commit()

            return JSONResponse(
                content={"detail": "Logout exitoso"},
                status_code=status.HTTP_204_NO_CONTENT
            )

        except Exception as e:
            raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, "Error al intentar logout")

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
                await self.session.flush()

                new_participant: Participant = Participant(
                    username= user.username,
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
                await self.session.flush()

                new_organizer: Organizer = Organizer(
                    username= user.username,
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
        user_dict = user.model_dump()
        for key, value in user_dict.items():
            if isinstance(value, date):
                user_dict[key] = value.isoformat()

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



