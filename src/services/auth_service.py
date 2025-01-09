from datetime import datetime, timedelta, timezone
from uuid import UUID
from fastapi import Depends, HTTPException, status
from sqlmodel.ext.asyncio.session import AsyncSession
import jwt
from decouple import config
from fastapi.security import OAuth2PasswordBearer
from src.models.user_model import User
from src.database.db import db
from typing import Annotated

oauth_scheme = OAuth2PasswordBearer(tokenUrl='/auth')


class AuthService:
    def __init__(self, session: AsyncSession = None):
        self.session = session

    async def auth(self, user:User):
        return  {
            'access_token': await self.create_token(user),
            'token_type': 'Bearer'
        }

    async def create_token(self, user: User, hours: int = 8):
        expire = datetime.now(timezone.utc) + timedelta(hours=hours)
        data = {
            'user_id': str(user.id),
            'email': user.email,
            'expire': expire.isoformat()  # Convert datetime to ISO format string
        }
        encoded_jwt = jwt.encode(data, config('SECRET_KEY'), algorithm="HS256")
        return encoded_jwt

    async def decode_token(self, token):
        try:
            return jwt.decode(token, config('SECRET_KEY'), algorithms=["HS256"])
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
            
            user: User | None = await session.get(User, UUID(data['user_id']) )

            if not user:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Usuario no encontrado",
                )

            return user
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Access Token no válido",
                headers={"WWW-Authenticate": "Bearer"},
            )

    # async def get_current_user(self, token: str = Depends(oauth_scheme)) -> User:
    #     data = self.decode_token(token)
    #     if data:
    #         statemen = User.get(data['user_id'])
    #         result: User | None = (await self.session.exec(statemen)).first()
    #         return result
    #     else:
    #         raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Access Token no valido', headers={ 'WWW-Authenticate' : 'Bearer'})

# def require_auth(auth_service: AuthService):
#     """
#     Decorador para autenticar al usuario mediante AuthService.
#     """
#     def decorator(func):
#         @wraps(func)
#         async def wrapper(*args, **kwargs):
#             # Obtener el token directamente desde el esquema OAuth2
#             token = kwargs.get("token") or await oauth_scheme(kwargs["request"])
#             if not token:
#                 raise HTTPException(
#                     status_code=status.HTTP_401_UNAUTHORIZED,
#                     detail="No se encontró un token de autenticación",
#                     headers={"WWW-Authenticate": "Bearer"},
#                 )
            
#             # Obtener el usuario actual usando AuthService
#             user = await auth_service.get_current_user(token)
#             kwargs["user"] = user  # Agregar el usuario autenticado a los kwargs
            
#             return await func(*args, **kwargs)
#         return wrapper
#     return decorator

# def require_auth(auth_service: AuthService):
#     """
#     Decorador para autenticar al usuario y pasarlo a la función decorada.
#     """
#     def decorator(func: Callable):
#         @wraps(func)
#         async def wrapper(*args, **kwargs):
#             # Obtener el request del contexto
#             request: Request = kwargs.get("request")
#             if not request:
#                 raise HTTPException(
#                     status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#                     detail="El decorador requiere 'request' como argumento",
#                 )

#             # Obtener el token desde el esquema OAuth2
#             token = await oauth_scheme(request)

#             # Obtener el usuario autenticado
#             user = await auth_service.get_current_user(token)

#             # Inyectar el usuario como argumento
#             kwargs["user"] = user
#             return await func(*args, **kwargs)
#         return wrapper
#     return decorator