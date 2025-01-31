from datetime import date, datetime, timezone
import uuid
from typing import List

# Importando los modelos
from schemas.user_schema.user_full import UserFull
from src.models.tournament_participants import TournamentParticipants
from src.models.participant_model import Participant
from src.models.user_model import User, RoleUser

# Datos simulados de participantes
mock_participants: List[Participant] = [
    Participant(
        id=str(uuid.uuid4()),
        username="player_one",
        first_name="John",
        last_name="Doe",
        date_of_birth=date(1995, 5, 24),
        url_image="https://via.placeholder.com/150",
        user_id=str(uuid.uuid4()),
        tournaments=[]  # Se puede agregar instancias de TournamentParticipants si es necesario
    ),
    Participant(
        id=str(uuid.uuid4()),
        username="gamer_23",
        first_name="Alice",
        last_name="Smith",
        date_of_birth=date(1998, 11, 3),
        url_image="https://via.placeholder.com/150",
        user_id=str(uuid.uuid4()),
        tournaments=[]
    ),
    Participant(
        id=str(uuid.uuid4()),
        username="champ_master",
        first_name="Bob",
        last_name="Johnson",
        date_of_birth=date(1992, 7, 15),
        url_image="https://via.placeholder.com/150",
        user_id=str(uuid.uuid4()),
        tournaments=[]
    )
]

# Datos simulados de usuarios
mock_users: List[User] = [
    User(
        id=str(uuid.uuid4()),
        username="testuser1",
        email="testuser1@example.com",
        password_hash="hashed_password_1",
        role=RoleUser.PARTICIPANT,
        is_active=True,
        token=str(uuid.uuid4()),
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    ),
    User(
        id=str(uuid.uuid4()),
        username="testuser2",
        email="testuser2@example.com",
        password_hash="hashed_password_2",
        role=RoleUser.ORGANIZER,
        is_active=True,
        token=str(uuid.uuid4()),
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )
]

# Mock de un usuario con un participante asociado
mock_user_full = UserFull(
    id=1,
    username="testuser1",
    email="testuser1@example.com",
    full=FullParticipant(
        participant=mock_participants[0],  # Usamos el primer participante como ejemplo
        organizer=None  # Si no necesitas un organizador, lo dejas como None
    )
)

# Mock para exportar
mock_data = {
    "participants": mock_participants,
    "users": mock_users,
    "user_full": mock_user_full
}
