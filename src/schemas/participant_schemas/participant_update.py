from datetime import date
from pydantic import BaseModel, field_validator


class ParticipantUpdate(BaseModel):
    first_name: str
    last_name: str
    date_of_birth: date

    @field_validator('date_of_birth')
    def date_of_birth_validator(cls, date_of_birth):
        today = date.today()
        age = today.year - date_of_birth.year - ((today.month, today.day) < (date_of_birth.month, date_of_birth.day))
        if age < 18:
            raise ValueError('El usuario debe tener al menos 18 años')
        return date_of_birth