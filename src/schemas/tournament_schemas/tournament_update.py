from datetime import datetime, timezone
from pydantic import BaseModel, field_validator, model_validator


class TournamentUpdate(BaseModel):
    name: str
    description: str
    start: datetime
    end: datetime

    @field_validator('description')
    def description_validator(cls, description):
        if len(description) < 20:
           raise ValueError('La descripción debe de contener al menos 20 carácteres')
        return description

    @model_validator(mode='before')
    def validate_dates(cls, values):
        now = datetime.now(timezone.utc) 

        start = values.get('start')
        end = values.get('end')

        if isinstance(start, str):
            start = datetime.fromisoformat(start.replace("Z", "+00:00")) 
        if isinstance(end, str):
            end = datetime.fromisoformat(end.replace("Z", "+00:00"))

        if start is None or end is None:
            raise ValueError("Las fechas de inicio y fin son obligatorias.")
        
        if start.date() <= now.date():
            raise ValueError("La fecha de inicio no puede ser hoy o anterior.")
        if end <= start:
            raise ValueError("La fecha de fin debe ser posterior a la fecha de inicio.")
        
        values['start'] = start
        values['end'] = end

        return values
    