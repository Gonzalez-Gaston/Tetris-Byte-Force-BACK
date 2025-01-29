from asyncio import to_thread
from typing import List
from fastapi import APIRouter, HTTPException, UploadFile, status
from sqlmodel import select
from src.models.banned_model import UserBanned
from src.models.cloudinary_model import CloudinaryModel
from src.models.organizer_model import Organizer
from src.models.participant_model import Participant
from src.models.tournament_participants import TournamentParticipants
from src.models.tournaments import Tournament
from src.schemas.organizer_schemas.organizer_ban import OrganizerBan
from src.schemas.organizer_schemas.organizer_data import OrganizerData
from src.schemas.organizer_schemas.organizer_update import OrganizerUpdate
from sqlmodel.ext.asyncio.session import AsyncSession
from fastapi.responses import JSONResponse
from src.schemas.tournament_schemas.tournament_name import TournamentName
from src.schemas.user_schema.user_full import UserFull
from sqlalchemy.orm import selectinload, joinedload

user_router = APIRouter()

class OrganizerService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def organizer_update(self, user: UserFull, image: UploadFile | None, organizer_update: OrganizerUpdate):
        try:
            organizer: Organizer = await self.session.get(Organizer, user.full.id)

            result = {}
            if image is not None:
                result = await to_thread(
                    CloudinaryModel().upload_image, 
                    image,
                    "organizer",
                    user.full.id
                )

            organizer.description = organizer_update.description
            if image is not None:
                organizer.url_image = result.get('secure_url', organizer.url_image)

            await self.session.commit()

            return JSONResponse(
                status_code=status.HTTP_200_OK, 
                content={
                    "detail": "Usuario actualizado correctamente."
                }
            )
        except Exception as e:
            raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, 'Error al actualizar usuario.')

    async def get_tournaments_created(self, user: UserFull):
        try:
            sttmt = (select(Tournament.id, Tournament.name).where(Tournament.organizer_id == user.full.id))
            tournaments: List[Tournament] = (await self.session.exec(sttmt)).all()

            list_tournaments: List[TournamentName] = [TournamentName.model_validate(tour).model_dump() for tour in tournaments]

            return JSONResponse(
                    content={"tournaments": list_tournaments},
                    status_code= status.HTTP_200_OK
                )

        except Exception as e:
            raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, "Error al intentar obtener los torneos")
  
    async def ban_participant(self, user: UserFull, data_ban: OrganizerBan):
        try:
            participant: Participant | None = await self.session.get(Participant, data_ban.participant_id)
            if participant is None:
                return JSONResponse(
                    status_code= status.HTTP_404_NOT_FOUND, 
                    content={
                        "detail": "Participante no encontrado."
                    }
                )    
            
            tournament: Tournament | None = await self.session.get(Tournament, data_ban.tournament_id)
            if tournament is None:
                return JSONResponse(
                    status_code= status.HTTP_404_NOT_FOUND, 
                    content={
                        "detail": "Torneo no encontrado."
                    }
                )  
            
            if tournament.organizer_id != user.full.id:
                return JSONResponse(
                    status_code= status.HTTP_403_FORBIDDEN, 
                    content={
                        "detail": "No tienes permisos para banear a este usuario."
                    }
                )  
            
            self.session.add(UserBanned(**data_ban.model_dump()))
            await self.session.flush()

            sttmt_register = select(TournamentParticipants).where(
                TournamentParticipants.participant_id == data_ban.participant_id, TournamentParticipants.tournament_id == data_ban.tournament_id
            )
            register: TournamentParticipants | None = (await self.session.exec(sttmt_register)).first()

            if register is None:
                return JSONResponse(
                    status_code= status.HTTP_404_NOT_FOUND, 
                    content={
                        "detail": "Registro no encontrado."
                    }
                )  
            
            await self.session.delete(register)

            await self.session.commit()

            return JSONResponse(
                status_code= status.HTTP_204_NO_CONTENT, 
                content={
                    "detail": "Usuario baneado correctamente."
                }
            )
        except Exception as e:
            raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, 'Error al banear usuario.')
        

    async def get_organizer_data(self, organizer_id: str):
        try:
            sttmt = (
                select(
                    Organizer
                ).options(joinedload(Organizer.tournaments))
                .where(Organizer.id == organizer_id)
            )

            organizer: Organizer = (await self.session.exec(sttmt)).first()

            if organizer is None:
                return JSONResponse(
                    status_code= status.HTTP_404_NOT_FOUND, 
                    content={
                        "detail": "Organizador no encontrado."
                    }
                )

            organizer_data: OrganizerData = OrganizerData(**organizer.model_dump(), tournaments_created= len(organizer.tournaments))

            return JSONResponse(
                content={
                    "organizer": organizer_data.model_dump()
                },
                status_code= status.HTTP_200_OK
            )
        except Exception as e:
            raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, "Error al intentar obtener usuario")
    