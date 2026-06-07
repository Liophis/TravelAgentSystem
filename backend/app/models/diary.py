from datetime import UTC, datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Diary(Base):
    __tablename__ = "diaries"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    destination_id: Mapped[int | None] = mapped_column(ForeignKey("destinations.id"), nullable=True)
    title: Mapped[str] = mapped_column(String(160), index=True)
    body: Mapped[str] = mapped_column(Text)
    compressed_body: Mapped[str | None] = mapped_column(Text, nullable=True)
    original_size: Mapped[int] = mapped_column(Integer, default=0)
    compressed_size: Mapped[int] = mapped_column(Integer, default=0)
    views: Mapped[int] = mapped_column(Integer, default=0)
    rating_sum: Mapped[int] = mapped_column(Integer, default=0)
    rating_count: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(UTC))

    comments: Mapped[list["DiaryComment"]] = relationship(back_populates="diary")
    ratings: Mapped[list["DiaryRating"]] = relationship(back_populates="diary")


class DiaryComment(Base):
    __tablename__ = "diary_comments"

    id: Mapped[int] = mapped_column(primary_key=True)
    diary_id: Mapped[int] = mapped_column(ForeignKey("diaries.id"), index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    content: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(UTC))

    diary: Mapped[Diary] = relationship(back_populates="comments")


class DiaryRating(Base):
    __tablename__ = "diary_ratings"

    id: Mapped[int] = mapped_column(primary_key=True)
    diary_id: Mapped[int] = mapped_column(ForeignKey("diaries.id"), index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    value: Mapped[int] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(UTC))

    diary: Mapped[Diary] = relationship(back_populates="ratings")
