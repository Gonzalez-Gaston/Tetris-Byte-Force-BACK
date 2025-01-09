from sqlmodel import Relationship, SQLModel, Field
import uuid
from src.models.company_category import CompanyCategory

class Category(SQLModel, table=True):
    __tablename__ = 'categories'
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    name: str = Field(max_length=50, unique=True)
    companies: list["Company"] = Relationship(back_populates="categories", link_model=CompanyCategory)