from datetime import date
import pytest
from unittest.mock import AsyncMock, patch
from fastapi import UploadFile
import sqlalchemy
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel import SQLModel, create_engine
from src.services.tournament_service import TournamentService
from src.models.tournaments import TypeTournament, Tournament
from src.models.participant_model import Participant
from src.schemas.tournament_schemas.tournament_create import TournamentCreate
from src.schemas.user_schema.user_full import UserFull

# Configuración de la base de datos para pruebas (SQLite en memoria)
engine = create_engine("sqlite:///:memory:", echo=True)

# Evitamos crear las tablas si ya están creadas
@pytest.fixture(scope="session", autouse=True)
def setup_db():
    # Conexión en memoria y desactivar claves foráneas en SQLite
    with engine.connect() as conn:
        # Usamos `text()` para envolver la cadena SQL y ejecutarla
        conn.execute(sqlalchemy.text('PRAGMA foreign_keys=OFF;'))  # Desactiva las claves foráneas en SQLite
        SQLModel.metadata.create_all(engine, checkfirst=True)  # Crear todas las tablas
        conn.execute(sqlalchemy.text('PRAGMA foreign_keys=ON;'))  # Reactiva las claves foráneas después de crear las tablas
    
    yield engine
    SQLModel.metadata.drop_all(engine)  # Limpieza de las tablas después de todas las pruebas

@pytest.mark.asyncio
async def test_create_tournament(setup_db):
    # Mock de la sesión de la base de datos
    mock_session = AsyncMock(spec=AsyncSession)

    # Mock de usuario organizador
    mock_user = UserFull(full=Participant(
        username="test_user",
        first_name="Test",
        last_name="User",
        date_of_birth=date(2000, 1, 1),
        url_image="https://example.com/image.png",
        user_id="1234"
    ))

    # Datos de torneo simulado
    tournament_data = TournamentCreate(
        name="Torneo Prueba",
        description="Un torneo de prueba",
        type=TypeTournament.SIMPLE,
        status="proximo",
        format=3,
        number_participants=8,
        start="2025-06-01T10:00:00Z",
        end="2025-06-05T18:00:00Z"
    )

    # Mock de imagen simulada
    mock_image = AsyncMock(spec=UploadFile)
    mock_image.filename = "test_image.jpg"

    # Mock de Cloudinary para evitar subida real
    with patch("src.models.cloudinary_model.CloudinaryModel.upload_image", return_value={"secure_url": "http://mocked_url.com/image.jpg"}):
        service = TournamentService(mock_session)

        # Ejecutamos la función
        response = await service.create_tournament(tournament_data, mock_user, mock_image)

        # Verificaciones
        assert response.status_code == 201  # Código HTTP esperado
        assert "tournament_id" in response.body.decode()  # Verifica que devuelve un ID
