from sqlalchemy.orm import Session
from fastapi.routing import APIRouter
from fastapi import Depends, HTTPException
from sql_app.session import get_db
from sql_app.models import Task, Tag, task_tag
from sql_app.schemas import TaskResponse, TagCreate, TaskCreate

task_router = APIRouter()


@task_router.put("/add_tag")
def add_tag(task_id: int, tag_name: str, db: Session = Depends(get_db)):
    task = db.query(Task).get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    tag = db.query(Tag).filter(Tag.tag == tag_name).first()
    task.tags.append(tag)
    db.add(task)
    db.commit()
    db.refresh(task)
    return task


@task_router.post("/create_tag")
def create_tag(item: TagCreate, db: Session = Depends(get_db)):
    db_item = Tag(**item.dict())
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    return db_item


@task_router.get("/get_all_tags")
def get_all_tags(db: Session = Depends(get_db)):
    tasks = db.query(Tag).all()
    return tasks


@task_router.post("/create", response_model=TaskResponse)
def create_task(obj: TaskCreate, db: Session = Depends(get_db)) -> TaskResponse:
    new_task = Task(
        user_id=obj.user_id,
        title=obj.title,
        description=obj.description
    )
    db.add(new_task)
    db.commit()
    db.refresh(new_task)
    return TaskResponse(
        user_id=new_task.user_id,
        title=new_task.title,
        description=new_task.description,
        is_done=new_task.is_done,
        created_at=new_task.created_at
    )


@task_router.delete("/delete_task")
def delete_task(task_id: int, db: Session = Depends(get_db)):
    task = db.query(Task).filter_by(id=task_id).delete()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    db.commit()
    return {"ok": True}


@task_router.get("/get_all_tasks")
def get_all_tasks(user_id: int, db: Session = Depends(get_db)):
    tasks = db.query(Task).filter(Task.user_id == user_id).all()
    return tasks


@task_router.delete("/delete_tag")
def delete_tag(tag_id: int, db: Session = Depends(get_db)):
    tag = db.query(Tag).filter_by(id=tag_id).delete()
    if not tag:
        raise HTTPException(status_code=404, detail="Tag not found")
    db.commit()
    return {"ok": True}
