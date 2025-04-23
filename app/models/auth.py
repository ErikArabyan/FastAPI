from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, Date
from sqlalchemy.orm import relationship
from app.db.session import Base
from datetime import datetime


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    first_name = Column(String(64))
    last_name = Column(String(64))
    email = Column(String(128), unique=True)
    password = Column(String(64))
    is_active = Column(Boolean, default=False)
    verification_code = Column(Integer, nullable=True)
    trycount = Column(Integer, default=0)

class Token(Base):
    __tablename__ = "user_token"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"))
    created = Column(Date, default=datetime.now())
    token = Column(String(40), unique=True, index=True)
    user = relationship("User")
