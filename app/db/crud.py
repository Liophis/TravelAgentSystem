from sqlalchemy.orm import Session

from app.db.models import POI, User, Facility, TravelDiary
from app.models.poi import POISchema
from app.models.user import UserSchema


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


# ==================== User Operations ====================
def get_user_by_username(db: Session, username: str) -> User | None:
    """Query a user by username."""
    return db.query(User).filter(User.username == username).first()


def get_user_by_id(db: Session, user_id: int) -> User | None:
    """Query a user by ID."""
    return db.query(User).filter(User.id == user_id).first()


def create_user(db: Session, user: UserSchema) -> User:
    """Create and persist a new user."""
    db_user = User(
        username=user.username,
        email=user.email,
        interests=user.interests,
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


# ==================== Facility Operations ====================
def get_facilities_by_poi(db: Session, poi_id: int) -> list[Facility]:
    """Get all facilities for a POI."""
    return db.query(Facility).filter(Facility.poi_id == poi_id).all()


def create_facility(db: Session, poi_id: int, name: str, facility_type: str, location_desc: str = None) -> Facility:
    """Create and persist a new facility."""
    db_facility = Facility(
        name=name,
        type=facility_type,
        poi_id=poi_id,
        location_desc=location_desc,
    )
    db.add(db_facility)
    db.commit()
    db.refresh(db_facility)
    return db_facility


# ==================== TravelDiary Operations ====================
def create_diary(db: Session, user_id: int, title: str, content: str, poi_id: int = None) -> TravelDiary:
    """Create and persist a new travel diary."""
    db_diary = TravelDiary(
        user_id=user_id,
        title=title,
        content=content,
        poi_id=poi_id,
    )
    db.add(db_diary)
    db.commit()
    db.refresh(db_diary)
    return db_diary


def get_diary_by_user(db: Session, user_id: int, skip: int = 0, limit: int = 100) -> list[TravelDiary]:
    """Get all diaries for a user."""
    return db.query(TravelDiary).filter(TravelDiary.user_id == user_id).offset(skip).limit(limit).all()


def get_diary_by_id(db: Session, diary_id: int) -> TravelDiary | None:
    """Get a diary by ID."""
    return db.query(TravelDiary).filter(TravelDiary.id == diary_id).first()
