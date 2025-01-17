from sqlmodel import SQLModel, Field
import uuid

class Organizer(SQLModel, table=True):
    __tablename__ = 'organizers'
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    name: str = Field(max_length=100)
    description: str | None = Field(default=None)
    user_id: str = Field(foreign_key='users.id')
