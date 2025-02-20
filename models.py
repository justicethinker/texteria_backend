from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.orm import relationship, declarative_base
from database import Base
from datetime import datetime

Base = declarative_base()

class RefreshToken(Base):
    __tablename__ = "refresh_tokens"

    id = Column(Integer, primary_key=True, index=True)
    token = Column(String, unique=True, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="refresh_tokens")

class MalariaReport(Base):
    __tablename__ = "malaria_reports"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)  # Link to users
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    cases_reported = Column(Integer, nullable=False)  # Number of malaria cases
    created_at = Column(DateTime, default=datetime.utcnow)  # Timestamp

    user = relationship("User", back_populates="malaria_reports")

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False)
    password = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    latitude = Column(Float, nullable=True)  
    longitude = Column(Float, nullable=True)

    refresh_tokens = relationship("RefreshToken", back_populates="user", cascade="all, delete-orphan")
    malaria_reports = relationship("MalariaReport", back_populates="user", cascade="all, delete-orphan")

   


