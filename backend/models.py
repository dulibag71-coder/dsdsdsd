from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    created_at = Column(DateTime, server_default=func.now())

    swings = relationship("Swing", back_populates="user", cascade="all, delete-orphan")

class Swing(Base):
    __tablename__ = "swings"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    video_path = Column(String(500), nullable=False)
    created_at = Column(DateTime, server_default=func.now())

    user = relationship("User", back_populates="swings")
    poses = relationship("Pose", back_populates="swing", cascade="all, delete-orphan")
    analysis = relationship("Analysis", back_populates="swing", cascade="all, delete-orphan")
    lessons = relationship("Lesson", back_populates="swing", cascade="all, delete-orphan")

class Pose(Base):
    __tablename__ = "poses"
    id = Column(Integer, primary_key=True, index=True)
    swing_id = Column(Integer, ForeignKey("swings.id"))
    frame_index = Column(Integer, nullable=False)
    keypoints_json = Column(Text, nullable=False)

    swing = relationship("Swing", back_populates="poses")

class Analysis(Base):
    __tablename__ = "analysis"
    id = Column(Integer, primary_key=True, index=True)
    swing_id = Column(Integer, ForeignKey("swings.id"))
    result_json = Column(Text, nullable=False)

    swing = relationship("Swing", back_populates="analysis")

class Lesson(Base):
    __tablename__ = "lessons"
    id = Column(Integer, primary_key=True, index=True)
    swing_id = Column(Integer, ForeignKey("swings.id"))
    lesson_text = Column(Text, nullable=False)

    swing = relationship("Swing", back_populates="lessons")
