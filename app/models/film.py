from sqlalchemy import Column, Integer, String, Date, ForeignKey
from sqlalchemy.orm import relationship
from db.session import Base
from datetime import datetime


class Film(Base):
    __tablename__ = "Film"

    id = Column(Integer, primary_key=True)
    name = Column(String)
    rate = Column(Integer, default=10)
    budget = Column(Integer)
    release_date = Column(Date, default=datetime.now())
    image = Column(String, nullable=True)
    film = Column(String, nullable=True)
    genres = relationship("Genre", secondary='film_genre')


class Genre(Base):
    __tablename__ = "Genre"

    id = Column(Integer, primary_key=True)
    name = Column(String(64))


class Film_Genre(Base):
    __tablename__ = 'film_genre'
    film_id = Column(Integer, ForeignKey('Film.id'))
    genre_id = Column(Integer, ForeignKey('Genre.id'))
