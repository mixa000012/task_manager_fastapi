from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship, declarative_base

Base = declarative_base()


class Task(Base):
    __tablename__ = 'tasks'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, index=True)
    title = Column(String, index=True)
    created_at = Column(DateTime, default=datetime.now())
    tag_id = Column(Integer, ForeignKey('tags.id'))
    tags = relationship('Tag', backref='tasks')


class Tag(Base):
    __tablename__ = 'tags'
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, index=True)
    tag = Column(String, index=True, unique=True)
