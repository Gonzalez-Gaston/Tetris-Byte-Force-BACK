# import pytest
# from httpx import AsyncClient
# from fastapi import FastAPI
# from src.services.auth_service import AuthService
# from src.models.user_model import User
# from src.database.db import db

# @pytest.mark.asyncio
# async def test_get_token():
#     app = FastAPI()
#     async with AsyncClient(app=app, base_url="http://test") as ac:
#         async with db.get_session() as session:
#             auth_service = AuthService(session)
#             user = User(id="test_id", username="test_user", email="test@example.com", password_hash="test_hash")
#             token = await auth_service.get_token(user)
#             assert "token" in token
#             assert "refresh_token" in token

# @pytest.mark.asyncio
# async def test_decode_token():
#     app = FastAPI()
#     async with AsyncClient(app=app, base_url="http://test") as ac:
#         async with db.get_session() as session:
#             auth_service = AuthService(session)
#             user = User(id="test_id", username="test_user", email="test@example.com", password_hash="test_hash")
#             token = await auth_service.create_token(user)
#             decoded_data = await auth_service.decode_token(token)
#             assert decoded_data["user_id"] == "test_id"
#             assert decoded_data["username"] == "test_user"
#             assert decoded_data["email"] == "test@example.com"
