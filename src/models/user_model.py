from datetime import date, datetime, timezone
from sqlmodel import SQLModel, Field
import uuid

class User(SQLModel, table=True):
    __tablename__ = 'users'
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    username: str = Field(max_length=50, unique=True)
    email: str = Field(max_length=50, unique=True, index=True)
    password_hash: str = Field(max_length=100)
    first_name: str = Field(max_length=50)
    last_name: str = Field(max_length=50)
    date_of_birth: date = Field()
    url_image: str | None = Field(default=None)
    is_active: bool = Field(default=False)
    token: uuid.UUID | None = Field(default_factory=lambda: uuid.uuid4())
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))