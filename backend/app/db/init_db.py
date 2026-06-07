from sqlalchemy import Engine

from app.db.base import Base
from app.models import *  # noqa: F401,F403


def create_all(engine: Engine) -> None:
    Base.metadata.create_all(bind=engine)


def drop_all(engine: Engine) -> None:
    Base.metadata.drop_all(bind=engine)
