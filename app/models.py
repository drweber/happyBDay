from sqlalchemy import Column, Integer, String, Date, Table
from sqlalchemy.orm import mapper
from app import database


class User(object):

    query = database.db_session.query_property()

    username = Column(String, primary_key=True, unique=True)
    birth_date = Column(Date)

    def __init__(self, username=None, birth_date=None):
        self.name = username
        self.birth_date = birth_date

users = Table('users', database.metadata,
    Column('username', String(45), nullable=False, primary_key=True,),
    Column('birth_date', Date, nullable=False)
)
mapper(User, users)
