from sqlalchemy import Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Destination(Base):
    __tablename__ = "destinations"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(128), index=True)
    category: Mapped[str] = mapped_column(String(64), index=True)
    description: Mapped[str] = mapped_column(Text)
    lng: Mapped[float] = mapped_column(Float)
    lat: Mapped[float] = mapped_column(Float)
    rating: Mapped[float] = mapped_column(Float, default=4.5)
    popularity: Mapped[int] = mapped_column(Integer, default=0)

    tags: Mapped[list["DestinationTag"]] = relationship(back_populates="destination")


class DestinationTag(Base):
    __tablename__ = "destination_tags"

    id: Mapped[int] = mapped_column(primary_key=True)
    destination_id: Mapped[int] = mapped_column(ForeignKey("destinations.id"), index=True)
    tag: Mapped[str] = mapped_column(String(64), index=True)

    destination: Mapped[Destination] = relationship(back_populates="tags")
