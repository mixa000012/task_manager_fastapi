from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

engine = create_async_engine(
    'postgresql+asyncpg://postgres:postgres@127.0.0.1:5432/postgres',
    future=True,
    echo=True,
    execution_options={"isolation_level": "AUTOCOMMIT"},
)

SessionLocal = sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

async def get_db():
    """Dependency for getting async session"""
    try:
        session: AsyncSession = SessionLocal()
        yield session
    finally:
        await session.close()