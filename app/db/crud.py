from sqlalchemy.orm import Session

from app.db.models import POI
from app.models.poi import POISchema


def get_poi_by_name(db: Session, name: str) -> POI | None:
    """Query a POI record by exact name."""
    return db.query(POI).filter(POI.name == name).first()


def create_poi(db: Session, poi: POISchema) -> POI:
    """Create and persist a new POI record."""
    db_poi = POI(
        name=poi.name,
        type=poi.type,
        latitude=poi.latitude,
        longitude=poi.longitude,
        floor=poi.floor,
    )
    db.add(db_poi)
    db.commit()
    db.refresh(db_poi)
    return db_poi
