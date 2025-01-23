# import pytest
# from httpx import AsyncClient
# from fastapi import FastAPI
# from src.services.user_service import UserService
# from src.models.user_model import User
# from src.schemas.user_schema.user_create import UserCreate
# from src.database.db import db

# @pytest.mark.asyncio
# async def test_create_user():
#     app = FastAPI()
#     async with AsyncClient(app=app, base_url="http://test") as ac:
#         async with db.get_session() as session:
#             user_service = UserService(session)
#             user_create = UserCreate(username="test_user", email="test@example.com", password="test_password")
#             response = await user_service.create_user(user_create)
#             assert response.status_code == 201
#             assert response.json()["detail"] == "Usuario creado exitosamente."

# @pytest.mark.asyncio
# async def test_login():
#     app = FastAPI()
#     async with AsyncClient(app=app, base_url="http://test") as ac:
#         async with db.get_session() as session:
#             user_service = UserService(session)
#             user = User(id="test_id", username="test_user", email="test@example.com", password_hash="test_hash")
#             session.add(user)
#             await session.commit()
#             response = await user_service.login(UserCredentials(email="test@example.com", password="test_password"))
#             assert response.status_code == 200
#             assert "token" in response.json()
