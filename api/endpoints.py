from typing import Optional

from fastapi import Depends
from fastapi import HTTPException
from fastapi.routing import APIRouter
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api.schemas import Tag_
from api.schemas import TagCreate
from api.schemas import TaskCreate
from api.schemas import TaskResponse
from db.models import Tag
from db.models import Task
from db.session import get_db

task_router = APIRouter()


@task_router.put("/add_tag")
async def add_tag(
    task_id: int, tag_name: str, user_id: int, db: AsyncSession = Depends(get_db)
) -> TaskResponse:
    task = await db.get(Task, task_id)
    tag = await db.execute(
        select(Tag).where(Tag.tag == tag_name, Tag.user_id == user_id)
    )
    tag = tag.scalar()

    task.tags = tag
    db.add(task)
    await db.commit()
    await db.refresh(task)
    return TaskResponse(
        id=task.id,
        user_id=task.user_id,
        title=task.title,
        tag_id=task.tag_id,
        created_at=task.created_at,
    )


@task_router.post("/create_tag")
async def create_tag(item: TagCreate, db: AsyncSession = Depends(get_db)) -> Tag_:
    db_item = Tag(**item.dict())
    db.add(db_item)
    await db.commit()
    await db.refresh(db_item)
    return Tag_(tag=db_item.tag, user_id=db_item.user_id)


@task_router.get("/get_all_tags")
async def get_all_tags(user_id: int, db: AsyncSession = Depends(get_db)) -> list[str]:
    tasks = await db.execute(select(Tag).filter_by(user_id=user_id))
    tasks = tasks.scalars().all()
    text = [i.tag for i in tasks]
    return text


@task_router.get("/is_exist_tag")
async def is_exist_tag(tag: str, db: AsyncSession = Depends(get_db)) -> bool:
    stmt = select(Tag).where(Tag.tag == tag)
    result = await db.execute(stmt)
    return bool(result.scalar())


@task_router.delete("/delete_tag")
async def delete_tag(
    user_id: int, tag: str, db: AsyncSession = Depends(get_db)
) -> dict[str, bool]:
    async with db.begin():
        tag_instance = await db.execute(select(Tag).filter_by(user_id=user_id, tag=tag))
        await db.delete(tag_instance.scalars().first())
        await db.commit()
    return {"ok": True}


@task_router.post("/create")
async def create_task(
    obj: TaskCreate, db: AsyncSession = Depends(get_db)
) -> TaskResponse:
    new_task = Task(
        user_id=obj.user_id,
        title=obj.title,
    )
    db.add(new_task)
    await db.commit()
    await db.refresh(new_task)
    return TaskResponse(
        id=new_task.id,
        user_id=new_task.user_id,
        title=new_task.title,
        created_at=new_task.created_at,
    )


@task_router.delete("/delete_task")
async def delete_task(
    task_id: int, db: AsyncSession = Depends(get_db)
) -> dict[str, bool]:
    async with db.begin():
        task = await db.execute(select(Task).where(Task.id == task_id))
        task = task.scalar()
        await db.delete(task)
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")
        await db.commit()
    return {"ok": True}


# todo айограм оптимизейшен
@task_router.get("/get_all_tasks")
async def get_all_tasks(
    user_id: int, tag: Optional[str] = None, db: AsyncSession = Depends(get_db)
) -> list[TaskResponse]:
    async with db.begin():
        if tag:
            tasks = await db.execute(
                select(Task)
                .join(Task.tags)
                .filter(Task.user_id == user_id)
                .filter(Tag.tag == tag)
            )
            tasks = tasks.scalars().all()
        else:
            tasks = await db.execute(select(Task).filter(Task.user_id == user_id))
            tasks = tasks.scalars().all()
    return [
        TaskResponse(
            id=task.id,
            title=task.title,
            user_id=task.user_id,
            created_at=task.created_at,
        )
        for task in tasks
    ]
