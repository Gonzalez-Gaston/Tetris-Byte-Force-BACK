import asyncio
from datetime import datetime, timedelta
from typing import List
from fastapi import HTTPException, WebSocket, Depends, status
from sqlmodel import select
from src.database.db import db
from src.models.tournaments import StatusTournament, Tournament
from src.schemas.tournament_schemas.tournament_socket import TournamentSocket
from sqlmodel.ext.asyncio.session import AsyncSession

class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self.tournaments: List[TournamentSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        asyncio.create_task(self.monitor_tournaments())

        await self.get_tournamnets()

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def send_personal_message(self, message: dict, websocket: WebSocket):
        await websocket.send_json(message)

    async def broadcast(self, message: dict):
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception as e:
                print(e)
    async def monitor_tournaments(self):
        while True:
            now = datetime.now()
            for tournament in self.tournaments[:]:
                if now >= tournament.start - timedelta(hours=1): 
                    message = {
                        "event": "tournament_start",
                        "tournament":{
                            "id": tournament.id,
                            "name": tournament.name,
                            "start": tournament.start.isoformat()
                        },
                        "message": "El torneo comenzará dentro de 1 hora."
                    }
                    await self.broadcast(message)
                    self.tournaments.remove(tournament)
            await asyncio.sleep(300)

    async def get_tournamnets(self):
        async for session in db.get_session():
            try:
                sttmt = select(
                    Tournament.id,
                    Tournament.name,
                    Tournament.start
                    ).where(Tournament.status == StatusTournament.PROXIMO)
                
                tournaments = (await session.exec(sttmt)).all()

                self.tournaments = [TournamentSocket(id= tour.id, name= tour.name, start= tour.start) for tour in tournaments]
            except Exception as e:
                raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, 'Error al obtener los torneos')
            
    async def add_tournament(self, tournament: TournamentSocket):
        self.tournaments.append(tournament)

