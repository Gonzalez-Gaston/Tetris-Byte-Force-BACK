from datetime import date
from fastapi.testclient import TestClient
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi import UploadFile
import sqlalchemy
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel import SQLModel, create_engine

# Ajustar las rutas de importación de los servicios y modelos
from models.banned_model import UserBanned
from src.services.tournament_service import TournamentService
from src.models.tournaments import TypeTournament, Tournament
from src.models.participant_model import Participant
from src.schemas.tournament_schemas.tournament_create import TournamentCreate
from src.schemas.user_schema.user_full import UserFull

@pytest.fixture
def mock_db(mocker):
    # Mock de la sesión de base de datos
    mock_session = MagicMock()
    mocker.patch('myapp.TournamentService.session', mock_session)
    return mock_session

@pytest.fixture
def client():
    return TestClient(app)

# Test de la función `register_tournament`
@pytest.mark.asyncio
async def test_register_tournament(mock_db, client):
    # Simular un usuario y un torneo
    user = UserFull(id="123", name="Test User")
    tournament_id = "tournament_001"

    # Caso: Usuario baneado
    mock_db.exec.return_value.first.return_value = UserBanned(participant_id="123", tournament_id="tournament_001")
    
    response = await client.post(f"/tournaments/{tournament_id}/register", json=user.dict())
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json() == {"detail": "Usuario baneado en el torneo"}

    # Caso: Usuario ya registrado
    mock_db.exec.return_value.first.return_value = TournamentParticipants(participant_id="123", tournament_id="tournament_001")
    
    response = await client.post(f"/tournaments/{tournament_id}/register", json=user.dict())
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json() == {"detail": "Ya se encuentra registrado"}

    # Caso: Registro exitoso
    mock_db.exec.return_value.first.return_value = None  # No encontrado ni baneado ni registrado
    mock_db.add.return_value = None  # No devuelve nada
    mock_db.commit.return_value = None

    response = await client.post(f"/tournaments/{tournament_id}/register", json=user.dict())
    assert response.status_code == status.HTTP_201_CREATED
    assert response.json() == {"detail": "Registrado con éxito!"}
