from fastapi import APIRouter, Depends, File, UploadFile, Form
from sqlmodel.ext.asyncio.session import AsyncSession
from src.config.decorators import authorization
from src.database.db import db
from src.models.user_model import RoleUser
from src.schemas.organizer_schemas.organizer_update import OrganizerUpdate
from src.schemas.user_schema.user_full import UserFull
from src.services.auth_service import AuthService
from src.services.organizer_service import OrganizerService

organizer_router = APIRouter(prefix='/organizer', tags=['Organizer'])

auth = AuthService()

@organizer_router.put('/organizer_update')
@authorization(roles=[RoleUser.ORGANIZER])
async def organizer_update(
    description: str = Form(...),
    image: UploadFile = File(None),
    user: UserFull = Depends(auth.get_current_user),
    session: AsyncSession = Depends(db.get_session),
):
    return await OrganizerService(session).organizer_update(user, image, OrganizerUpdate(description= description))