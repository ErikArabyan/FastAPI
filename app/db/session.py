from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import declarative_base
from sqlalchemy.ext.asyncio import async_sessionmaker
import asyncio


Base = declarative_base()

SQLALCHEMY_DATABASE_URL = "postgresql+asyncpg://postgres:Hayk1234@localhost/FastAPINetflix"

engine = create_async_engine(SQLALCHEMY_DATABASE_URL)

SessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        asyncio.create_task(delayed_close(db))


async def delayed_close(db):
    await asyncio.sleep(5)
    await db.close()


# async def get_db():
#     async with SessionLocal() as db:
#         yield db
