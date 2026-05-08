from datetime import datetime

from sqlalchemy import Column, DateTime, Float, Integer, String, Text
from sqlalchemy.orm import declarative_base


# Declarative Base for all SQLAlchemy ORM tables.
Base = declarative_base()


class POI(Base):
    """Points of Interest - 旅游景点"""
    __tablename__ = "pois"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), unique=True, nullable=False)
    type = Column(String(100), nullable=False)  # e.g., 景区、建筑、餐厅
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    floor = Column(Integer, default=1, nullable=False)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class User(Base):
    """用户表"""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(100), unique=True, nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=False)
    interests = Column(String(500), nullable=True)  # 兴趣标签，逗号分隔
    created_at = Column(DateTime, default=datetime.utcnow)


class Facility(Base):
    """设施表"""
    __tablename__ = "facilities"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    type = Column(String(100), nullable=False)  # e.g., 厕所、餐厅、停车场
    poi_id = Column(Integer, nullable=False, index=True)
    location_desc = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class TravelDiary(Base):
    """旅游日记表"""
    __tablename__ = "travel_diaries"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False, index=True)
    title = Column(String(255), nullable=False)
    content = Column(Text, nullable=False)
    poi_id = Column(Integer, nullable=True)  # 关联的 POI
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
