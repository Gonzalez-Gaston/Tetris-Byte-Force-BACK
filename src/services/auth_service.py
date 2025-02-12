from datetime import datetime, timedelta, timezone
from uuid import UUID
from fastapi import Depends, HTTPException, status
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession
import jwt
from decouple import config
from fastapi.security import OAuth2PasswordBearer
from src.models.organizer_model import Organizer
from src.models.participant_model import Participant
from src.models.user_model import RoleUser, User
from src.database.db import db
from typing import Annotated

from src.schemas.user_schema.user_full import UserFull

oauth_scheme = OAuth2PasswordBearer(tokenUrl='/auth')

class AuthService:
    def __init__(self, session: AsyncSession = None):
        self.session = session

    async def get_token(self, user:User):
        return  {
            'token': await self.create_token(user),
            'refresh_token': await self.create_refresh_token(user),
        }

    async def create_token(self, user: User, hs: int = 2):
        expire = datetime.now(timezone.utc) + timedelta(hours=hs)
        data = {
            'user_id': user.id,
            'username': user.username,
            'email': user.email,
            'role': user.role,
            'expire': expire.isoformat()  # Convert datetime to ISO format string
        }
        encoded_jwt = jwt.encode(data, config('SECRET_KEY'), algorithm="HS256")
        return encoded_jwt

    async def create_refresh_token(self, user: User, days: int = 1):
        expire = datetime.now(timezone.utc) + timedelta(days=days)
        data = {
            'expire': expire.isoformat()  # Convert datetime to ISO format string
        }
        encoded_jwt = jwt.encode(data, config('SECRET_KEY'), algorithm="HS256")
        return encoded_jwt

    async def decode_token(self, token):
        try:
            data = jwt.decode(token, config('SECRET_KEY'), algorithms=["HS256"])
            expire = datetime.fromisoformat(data['expire'])
            if datetime.now(timezone.utc) >= expire:
                return False
            return data
        except jwt.ExpiredSignatureError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token expirado",
                headers={"WWW-Authenticate": "Bearer"},
            )
        except Exception as e:
            return None

    async def get_current_user(self, token: Annotated[str, Depends(oauth_scheme)], session: AsyncSession = Depends(db.get_session)):
        try:
            if not token:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="No se encontró un token de autenticación",
                    headers={"WWW-Authenticate": "Bearer"},
                )

            data = await self.decode_token(token)

            if not data:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Access Token no válido",
                    headers={"WWW-Authenticate": "Bearer"},
                )

            user: User | None = await session.get(User, data['user_id'] )

            if not user:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Usuario no encontrado",
                )

            if user.role == RoleUser.PARTICIPANT:
                sttmt = select(Participant).where(Participant.user_id == user.id)
                full: Participant | None = (await session.exec(sttmt)).first()

                if full is None:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail="Participante no encontrado",
                    )

            if user.role == RoleUser.ORGANIZER:
                sttmt = select(Organizer).where(Organizer.user_id == user.id)
                full: Organizer | None = (await session.exec(sttmt)).first()

                if full is None:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail="Organizador no encontrado",
                    )

            return UserFull(
                user= user,
                full= full,
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Access Token no válido",
                headers={"WWW-Authenticate": "Bearer"},
            )

    async def get_user_refresh_token(self, token: Annotated[str, Depends(oauth_scheme)], session: AsyncSession = Depends(db.get_session)):
        try:
            if not token:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="No se encontró un token de autenticación",
                    headers={"WWW-Authenticate": "Bearer"},
                )

            data = jwt.decode(token, config('SECRET_KEY'), algorithms=["HS256"])

            if not data:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Access Token no válido",
                    headers={"WWW-Authenticate": "Bearer"},
                )

            expire = datetime.fromisoformat(data['expire'])
            if datetime.now(timezone.utc) < expire:
                return False

            user: User | None = await session.get(User, data['user_id'])

            if not user:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Usuario no encontrado",
                )

            return user,token,
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Access Token no válido",
                headers={"WWW-Authenticate": "Bearer"},
            )
