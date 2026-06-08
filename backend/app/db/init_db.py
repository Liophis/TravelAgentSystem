from sqlalchemy import Engine
from sqlalchemy import inspect, text

from app.core.scenes import DEFAULT_SCENE_KEY
from app.db.base import Base
from app.models import *  # noqa: F401,F403


def create_all(engine: Engine) -> None:
    Base.metadata.create_all(bind=engine)
    ensure_compatible_schema(engine)


def drop_all(engine: Engine) -> None:
    Base.metadata.drop_all(bind=engine)


def ensure_compatible_schema(engine: Engine) -> None:
    inspector = inspect(engine)
    table_names = set(inspector.get_table_names())
    with engine.begin() as connection:
        for table_name in ("map_nodes", "map_edges", "buildings", "facilities"):
            if table_name in table_names:
                columns = {column["name"] for column in inspector.get_columns(table_name)}
                if "scene_key" not in columns:
                    connection.execute(
                        text(
                            f"ALTER TABLE {table_name} "
                            f"ADD COLUMN scene_key VARCHAR(64) NOT NULL DEFAULT '{DEFAULT_SCENE_KEY}'"
                        )
                    )
        if "users" in table_names:
            user_columns = {column["name"] for column in inspector.get_columns("users")}
            if "role" not in user_columns:
                connection.execute(text("ALTER TABLE users ADD COLUMN role VARCHAR(32) NOT NULL DEFAULT 'user'"))
        if "restaurants" in table_names:
            restaurant_columns = {column["name"] for column in inspector.get_columns("restaurants")}
            if "destination_id" not in restaurant_columns:
                connection.execute(text("ALTER TABLE restaurants ADD COLUMN destination_id INTEGER"))
