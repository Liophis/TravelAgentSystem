from sqlalchemy import Column, Float, Integer, String
from sqlalchemy.orm import declarative_base


# Declarative Base for all SQLAlchemy ORM tables.
Base = declarative_base()


class POI(Base):
    __tablename__ = "pois"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), unique=True, nullable=False)
    type = Column(String(100), nullable=False)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    floor = Column(Integer, default=1, nullable=False)
