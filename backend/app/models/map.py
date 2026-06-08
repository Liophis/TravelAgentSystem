from sqlalchemy import Float, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class MapNode(Base):
    __tablename__ = "map_nodes"

    id: Mapped[int] = mapped_column(primary_key=True)
    external_id: Mapped[str] = mapped_column(String(128), unique=True, index=True)
    name: Mapped[str | None] = mapped_column(String(128), nullable=True)
    lng: Mapped[float] = mapped_column(Float)
    lat: Mapped[float] = mapped_column(Float)


class MapEdge(Base):
    __tablename__ = "map_edges"

    id: Mapped[int] = mapped_column(primary_key=True)
    from_node_id: Mapped[int] = mapped_column(ForeignKey("map_nodes.id"), index=True)
    to_node_id: Mapped[int] = mapped_column(ForeignKey("map_nodes.id"), index=True)
    distance: Mapped[float] = mapped_column(Float)
    walk_time: Mapped[float] = mapped_column(Float)
    congestion: Mapped[float] = mapped_column(Float, default=1.0)
    walk_speed: Mapped[float] = mapped_column(Float, default=1.2)
    bike_speed: Mapped[float] = mapped_column(Float, default=3.5)
    electric_cart_speed: Mapped[float] = mapped_column(Float, default=4.5)
    allowed_modes: Mapped[list[str]] = mapped_column(JSON, default=lambda: ["walk"])
    geometry: Mapped[list[list[float]]] = mapped_column(JSON)


class Building(Base):
    __tablename__ = "buildings"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(128), index=True)
    category: Mapped[str] = mapped_column(String(64), default="building")
    polygon: Mapped[list[list[float]]] = mapped_column(JSON)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)


class FacilityCategory(Base):
    __tablename__ = "facility_categories"

    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(64))

    facilities: Mapped[list["Facility"]] = relationship(back_populates="category")


class Facility(Base):
    __tablename__ = "facilities"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(128), index=True)
    category_id: Mapped[int] = mapped_column(ForeignKey("facility_categories.id"), index=True)
    nearest_node_id: Mapped[int | None] = mapped_column(ForeignKey("map_nodes.id"), nullable=True)
    lng: Mapped[float] = mapped_column(Float)
    lat: Mapped[float] = mapped_column(Float)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    category: Mapped[FacilityCategory] = relationship(back_populates="facilities")
