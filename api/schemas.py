from pydantic import BaseModel
from datetime import datetime


class Tag_(BaseModel):
    tag: str
    user_id: int


class TagCreate(Tag_):
    pass


class TaskCreate(BaseModel):
    title: str
    user_id: int


class TaskResponse(TaskCreate):
    id: int
    created_at: datetime
    tag_id: int | None
