from datetime import datetime

from sqlalchemy import Column
from sqlalchemy import DateTime
from sqlalchemy import ForeignKey
from sqlalchemy import Integer
from sqlalchemy import String
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()


class Task(Base):
    __tablename__ = "tasks"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, index=True)
    title = Column(String, index=True)
    created_at = Column(DateTime, default=datetime.now())
    tag_id = Column(Integer, ForeignKey("tags.id"))
    tags = relationship("Tag", backref="tasks")


class Tag(Base):
    __tablename__ = "tags"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, index=True)
    tag = Column(String, index=True, unique=True)
