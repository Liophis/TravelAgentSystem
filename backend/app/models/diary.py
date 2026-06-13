from datetime import datetime, timezone

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
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))

    comments: Mapped[list["DiaryComment"]] = relationship(back_populates="diary")
    ratings: Mapped[list["DiaryRating"]] = relationship(back_populates="diary")
    media: Mapped[list["DiaryMedia"]] = relationship(back_populates="diary")


class DiaryComment(Base):
    __tablename__ = "diary_comments"

    id: Mapped[int] = mapped_column(primary_key=True)
    diary_id: Mapped[int] = mapped_column(ForeignKey("diaries.id"), index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    content: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))

    diary: Mapped[Diary] = relationship(back_populates="comments")


class DiaryRating(Base):
    __tablename__ = "diary_ratings"

    id: Mapped[int] = mapped_column(primary_key=True)
    diary_id: Mapped[int] = mapped_column(ForeignKey("diaries.id"), index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    value: Mapped[int] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))

    diary: Mapped[Diary] = relationship(back_populates="ratings")


class DiaryMedia(Base):
    __tablename__ = "diary_media"

    id: Mapped[int] = mapped_column(primary_key=True)
    diary_id: Mapped[int] = mapped_column(ForeignKey("diaries.id"), index=True)
    media_type: Mapped[str] = mapped_column(String(32), index=True)
    url: Mapped[str] = mapped_column(String(512))
    caption: Mapped[str | None] = mapped_column(String(160), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))

    diary: Mapped[Diary] = relationship(back_populates="media")


class DiaryTitleIndex(Base):
    __tablename__ = "diary_title_indexes"

    id: Mapped[int] = mapped_column(primary_key=True)
    diary_id: Mapped[int] = mapped_column(ForeignKey("diaries.id"), unique=True, index=True)
    normalized_title: Mapped[str] = mapped_column(String(200), index=True)


class DiarySearchToken(Base):
    __tablename__ = "diary_search_tokens"

    id: Mapped[int] = mapped_column(primary_key=True)
    diary_id: Mapped[int] = mapped_column(ForeignKey("diaries.id"), index=True)
    token: Mapped[str] = mapped_column(String(80), index=True)
    field: Mapped[str] = mapped_column(String(24), default="body")
    frequency: Mapped[int] = mapped_column(Integer, default=1)
