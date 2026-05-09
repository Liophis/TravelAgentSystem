from sqlalchemy import text

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings

from app.api.routes import router
from app.db.bootstrap import sync_sample_pois
from app.db.database import engine
from app.db.database import SessionLocal
from app.db.models import Base


Base.metadata.create_all(bind=engine)


def ensure_poi_city_column() -> None:
    with engine.begin() as connection:
        columns = connection.execute(text("PRAGMA table_info(pois)")).fetchall()
        column_names = {row[1] for row in columns}
        if "city" not in column_names:
            connection.execute(text("ALTER TABLE pois ADD COLUMN city VARCHAR(100) NOT NULL DEFAULT '北京'"))


ensure_poi_city_column()


def ensure_sample_pois() -> None:
    db = SessionLocal()
    try:
        sync_sample_pois(db)
    finally:
        db.close()


ensure_sample_pois()
settings = get_settings()

app = FastAPI(
    title=settings.app_name,
    description="Personalized travel planning backend powered by FastAPI.",
    version=settings.app_version,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.get_cors_origins_list(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)


@app.get("/")
def root() -> dict[str, str]:
    return {"message": "欢迎使用旅游智能体系统 API"}
