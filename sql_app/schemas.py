from pydantic import BaseModel
from datetime import datetime
from typing import List, Optional



class Tag_(BaseModel):
    tag: str
    user_id: int

class TagCreate(Tag_):
    pass


class TaskCreate(BaseModel):
    title: str
    user_id: int


class TaskResponse(BaseModel):
    id: int
    user_id: int
    title: str
    created_at: datetime
    tag_id: int | None


