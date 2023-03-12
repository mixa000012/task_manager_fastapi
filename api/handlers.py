from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi.routing import APIRouter
from fastapi import Depends, HTTPException

from sql_app.session import get_db
from sql_app.models import Task, Tag
from sql_app.schemas import TagCreate, TaskCreate, TaskResponse

task_router = APIRouter()


@task_router.put("/add_tag")
async def add_tag(task_id: int, tag_name: str, user_id: int, db: AsyncSession = Depends(get_db)):
    task = await db.get(Task, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    # tag = db.query(Tag).filter(Tag.tag == tag_name).first()
    tag = await db.execute(select(Tag).where(Tag.tag == tag_name, Tag.user_id == user_id))
    tag = tag.scalar()

    task.tags = tag
    db.add(task)
    await db.commit()
    await db.refresh(task)
    return task


@task_router.post("/create_tag")
async def create_tag(item: TagCreate, user_id: int, db: AsyncSession = Depends(get_db)):
    db_item = Tag(**item.dict(), user_id=user_id)
    db.add(db_item)
    await db.commit()
    await db.refresh(db_item)
    return db_item


@task_router.get("/get_all_tags")
async def get_all_tags(user_id: int, db: AsyncSession = Depends(get_db)):
    tasks = await db.execute(select(Tag).filter_by(user_id=user_id))
    tasks = tasks.scalars().all()
    text = [i.tag for i in tasks]
    return text


@task_router.get("/is_exist_tag")
async def is_exist_tag(tag: str, db: AsyncSession = Depends(get_db)):
    stmt = select(Tag).where(Tag.tag == tag)
    result = await db.execute(stmt)
    return bool(result.scalar())


@task_router.delete("/delete_tag")
async def delete_tag(user_id: int, tag: str, db: AsyncSession = Depends(get_db)):
    async with db.begin():
        tag_instance = await db.execute(select(Tag).filter_by(user_id=user_id, tag=tag))
        await db.delete(tag_instance.scalars().first())
        await db.commit()
    return {"ok": True}


@task_router.post("/create")
async def create_task(obj: TaskCreate, db: AsyncSession = Depends(get_db)) -> TaskResponse:
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
        created_at=new_task.created_at
    )


@task_router.delete("/delete_task")
async def delete_task(task_id: int, db: AsyncSession = Depends(get_db)):
    async with db.begin():
        task = await db.execute(
            select(Task).where(Task.id == task_id)
        )
        task = task.scalar()
        await db.delete(task)
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")
        await db.commit()
    return {"ok": True}


@task_router.get("/get_all_tasks")
async def get_all_tasks(user_id: int, tag: Optional[str] = None, db: AsyncSession = Depends(get_db)):
    async with db.begin():
        if tag:
            tasks = await db.execute(
                select(Task).join(Task.tags).filter(Task.user_id == user_id).filter(Tag.tag == tag)
            )
            tasks = tasks.scalars().all()
        else:
            tasks = await db.execute(
                select(Task).filter(Task.user_id == user_id)
            )
            tasks = tasks.scalars().all()
    return tasks
