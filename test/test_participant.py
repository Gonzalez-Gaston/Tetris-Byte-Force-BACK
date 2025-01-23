# import pytest
# from httpx import AsyncClient
# from fastapi import FastAPI
# from src.services.participant_service import ParticipantService
# from src.models.participant_model import Participant
# from src.models.tournament_participants import TournamentParticipants
# from src.schemas.user_schema.user_full import UserFull
# from src.database.db import db

# @pytest.mark.asyncio
# async def test_register_tournament():
#     app = FastAPI()
#     async with AsyncClient(app=app, base_url="http://test") as ac:
#         async with db.get_session() as session:
#             participant_service = ParticipantService(session)
#             user_full = UserFull(user=User(id="test_id", username="test_user", email="test@example.com", password_hash="test_hash"), full=Participant(id="test_id", username="test_user", first_name="Test", last_name="User", date_of_birth="2000-01-01", user_id="test_id"))
#             response = await participant_service.register_tournament("test_tournament_id", user_full)
#             assert response.status_code == 201
#             assert response.json()["detail"] == "Registrado con éxito!"

# @pytest.mark.asyncio
# async def test_confirm_participation():
#     app = FastAPI()
#     async with AsyncClient(app=app, base_url="http://test") as ac:
#         async with db.get_session() as session:
#             participant_service = ParticipantService(session)
#             user_full = UserFull(user=User(id="test_id", username="test_user", email="test@example.com", password_hash="test_hash"), full=Participant(id="test_id", username="test_user", first_name="Test", last_name="User", date_of_birth="2000-01-01", user_id="test_id"))
#             tournament_participant = TournamentParticipants(id="test_tp_id", participant_id="test_id", tournament_id="test_tournament_id")
#             session.add(tournament_participant)
#             await session.commit()
#             response = await participant_service.confirm_participation("test_tp_id", user_full)
#             assert response.status_code == 200
#             assert response.json()["detail"] == "Participación confirmada con éxito!"
