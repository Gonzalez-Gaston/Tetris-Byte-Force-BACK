import pytest
from pytest_mock import mocker
from datetime import datetime, timezone
from src.models.tournaments import Tournament, StatusTournament
from src.services.tournament_service import TournamentService
from src.models.organizer_model import Organizer
from unittest.mock import AsyncMock
from fastapi import status
from fastapi.responses import JSONResponse

@pytest.mark.asyncio
async def test_get_all_tournaments(mocker):
    # Crear un mock de la sesión de la base de datos utilizando mocker
    mock_session = mocker.MagicMock()

    # Crear datos de prueba
    organizer = Organizer(id="organizer_1", name="Organizer 1")
    tournament_1 = Tournament(
        id="1", name="Tournament 1", status=StatusTournament.PROXIMO,
        start=datetime.now(timezone.utc), end=datetime.now(timezone.utc),
        organizer=organizer, participants=[])

    tournament_2 = Tournament(
        id="2", name="Tournament 2", status=StatusTournament.CURSO,
        start=datetime.now(timezone.utc), end=datetime.now(timezone.utc),
        organizer=organizer, participants=[])

    # Simular el comportamiento del exec() con un mock que devuelva una lista de torneos
    mock_session.exec.return_value = [tournament_1, tournament_2]

    # Crear una instancia del servicio y llamar a la función
    service = TournamentService(session=mock_session)

    # Llamar a la función sin filtro (None significa sin filtro)
    tournaments = await service.get_all_tournaments(None)

    # Simular la respuesta de FastAPI (esto debería retornar un JSONResponse)
    response = JSONResponse(content={"tournaments": tournaments, "length": len(tournaments)})

    # Verificar que la respuesta tenga la estructura correcta
    assert response.status_code == status.HTTP_200_OK
    response_json = response.json()

    # Verificar que la respuesta contiene los datos esperados
    assert "tournaments" in response_json
    assert "length" in response_json
    assert len(response_json["tournaments"]) == 2  # Asegúrate de que la respuesta tenga 2 torneos
    assert response_json["length"] == 2  # Asegúrate de que el campo length es 2

@pytest.mark.asyncio
async def test_get_all_tournaments_with_filter(mocker):
    # Crear un mock de la sesión de la base de datos utilizando mocker
    mock_session = mocker.MagicMock()

    # Crear datos de prueba
    organizer = Organizer(id="1", name="Organizer 1")
    tournament_1 = Tournament(
        id="1", name="Tournament 1", status=StatusTournament.PROXIMO,
        start=datetime.now(timezone.utc), end=datetime.now(timezone.utc),
        organizer=organizer, participants=[])

    tournament_2 = Tournament(
        id="2", name="Tournament 2", status=StatusTournament.CURSO,
        start=datetime.now(timezone.utc), end=datetime.now(timezone.utc),
        organizer=organizer, participants=[])

    # Simular el comportamiento del exec() con un mock que devuelva solo los torneos con estado "CURSO"
    mock_session.exec.return_value = [tournament_2]  # Solo uno con "CURSO"

    # Crear una instancia del servicio y llamar a la función con el filtro de estado
    service = TournamentService(session=mock_session)

    # Llamar a la función con el filtro de estado "CURSO"
    tournaments = await service.get_all_tournaments(StatusTournament.CURSO)

    # Simular la respuesta de FastAPI (esto debería retornar un JSONResponse)
    response = JSONResponse(content={"tournaments": tournaments, "length": len(tournaments)})

    # Verificar que la respuesta tenga la estructura correcta
    assert response.status_code == status.HTTP_200_OK
    response_json = response.json()

    # Verificar que la respuesta contiene los datos esperados
    assert "tournaments" in response_json
    assert "length" in response_json
    assert len(response_json["tournaments"]) == 1  # Asegúrate de que la respuesta tenga 1 torneo
    assert response_json["length"] == 1  # Asegúrate de que el campo length es 1
