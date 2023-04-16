import asyncio
import os
from typing import Any
from typing import Generator

import asyncpg
import pytest
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.orm import sessionmaker
from starlette.testclient import TestClient
from sqlalchemy import text
from sqlalchemy import delete
from sql_app.session import get_db
from main import app
from sql_app.models import Task, Tag

CLEAN_TABLES = [
    "tasks"
]
DB_URL = 'postgresql+asyncpg://postgres:postgres@127.0.0.1:5433/postgres'


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session", autouse=True)
async def run_migrations():
    os.system("alembic init migrations")
    os.system('alembic revision --autogenerate -m "test running migrations"')
    os.system("alembic upgrade heads")


@pytest.fixture(scope="session")
async def async_session_test():
    engine = create_async_engine(DB_URL, future=True, echo=True)
    async_session = sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
    yield async_session

    await engine.dispose()


@pytest.fixture(scope="function", autouse=True)
async def clean_tables(async_session_test):
    """Clean data in all tables before running test function"""
    async with async_session_test() as session:
        try:
            async with session.begin():
                await session.execute(delete(Task))
                await session.execute(delete(Tag))

            await session.commit()
        except Exception as e:
            await session.rollback()
            raise e

async def _get_test_db():
    try:
        # create async engine for interaction with database
        test_engine = create_async_engine(
            DB_URL, future=True, echo=True
        )

        # create session for the interaction with database
        test_async_session = sessionmaker(
            test_engine, expire_on_commit=False, class_=AsyncSession
        )
        yield test_async_session()
    finally:
        pass


@pytest.fixture(scope="function")
async def client() -> Generator[TestClient, Any, None]:
    """
    Create a new FastAPI TestClient that uses the `db_session` fixture to override
    the `get_db` dependency that is injected into routes.
    """

    app.dependency_overrides[get_db] = _get_test_db
    with TestClient(app) as client:
        yield client


@pytest.fixture(scope="session")
async def asyncpg_pool():
    pool = await asyncpg.create_pool(
        "".join(DB_URL.split("+asyncpg"))
    )
    yield pool
    pool.close()


@pytest.fixture
async def get_task_from_database(asyncpg_pool):
    async def get_task_from_database_by_id(user_id: int):
        async with asyncpg_pool.acquire() as connection:
            return await connection.fetch(
                """SELECT * FROM tasks WHERE user_id = $1;""", user_id
            )

    return get_task_from_database_by_id


@pytest.fixture
async def create_task_in_database(asyncpg_pool):
    async def create_user_in_database(
            id: int,
            user_id: str,
            task: str,
    ):
        async with asyncpg_pool.acquire() as connection:
            return await connection.execute(
                """INSERT INTO tasks VALUES ($1, $2, $3, $4)""",
                id,
                user_id,
                task,
                datetime.now()
            )

    return create_user_in_database
