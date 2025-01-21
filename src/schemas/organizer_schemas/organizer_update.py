from datetime import date
from pydantic import BaseModel, field_validator


class OrganizerUpdate(BaseModel):
    description: str

    @field_validator('description')
    def description_validator(cls, description):
        if len(description) < 20 or len(description) > 200:
            raise ValueError('La description debe contener entre 20 y 200 caracteres')
        return description