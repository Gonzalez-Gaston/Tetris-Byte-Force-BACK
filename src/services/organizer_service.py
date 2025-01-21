from asyncio import to_thread
from fastapi import APIRouter, HTTPException, UploadFile, status
from src.models.cloudinary_model import CloudinaryModel
from src.models.organizer_model import Organizer
from src.schemas.organizer_schemas.organizer_update import OrganizerUpdate
from sqlmodel.ext.asyncio.session import AsyncSession
from fastapi.responses import JSONResponse
from src.schemas.user_schema.user_full import UserFull

user_router = APIRouter()

class OrganizerService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def organizer_update(self, user: UserFull, image: UploadFile, organizer_update: OrganizerUpdate):
        try:
            organizer: Organizer = await self.session.get(Organizer, user.full.id)

            result = {}
            if image:
                result = await to_thread(
                    CloudinaryModel().upload_image, 
                    image,
                    "organizer",
                    user.full.id
                )

            organizer.description = organizer_update.description
            if image:
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

  

    