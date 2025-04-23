from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, Date, UniqueConstraint
from sqlalchemy.orm import relationship

from datetime import datetime

from app.db.session import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    first_name = Column(String(64), nullable=False)
    last_name = Column(String(64), nullable=False)
    email = Column(String(128), unique=True, nullable=False)
    password = Column(String(64), nullable=True)
    is_active = Column(Boolean, default=False)
    verification_code = Column(Integer, nullable=True)
    trycount = Column(Integer, default=0, nullable=True)
    image = Column(String(256), default="profile_images/profile_default.png")


class Token(Base):
    __tablename__ = "user_token"
    __table_args__ = (UniqueConstraint(
        'ip_address', 'user_agent', name='_unique_device'),)

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"))
    user = relationship("User")
    created = Column(Date, default=datetime.now())
    token = Column(String(40), unique=True, index=True)
    ip_address = Column(String)
    user_agent = Column(String)
    location = Column(String, nullable=True)
    proxy = Column(Boolean)
