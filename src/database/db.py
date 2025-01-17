# #MYSQL

# from sqlmodel import SQLModel
# from sqlalchemy.ext.asyncio import create_async_engine
# from sqlmodel.ext.asyncio.session import AsyncSession
# from sqlalchemy.orm import sessionmaker
# from decouple import config
# import logging
# import aiomysql

# DATABASE_URL="mysql+aiomysql://root:YeorsGTTacntTqCoYlVeMnwiwOUMiNTg@junction.proxy.rlwy.net:25545/railway"

# class DataBase:
#     def __init__(self):
#         self.__host = config('DB_HOST')
#         self.__user = config('DB_USER')
#         self.__passwd = config('DB_PASSWORD')
#         self.__db = config('DB_NAME')
#         self.__port = int(config('DB_PORT'))
#         # self.database_url = f"mysql+aiomysql://{self.__user}:{self.__passwd}@{self.__host}:{self.__port}/{self.__db}"
#         self.database_url = DATABASE_URL
#         self.engine = create_async_engine(self.database_url, echo=True)

#     async def create_database_if_not_exists(self):
#         temp_connection = await aiomysql.connect(
#             host=self.__host,
#             user=self.__user,
#             password=self.__passwd,
#             port=self.__port
#         )
#         try:
#             cursor = await temp_connection.cursor()
#             await cursor.execute(f"CREATE DATABASE IF NOT EXISTS {self.__db}")
#             logging.info('Creando base de datos...')
#             await temp_connection.commit()
#             logging.info('Base de datos creada')
#         except Exception as e:
#             logging.error(f'Error al crear la base de datos: {e}')
#             raise e
#         finally:
#             await cursor.close()
#             temp_connection.close()

#     async def connect(self):
#         try:
#             logging.info('Conectando a la base de datos...')
#             async with self.engine.connect() as conn:
#                 await conn.run_sync(lambda conn: None)  # Test connection
#             logging.info('Conexión exitosa')
#         except Exception as e:
#             logging.error(f'Error al conectar a la base de datos: {e}')
#             raise e

#     async def close(self):
#         logging.info('Cerrando conexion a la base de datos...')
#         await self.engine.dispose()
#         logging.info('Conexión cerrada')

#     def is_closed(self):
#         return not self.engine.pool.checkedout()

#     async def create_tables(self):
#         try:
#             logging.info('Validando tablas...')
#             from src.models.refresh_token import HistorialRefreshToken
#             from src.models.organizer_model import Organizer
#             from src.models.participant_model import Participant
#             from src.models.tournaments import Tournament
#             from src.models.tournament_participants import TournamentParticipants

#             async with self.engine.begin() as conn:
#                 await conn.run_sync(SQLModel.metadata.create_all)
#             logging.info('Tablas validadas')
#         except Exception as e:
#             logging.error(f'Error al validar las tablas: {e}')
#             raise e

#     async def get_session(self):
#         async_session = sessionmaker(
#             bind=self.engine,
#             class_=AsyncSession,
#             expire_on_commit=False
#         )

#         async with async_session() as session:
#             yield session


# db = DataBase()



# SQLITE


from sqlmodel import SQLModel
from sqlalchemy.ext.asyncio import create_async_engine
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlalchemy.orm import sessionmaker
from decouple import config
import logging
import aiosqlite

class DataBase:
    def __init__(self):
        # self.database_url = f"sqlite+aiosqlite:///./{config('DB_NAME')}.db"
        self.database_url = f"sqlite+aiosqlite:///./tetris.db"
        self.engine = create_async_engine(self.database_url, echo=True)

    async def connect(self):
        try:
            logging.info('Conectando a la base de datos...')
            await self.engine.connect()
            logging.info('Conexión exitosa')
        except Exception as e:
            logging.error(f'Error al conectar a la base de datos: {e}')
            raise e

    async def close(self):
        logging.info('Cerrando conexion a la base de datos...')
        await self.engine.dispose()
        logging.info('Conexión cerrada')

    def is_closed(self):
        return self.engine.pool is None or self.engine.pool.status() == 'closed'

    async def create_tables(self):
        try:
            logging.info('Validando tablas...')
            from src.models.refresh_token import HistorialRefreshToken
            from src.models.organizer_model import Organizer
            from src.models.participant_model import Participant
            from src.models.tournaments import Tournament
            from src.models.tournament_participants import TournamentParticipants

            async with self.engine.begin() as conn:
                await conn.run_sync(SQLModel.metadata.create_all)
            logging.info('Tablas validadas')
        except Exception as e:
            logging.error(f'Error al validar las tablas: {e}')
            raise e

    async def get_session(self):
        async_session = sessionmaker(
            bind=self.engine,
            class_=AsyncSession,
            expire_on_commit=False
        )

        async with async_session() as session:
            yield session


db = DataBase()