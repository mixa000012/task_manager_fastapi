from datetime import datetime
from sqlalchemy import Boolean, Column, Integer, String, DateTime, Table, ForeignKey
from sqlalchemy.orm import relationship, declarative_base

Base = declarative_base()

task_tag = Table('task_tag', Base.metadata,
                 Column('task_id', ForeignKey('tasks.user_id'), primary_key=True),
                 Column('tag_id', ForeignKey('tags.id'), primary_key=True,)
                 )


class Task(Base):
    __tablename__ = 'tasks'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, index=True)
    title = Column(String, index=True)
    description = Column(String, nullable=True)
    is_done = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.now())
    tags = relationship('Tag', secondary="task_tag", backref='tags')


class Tag(Base):
    __tablename__ = 'tags'

    tasks = relationship("Task", secondary="task_tag", backref='tasks', overlaps="tags,tags")
    id = Column(Integer, primary_key=True, index=True)
    tag = Column(String, index=True)
