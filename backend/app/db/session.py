from collections.abc import Generator

from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import settings


def create_app_engine(database_url: str | None = None) -> Engine:
    url = database_url or settings.database_url
    connect_args = {"check_same_thread": False} if url.startswith("sqlite") else {}
    return create_engine(url, connect_args=connect_args, future=True)


def create_session_factory(database_url: str | None = None) -> sessionmaker[Session]:
    return sessionmaker(
        bind=create_app_engine(database_url),
        autoflush=False,
        autocommit=False,
        future=True,
    )


def get_db() -> Generator[Session, None, None]:
    session_local = create_session_factory()
    db = session_local()
    try:
        yield db
    finally:
        db.close()
