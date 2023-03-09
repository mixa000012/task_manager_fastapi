from pydantic import BaseModel
from datetime import datetime
from typing import List, Optional



class Tag(BaseModel):
    tag: str

class TagCreate(Tag):
    pass


class TaskCreate(BaseModel):
    title: str
    description: str | None = None
    user_id: int


class TaskResponse(BaseModel):
    user_id: int
    title: str
    description: Optional[str] | None = None
    is_done: bool
    created_at: datetime
    tags: List[Tag] | None = None
