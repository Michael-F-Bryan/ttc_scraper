from sqlalchemy import Table, Column, Integer, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import String, Column, Integer, ForeignKey, Text



Base = declarative_base()


class Forum(Base):
    __tablename__ = 'forums'

    id = Column(Integer, primary_key=True)
    name = Column(String(64), index=True, unique=True)
    link = Column(String(128), index=True, unique=True)

    child_threads = relationship('Thread')
    
    parent_id = Column(Integer, ForeignKey('forums.id'))
    parent = relationship('Forum')

    def __repr__(self):
        return '<{}: {}>'.format(
                self.__class__.__name__,
                self.name)


class Thread(Base):
    __tablename__ = 'threads'

    id = Column(Integer, primary_key=True)
    name = Column(String(64), index=True)
    link = Column(String(128), index=True, unique=True)

    forum_id = Column(Integer, ForeignKey('forums.id'))
    forums = relationship('Forum', backref='threads')

    def __repr__(self):
        return '<{}: {}>'.format(
                self.__class__.__name__,
                self.name)


class Post(Base):
    __tablename__ = 'posts'

    id = Column(Integer, primary_key=True)
    author = Column(String(20), unique=False)
    created = Column(String(20))
    content = Column(Text)

    thread_id = Column(Integer, ForeignKey('threads.id'))
    threads = relationship('Thread', backref='posts')

    def __repr__(self):
        return '<{}: author:{}, created: {}>'.format(
                self.__class__.__name__,
                self.author,
                self.created)


class Url(Base):
    __tablename__ = 'urls'
    id = Column(Integer, primary_key=True)
    link = Column(String(128), index=True, unique=True)

    def __repr__(self):
        return '<{}: {}>'.format(
                self.__class__.__name__,
                self.link)


class Attachment(Base):
    __tablename__ = 'attachments'

    id = Column(Integer, primary_key=True)
    link = Column(String(128), index=True)
    name = Column(String(64), index=True)

    post_id = Column(Integer, ForeignKey('posts.id'))
    posts = relationship('Post', backref='attachments')

    def __repr__(self):
        return '<{}: {}>'.format(
                self.__class__.__name__,
                self.name)
