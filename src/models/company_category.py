import uuid
from sqlmodel import Field, SQLModel

class CompanyCategory(SQLModel, table=True):
    __tablename__ = 'company_category_link'
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    category_id: uuid.UUID = Field(default=None, foreign_key="categories.id")
    company_id: uuid.UUID = Field(default=None, foreign_key="companies.id")
