from sqlmodel import Relationship, SQLModel, Field
import uuid
from src.models.company_category import CompanyCategory


class Company(SQLModel, table=True):
    __tablename__ = 'companies'
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    name: str = Field(max_length=50)
    description: str = Field(max_length=500)
    email: str = Field(max_length=50, unique=True, index=True)
    password_hash: str = Field(max_length=100)
    address: str = Field(max_length=100)
    city: str = Field(max_length=50)
    country: str = Field(max_length=50)
    url_web: str | None = Field(max_length=100, default=None)
    url_image: str | None = Field(max_length=100, default=None)
    age_fundation: int = Field()
    categories: list["Category"] = Relationship(back_populates="companies", link_model=CompanyCategory)
