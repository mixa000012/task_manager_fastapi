from typing import Optional

from sqlalchemy.orm import Session
from fastapi.routing import APIRouter
from fastapi import Depends, HTTPException
from sql_app.session import get_db
from sql_app.models import Task, Tag
from sql_app.schemas import TaskResponse, TagCreate, TaskCreate

task_router = APIRouter()


@task_router.put("/add_tag")
def add_tag(task_id: int, tag_name: str, user_id:int, db: Session = Depends(get_db)):
    task = db.query(Task).get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    # tag = db.query(Tag).filter(Tag.tag == tag_name).first()
    tag = db.query(Tag).filter_by(tag=tag_name,user_id=user_id).one()

    task.tags = tag
    db.add(task)
    db.commit()
    db.refresh(task)
    return task


@task_router.post("/create_tag")
def create_tag(item: TagCreate, user_id: int, db: Session = Depends(get_db)):
    db_item = Tag(**item.dict(), user_id=user_id)
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    return db_item


@task_router.get("/get_all_tags")
def get_all_tags(user_id:int, db: Session = Depends(get_db)):
    tasks = db.query(Tag).filter_by(user_id=user_id).all()
    text = [i.tag for i in tasks]
    return text


@task_router.get("/is_exist_tag")
def is_exist_tag(tag: str, db: Session = Depends(get_db)):
    if db.query(Tag).filter(Tag.tag == tag).count() > 0:
        return True
    return False


@task_router.delete("/delete_tag")
def delete_tag(tag_id: int, db: Session = Depends(get_db)):
    tag = db.query(Tag).filter_by(id=tag_id).delete()
    if not tag:
        raise HTTPException(status_code=404, detail="Tag not found")
    db.commit()
    return {"ok": True}


@task_router.post("/create", response_model=TaskResponse)
def create_task(obj: TaskCreate, db: Session = Depends(get_db)) -> TaskResponse:
    new_task = Task(
        user_id=obj.user_id,
        title=obj.title,
    )
    db.add(new_task)
    db.commit()
    db.refresh(new_task)
    return TaskResponse(
        id=new_task.id,
        user_id=new_task.user_id,
        title=new_task.title,
        created_at=new_task.created_at
    )


@task_router.delete("/delete_task")
def delete_task(task_id: int, db: Session = Depends(get_db)):
    task = db.query(Task).filter_by(id=task_id).first()
    db.delete(task)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    db.commit()
    return {"ok": True}

@task_router.get("/get_all_tasks")
def get_all_tasks(user_id: int, tag: Optional[str] = None, db: Session = Depends(get_db)):
    if tag:
        tasks = db.query(Task).join(Task.tags).filter(Task.user_id == user_id).filter(Tag.tag == tag).all()
    else:
        tasks = db.query(Task).filter(Task.user_id == user_id).all()
    return tasks