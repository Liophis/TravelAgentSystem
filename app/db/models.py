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
