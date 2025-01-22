# import pytest
# from fastapi.testclient import TestClient
# from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
# from sqlalchemy.orm import sessionmaker
# from src.database.db import db
# from src.__init__ import app

# DATABASE_URL = "sqlite+aiosqlite:///./test.db"

# engine = create_async_engine(DATABASE_URL, echo=True)
# TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine, class_=AsyncSession)

# @pytest.fixture(scope="module")
# def client():
#     with TestClient(app) as c:
#         yield c

# @pytest.fixture(scope="module")
# async def session():
#     async with engine.begin() as conn:
#         await conn.run_sync(db.create_all)
#     async with TestingSessionLocal() as session:
#         yield session
#     async with engine.begin() as conn:
#         await conn.run_sync(db.drop_all)
