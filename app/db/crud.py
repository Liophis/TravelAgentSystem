from sqlalchemy.orm import Session

from app.db.models import POI
from app.models.poi import POISchema


# ==================== POI Operations ====================
def get_poi_by_name(db: Session, name: str) -> POI | None:
    """Query a POI record by exact name."""
    return db.query(POI).filter(POI.name == name).first()


def get_poi_by_id(db: Session, poi_id: int) -> POI | None:
    """Query a POI record by ID."""
    return db.query(POI).filter(POI.id == poi_id).first()


def get_all_pois(db: Session, skip: int = 0, limit: int = 100) -> list[POI]:
    """Get all POI records with pagination."""
    return db.query(POI).offset(skip).limit(limit).all()


def create_poi(db: Session, poi: POISchema) -> POI:
    """Create and persist a new POI record."""
    db_poi = POI(
        name=poi.name,
        type=poi.type,
        latitude=poi.latitude,
        longitude=poi.longitude,
        floor=poi.floor,
        description=poi.description,
    )
    db.add(db_poi)
    db.commit()
    db.refresh(db_poi)
    return db_poi
