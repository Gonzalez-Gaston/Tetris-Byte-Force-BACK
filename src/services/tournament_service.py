import json
from typing import List
from fastapi import HTTPException, status
from src.models.tournament_participants import TournamentParticipants
from src.models.tournaments import StatusTournament, Tournament
from src.schemas.tournament_schemas.tournament_response import TournamentResponse
from sqlmodel import select, or_
from sqlmodel.ext.asyncio.session import AsyncSession
from fastapi.responses import JSONResponse
from sqlalchemy.orm import selectinload


class TournamentService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_all_tournaments(self, status_filter: StatusTournament | None):
        try:
            if status_filter is None:
                stmt = select(Tournament)
            else:
                stmt = select(Tournament).where(Tournament.status == status_filter)

            tournaments: List[Tournament] = (await self.session.exec(stmt)).all()

            list_tour = [TournamentResponse.model_validate(tour).model_dump(mode="json") for tour in tournaments]

            return JSONResponse(
                content={
                    "tournaments": list_tour, 
                    "length": len(list_tour)
                },
                status_code= status.HTTP_200_OK
            )

        except Exception as e:
            print(f"Error al obtener torneos: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error al intentar obtener torneos"
            )
        
    async def get_name_tournaments(self, name_filter: str):
        try:
            stmt = select(Tournament).where(Tournament.name.like(f"%{name_filter}%"))

            tournaments: List[Tournament] = (await self.session.exec(stmt)).all()

            list_tour = [TournamentResponse.model_validate(tour).model_dump(mode="json") for tour in tournaments]

            return JSONResponse(
                content={
                    "tournaments": list_tour, 
                    "length": len(list_tour)
                },
                status_code= status.HTTP_200_OK
            )

        except Exception as e:
            print(f"Error al obtener torneos: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error al intentar obtener torneos"
            )
        
    async def get_tournament(self, id: str):
        try:
            # stmt = (
            #     select(Tournament)
            #     .where(Tournament.id == id)
            #     .options(selectinload(Tournament.participants).selectinload(TournamentParticipants.participant))
            # )
            # tournament = (await self.session.exec(stmt)).first()

            tournament: Tournament | None = await self.session.get(Tournament, id)

            if tournament is None:
                return JSONResponse(
                content={
                    "detail": "Torneo no entontrado", 
                },
                status_code= status.HTTP_404_NOT_FOUND
            )

            return JSONResponse(
                content={
                    "tournament": TournamentResponse.model_validate(tournament).model_dump(mode="json") 
                },
                status_code= status.HTTP_200_OK
            )

        except Exception as e:
            print(f"Error al obtener torneos: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error al intentar obtener torneos"
            )