from sqlmodel import SQLModel, Field
import uuid

class Organizer(SQLModel, table=True):
    __tablename__ = 'organizers'
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    name: str = Field(max_length=100)
    description: str = Field()
    user_id: uuid.UUID = Field(foreign_key='users.id', index=True)
