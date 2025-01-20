from typing import List
from sqlmodel import Relationship, SQLModel, Field
import uuid

class Organizer(SQLModel, table=True):
    __tablename__ = 'organizers'
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    username: str = Field(max_length=50, unique=True)
    description: str | None = Field(default=None)
    url_image: str | None = Field(default=None)
    user_id: str = Field(foreign_key='users.id')
    tournaments: List["Tournament"] = Relationship(back_populates="organizer")