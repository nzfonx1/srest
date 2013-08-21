from sqlalchemy import (
    Column,
    Integer,
    Text,
    Unicode,
    DATETIME,
)

from sqlalchemy.ext.declarative import declarative_base
import sqlalchemy.types as types
from sqlalchemy.orm import (
    scoped_session,
    sessionmaker,
)
from sqlalchemy.types import TypeDecorator, BINARY
from zope.sqlalchemy import ZopeTransactionExtension

from datetime import datetime


DBSession = scoped_session(sessionmaker(extension=ZopeTransactionExtension()))
Base = declarative_base()


# attempt at resolving the UUID issue...
class UUID(types.TypeEngine):

    def get_col_spec(self):
        return "uuid"

    def bind_processor(self, dialect):
        def process(value):
            return value
        return process

    def result_processor(self, dialect):
        def process(value):
            return value
        return process


class MyModel(Base):
    __tablename__ = 'files'
    id = Column(Unicode(255), primary_key=True)
    path = Column(Text)
    size = Column(Integer)
    timestamp = Column(DATETIME)

    def __init__(self, id, path, size):
        self.id = id
        self.path = path
        self.size = size
        self.timestamp = datetime.now()


def initialize_sql(engine):
    DBSession.configure(bind=engine)
    Base.metadata.bind = engine
    Base.metadata.create_all(engine)
