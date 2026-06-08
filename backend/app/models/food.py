from sqlalchemy import Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Restaurant(Base):
    __tablename__ = "restaurants"

    id: Mapped[int] = mapped_column(primary_key=True)
    destination_id: Mapped[int | None] = mapped_column(ForeignKey("destinations.id"), nullable=True, index=True)
    name: Mapped[str] = mapped_column(String(128), index=True)
    lng: Mapped[float] = mapped_column(Float)
    lat: Mapped[float] = mapped_column(Float)
    heat: Mapped[int] = mapped_column(Integer, default=0)
    source: Mapped[str] = mapped_column(String(32), default="seed")
    external_id: Mapped[str | None] = mapped_column(String(128), nullable=True, index=True)
    address: Mapped[str | None] = mapped_column(String(256), nullable=True)
    category: Mapped[str | None] = mapped_column(String(128), nullable=True)

    foods: Mapped[list["Food"]] = relationship(back_populates="restaurant")


class Food(Base):
    __tablename__ = "foods"

    id: Mapped[int] = mapped_column(primary_key=True)
    restaurant_id: Mapped[int] = mapped_column(ForeignKey("restaurants.id"), index=True)
    name: Mapped[str] = mapped_column(String(128), index=True)
    cuisine: Mapped[str] = mapped_column(String(64), index=True)
    price: Mapped[float] = mapped_column(Float)
    rating: Mapped[float] = mapped_column(Float, default=4.5)
    heat: Mapped[int] = mapped_column(Integer, default=0)

    restaurant: Mapped[Restaurant] = relationship(back_populates="foods")
