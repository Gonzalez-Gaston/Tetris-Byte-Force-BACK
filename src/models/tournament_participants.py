from datetime import datetime
from typing import Optional
from sqlmodel import SQLModel, Field, Relationship
import uuid

class TournamentParticipants(SQLModel, table=True):
    __tablename__ = 'tournament_participants'
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    participant_id: str = Field(foreign_key='participants.id', index=True)
    tournament_id: str = Field(foreign_key='tournaments.id')
    final_position: int | None = Field()
    points: int = Field(default=0)
    confirm: bool = Field(default=False)
    participant: Optional["Participant"] = Relationship(back_populates="tournaments")
    tournament: Optional["Tournament"] = Relationship(back_populates="participants")
    win: int = Field(default=0)
    lose: int = Field(default=0)

    @property
    def calculate_value_point(self) -> float:
        if not self.end:
            return self.points
        months_diff = (datetime.now() - self.end).days // 30
        if months_diff > 12:
            return 0
        elif months_diff > 9:
            return self.points * 0.2
        elif months_diff > 6:
            return self.points * 0.5
        elif months_diff > 3:
            return self.points * 0.7
        else:
            return self.points
