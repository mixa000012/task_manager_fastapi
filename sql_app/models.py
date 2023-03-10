from datetime import datetime
from sqlalchemy import Boolean, Column, Integer, String, DateTime, Table, ForeignKey
from sqlalchemy.orm import relationship, declarative_base
from sqlalchemy.orm import backref

Base = declarative_base()

# task_tag = Table('task_tag', Base.metadata,
#                  Column('task_id',Integer, ForeignKey('tasks.id')),
#                  Column('tag_id',Integer, ForeignKey('tags.id'))
#                  )
#
#
# class Task(Base):
#     __tablename__ = 'tasks'
#     id = Column(Integer, primary_key=True)
#     user_id = Column(Integer, index=True)
#     title = Column(String, index=True)
#     created_at = Column(DateTime, default=datetime.now())
#     tags = relationship('Tag', secondary="task_tag", backref=backref("tags"), cascade='all', single_parent=True)
#     # tags = relationship('Tag', secondary="task_tag", backref='tags')
#
#
# class Tag(Base):
#     __tablename__ = 'tags'
#     id = Column(Integer, primary_key=True, index=True)
#     user_id = Column(Integer, index=True)
#     tasks = relationship("Task", secondary="task_tag", backref=backref("tasks"), cascade='all')
#     tag = Column(String, index=True, unique=True)


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