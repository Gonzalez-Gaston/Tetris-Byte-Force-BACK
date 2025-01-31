from asyncio import to_thread
from datetime import datetime, timedelta
from typing import List
from fastapi import APIRouter, HTTPException, UploadFile, status
from sqlalchemy import func
from src.models.banned_model import UserBanned
from src.models.cloudinary_model import CloudinaryModel
from src.models.participant_model import Participant
from src.models.tournament_participants import TournamentParticipants
from src.models.tournaments import StatusTournament, Tournament
from src.schemas.participant_schemas.participant_data import ParticipantData
from src.schemas.participant_schemas.participant_ranking import ParticipantRanking
from src.schemas.participant_schemas.participant_update import ParticipantUpdate
from sqlmodel import case, select, or_
from sqlmodel.ext.asyncio.session import AsyncSession
from fastapi.responses import JSONResponse
from src.schemas.tournament_schemas.tournament_inscription import InscriptionDTO, TournamentInsc, TournamentInscription
from src.schemas.user_schema.user_full import UserFull
from sqlalchemy.orm import selectinload, joinedload

user_router = APIRouter()

class ParticipantService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def register_tournament(self, tournament_id: str, user: UserFull):
        try:
            banned_sttmt = select(UserBanned).where(UserBanned.participant_id == user.full.id, UserBanned.tournament_id == tournament_id)
            banned: UserBanned | None = (await self.session.exec(banned_sttmt)).first()

            if banned is not None:
                return JSONResponse(
                    content={
                        "detail": "Usuario baneado en el torneo", 
                    },
                    status_code= status.HTTP_400_BAD_REQUEST
                )

            sttmt = select(TournamentParticipants).where(
                TournamentParticipants.tournament_id == tournament_id,
                TournamentParticipants.participant_id == user.full.id
            )
            register: TournamentParticipants | None = (await self.session.exec(sttmt)).first()

            if register is not None:
                return JSONResponse(
                    content={
                        "detail": "Ya se encuentra registrado", 
                    },
                    status_code= status.HTTP_400_BAD_REQUEST
                )

            new_register: TournamentParticipants = TournamentParticipants(
                participant_id= user.full.id,
                tournament_id= tournament_id
            )

            self.session.add(new_register)

            await self.session.commit()

            return JSONResponse(
                content={"detail":"Registrado con éxito!"},
                status_code=status.HTTP_201_CREATED
            )

        except Exception as e:
            raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, "Error al intentar registrarse en el torneo")
   
    async def cancel_register_tournament(self, tournament_id: str, user: UserFull):
        try:
            sttmt = select(TournamentParticipants).where(
                TournamentParticipants.tournament_id == tournament_id,
                TournamentParticipants.participant_id == user.full.id
            )
            register: TournamentParticipants | None = (await self.session.exec(sttmt)).first()

            if register is None:
                return JSONResponse(
                    content={
                        "detail": "Registro no entontrado", 
                    },
                    status_code= status.HTTP_404_NOT_FOUND
                )

            await self.session.delete(register)
            await self.session.commit()

            return JSONResponse(
                content={"detail":"Registro cancelado con éxito!"},
                status_code=status.HTTP_204_NO_CONTENT
            )

        except Exception as e:
            raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, "Error al intentar crear torneo")
        
    async def registered_tournaments(self, user: UserFull):
        try:
            sttmt = select(TournamentParticipants).where(
                TournamentParticipants.participant_id == user.full.id
            ).join(Tournament, Tournament.id == TournamentParticipants.tournament_id)
            registers: List[TournamentParticipants] = (await self.session.exec(sttmt)).all()

            if not registers:
                return JSONResponse(
                    content={
                        "detail": "No se encontraron registros", 
                    },
                    status_code= status.HTTP_404_NOT_FOUND
                )

            tournaments = []
            for register in registers:
                tournament = register.tournament
                tournaments.append(tournament)

            return JSONResponse(
                    content={"tournaments": tournaments},
                    status_code= status.HTTP_200_OK
                )

        except Exception as e:
            raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, "Error al intentar obtener los torneos")
        
    async def participant_update(self, user: UserFull, image: UploadFile | None, participant_update: ParticipantUpdate):
        try:
            participant: Participant = await self.session.get(Participant, user.full.id)

            result = {}
            if image is not None:
                result = await to_thread(
                    CloudinaryModel().upload_image, 
                    image,
                    "participant",
                    user.full.id
                )

            participant.first_name = participant_update.first_name
            participant.last_name = participant_update.last_name
            participant.date_of_birth = participant_update.date_of_birth
            if image is not None:
                participant.url_image = result.get('secure_url', participant.url_image)

            await self.session.commit()

            return JSONResponse(
                status_code=status.HTTP_204_NO_CONTENT, 
                content={
                    "detail": "Usuario actualizado correctamente."
                }
            )
        except Exception as e:
            raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, 'Error al actualizar usuario.')
        
    async def registered_tournaments_ids(self, user: UserFull):
        try:
            sttmt = (select(TournamentParticipants)
                        .join(Tournament, Tournament.id == TournamentParticipants.tournament_id)
                            # .options(selectinload(TournamentParticipants.tournament))
                        .where(TournamentParticipants.participant_id == user.full.id, Tournament.status == StatusTournament.PROXIMO)
                        ).options(selectinload(TournamentParticipants.tournament))
            tournaments: List[TournamentParticipants] = (await self.session.exec(sttmt)).all()

            list_tournaments:List[TournamentInscription] = [TournamentInscription(
                tournament= TournamentInsc.model_validate(tournament.tournament),
                inscription= InscriptionDTO.model_validate(tournament)
            ).model_dump(mode='json') for tournament in tournaments]

            return JSONResponse(
                    content={"tournaments_ids": list_tournaments},
                    status_code= status.HTTP_200_OK
                )

        except Exception as e:
            raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, "Error al intentar obtener los torneos")
        
    
    async def confirm_participation(self, tournament_id: str, user: UserFull):
        try:
            sttmt = select(TournamentParticipants).where(
                TournamentParticipants.tournament_id == tournament_id,
                TournamentParticipants.participant_id == user.full.id
            ).join(Tournament, Tournament.id == TournamentParticipants.tournament_id).options(
            selectinload(TournamentParticipants.tournament)  # Cargar la relación 'tournament'
        )
            register: TournamentParticipants | None = (await self.session.exec(sttmt)).unique().first()

            if register is None:
                return JSONResponse(
                    content={
                        "detail": "Registro no entontrado", 
                    },
                    status_code= status.HTTP_404_NOT_FOUND
                )
            
            tournament: Tournament = register.tournament

            if tournament.status != StatusTournament.PROXIMO:
                return JSONResponse(
                    content={
                        "detail": "No se puede confirmar participación en torneos pasados, cancelados o en curso", 
                    },
                    status_code= status.HTTP_400_BAD_REQUEST
                )
            
            # if tournament.start - timedelta(hours=1) > datetime.now():
            #     return JSONResponse(
            #         content={
            #             "detail": "Solo se puede copnfirmar la participación una hora antes del inicio del torneo", 
            #         },
            #         status_code= status.HTTP_400_BAD_REQUEST
            #     ) 

            register.confirm = True

            await self.session.commit()


            return JSONResponse(
                content={"detail":"Participación confirmada con éxito!"},
                status_code=status.HTTP_204_NO_CONTENT
            )

        except Exception as e:
            raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, "Error al intentar confirmar participación")

    async def get_ranking(self):
        try:
            sttmt = (
                select(
                    TournamentParticipants.participant_id,
                    Participant.username.label("username"),
                    Participant.url_image.label("url_image"),
                    Participant.user_id.label("user_id"),
                    func.sum(TournamentParticipants.points).label("points"),
                    func.sum(TournamentParticipants.win).label("win"),
                    func.sum(TournamentParticipants.lose).label("lose"),
                    func.count(
                        case((TournamentParticipants.final_position == 'Ganador', 1), else_=None)
                    ).label("tournaments_win")
                )
                .join(Participant, Participant.id == TournamentParticipants.participant_id)
                .group_by(
                    TournamentParticipants.participant_id,
                    Participant.username,
                    Participant.url_image,
                    Participant.user_id,
                )
            )

            # Ejecutar la consulta
            results = (await self.session.exec(sttmt)).all()

            ranking: List[ParticipantRanking] = [
                ParticipantRanking(
                    id=row.participant_id,
                    username=row.username,
                    url_imgae=row.url_image,
                    user_id=row.user_id,
                    points=int(row.points or 0),
                    win=int(row.win or 0),
                    lose=int(row.lose or 0),
                    tournaments_win=int(row.tournaments_win or 0)
                ).model_dump()
                for row in results
            ]

            return sorted(ranking, key=lambda x: x['points'], reverse=True)
        except Exception as e:
            print(e)
            raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, "Error al intentar obtener ranking")
        
    async def get_participant_data(self, participant_id: str):
        try:
            sttmt = (
                select(
                    Participant.id,
                    Participant.username,
                    Participant.first_name,
                    Participant.last_name,
                    Participant.url_image,
                    Participant.user_id,
                    func.sum(TournamentParticipants.points).label("points"),
                    func.sum(TournamentParticipants.win).label("win"),
                    func.sum(TournamentParticipants.lose).label("lose"),
                    func.count(
                        case((TournamentParticipants.final_position == 'Ganador', 1), else_=None)
                    ).label("tournaments_win")
                )
                .join(TournamentParticipants, Participant.id == TournamentParticipants.participant_id)
                .where(TournamentParticipants.participant_id == participant_id)
            )

            participant = (await self.session.exec(sttmt)).first()

            participant_data: ParticipantData = ParticipantData(
                id=participant.id,
                username=participant.username,
                first_name=participant.first_name,
                last_name=participant.last_name,
                url_image=participant.url_image,
                user_id=participant.user_id,
                points=int(participant.points or 0),
                win=int(participant.win or 0),
                lose=int(participant.lose or 0),
                tournaments_win=int(participant.tournaments_win or 0)
            )

            return JSONResponse(
                content={
                    "participant": participant_data.model_dump()
                },
                status_code= status.HTTP_200_OK
            )
        except Exception as e:
            raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, "Error al intentar obtener usuario")