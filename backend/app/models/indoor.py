from sqlalchemy import Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class IndoorNode(Base):
    __tablename__ = "indoor_nodes"

    id: Mapped[int] = mapped_column(primary_key=True)
    building_name: Mapped[str] = mapped_column(String(128), index=True)
    floor: Mapped[int] = mapped_column(Integer, index=True)
    name: Mapped[str] = mapped_column(String(128), index=True)
    node_type: Mapped[str] = mapped_column(String(64), default="room")
    x: Mapped[float] = mapped_column(Float, default=0)
    y: Mapped[float] = mapped_column(Float, default=0)


class IndoorEdge(Base):
    __tablename__ = "indoor_edges"

    id: Mapped[int] = mapped_column(primary_key=True)
    building_name: Mapped[str] = mapped_column(String(128), index=True)
    from_node_id: Mapped[int] = mapped_column(ForeignKey("indoor_nodes.id"), index=True)
    to_node_id: Mapped[int] = mapped_column(ForeignKey("indoor_nodes.id"), index=True)
    distance: Mapped[float] = mapped_column(Float)
    duration: Mapped[float] = mapped_column(Float)
    access_type: Mapped[str] = mapped_column(String(64), default="corridor")

    from_node: Mapped[IndoorNode] = relationship(foreign_keys=[from_node_id])
    to_node: Mapped[IndoorNode] = relationship(foreign_keys=[to_node_id])
