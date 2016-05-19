from sqlalchemy import Table, Column, Integer, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import String, Column, Integer, ForeignKey



Base = declarative_base()


class Forum(Base):
    __tablename__ = 'forums'

    id = Column(Integer, primary_key=True)
    name = Column(String(64), index=True, unique=True)

    children = relationship('Thread')

class Thread(Base):
    __tablename__ = 'threads'

    id = Column(Integer, primary_key=True)
    name = Column(String(64), index=True, unique=True)

    forum_id = Column(Integer, ForeignKey('forums.id'))
    forums = relationship('Forum', backref='threads')

class Url(Base):
    __tablename__ = 'urls'
    id = Column(Integer, primary_key=True)
    link = Column(String(128), index=True, unique=True)


