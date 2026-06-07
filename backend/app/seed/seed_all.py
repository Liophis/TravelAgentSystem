import os
import sys
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session

if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from app.core.config import settings
from app.db.init_db import create_all
from app.db.session import create_app_engine
from app.models import (
    Building,
    Destination,
    DestinationTag,
    Diary,
    Facility,
    FacilityCategory,
    Food,
    MapEdge,
    MapNode,
    Restaurant,
    User,
    UserInterest,
    UserProfile,
)
from app.seed.sample_data import BUPT_SHAHE_CENTER, FACILITY_CATEGORIES, FOOD_CUISINES, INTEREST_TAGS


def resolve_seed_database_url() -> str:
    return os.getenv("SEED_DATABASE_URL") or os.getenv("DEV_DATABASE_URL") or settings.dev_database_url


def seed_demo_data(session: Session) -> dict[str, int]:
    if session.scalar(select(User).limit(1)) is not None:
        return count_seeded_data(session)

    center_lng, center_lat = BUPT_SHAHE_CENTER

    users = [
        User(username=f"user{i:02d}", email=f"user{i:02d}@example.com", password_hash="demo-hash")
        for i in range(1, 11)
    ]
    session.add_all(users)
    session.flush()
    for index, user in enumerate(users):
        session.add(UserProfile(user_id=user.id, nickname=f"游客 {index + 1}", avatar_url=None))
        for tag in INTEREST_TAGS[index % len(INTEREST_TAGS) : index % len(INTEREST_TAGS) + 2]:
            session.add(UserInterest(user_id=user.id, tag=tag))

    destinations = []
    for index in range(200):
        lng = center_lng + ((index % 20) - 10) * 0.00018
        lat = center_lat + ((index // 20) - 5) * 0.00016
        destination = Destination(
            name=f"北邮沙河导览点 {index + 1:03d}",
            category=["campus", "building", "service", "landscape"][index % 4],
            description="北京邮电大学沙河校区演示目的地数据。",
            lng=lng,
            lat=lat,
            rating=4.2 + (index % 8) * 0.1,
            popularity=80 + index,
        )
        destinations.append(destination)
    session.add_all(destinations)
    session.flush()
    for index, destination in enumerate(destinations[:40]):
        session.add(DestinationTag(destination_id=destination.id, tag=INTEREST_TAGS[index % len(INTEREST_TAGS)]))

    nodes = [
        MapNode(
            external_id=f"bupt-node-{index + 1}",
            name=f"路口 {index + 1}",
            lng=center_lng + (index % 10) * 0.00022,
            lat=center_lat + (index // 10) * 0.00022,
        )
        for index in range(80)
    ]
    session.add_all(nodes)
    session.flush()
    edges = []
    for index in range(220):
        from_node = nodes[index % len(nodes)]
        to_node = nodes[(index + 1 + index // len(nodes)) % len(nodes)]
        edges.append(
            MapEdge(
                from_node_id=from_node.id,
                to_node_id=to_node.id,
                distance=85 + index,
                walk_time=(85 + index) / 1.2,
                geometry=[[from_node.lng, from_node.lat], [to_node.lng, to_node.lat]],
            )
        )
    session.add_all(edges)

    buildings = []
    for index in range(20):
        lng = center_lng + (index % 5) * 0.00035
        lat = center_lat + (index // 5) * 0.00030
        buildings.append(
            Building(
                name=f"沙河校区建筑 {index + 1}",
                category="teaching" if index % 2 == 0 else "service",
                polygon=[
                    [lng, lat],
                    [lng + 0.00018, lat],
                    [lng + 0.00018, lat + 0.00014],
                    [lng, lat + 0.00014],
                ],
                description="Stage 2 seed building polygon.",
            )
        )
    session.add_all(buildings)

    categories = [FacilityCategory(code=code, name=name) for code, name in FACILITY_CATEGORIES]
    session.add_all(categories)
    session.flush()
    facilities = []
    for index in range(50):
        category = categories[index % len(categories)]
        facilities.append(
            Facility(
                name=f"{category.name} {index + 1}",
                category_id=category.id,
                nearest_node_id=nodes[index % len(nodes)].id,
                lng=center_lng + (index % 10) * 0.00020,
                lat=center_lat + (index // 10) * 0.00018,
                description="Stage 2 seed facility.",
            )
        )
    session.add_all(facilities)

    restaurants = [
        Restaurant(
            name=f"沙河餐厅 {index + 1}",
            lng=center_lng + index * 0.00025,
            lat=center_lat + index * 0.00018,
            heat=100 - index,
        )
        for index in range(5)
    ]
    session.add_all(restaurants)
    session.flush()
    foods = []
    for index in range(30):
        foods.append(
            Food(
                restaurant_id=restaurants[index % len(restaurants)].id,
                name=f"推荐菜品 {index + 1}",
                cuisine=FOOD_CUISINES[index % len(FOOD_CUISINES)],
                price=12 + index % 18,
                rating=4.0 + (index % 10) * 0.08,
                heat=60 + index,
            )
        )
    session.add_all(foods)

    diaries = [
        Diary(
            user_id=users[index % len(users)].id,
            destination_id=destinations[index].id,
            title=f"沙河校区游记 {index + 1}",
            body="这里是 Stage 2 的游记种子文本，用于后续全文检索和压缩功能。",
            views=index * 3,
        )
        for index in range(20)
    ]
    session.add_all(diaries)

    session.commit()
    return count_seeded_data(session)


def count_seeded_data(session: Session) -> dict[str, int]:
    models = {
        "users": User,
        "destinations": Destination,
        "map_nodes": MapNode,
        "map_edges": MapEdge,
        "buildings": Building,
        "facility_categories": FacilityCategory,
        "facilities": Facility,
        "restaurants": Restaurant,
        "foods": Food,
        "diaries": Diary,
    }
    return {name: len(session.scalars(select(model)).all()) for name, model in models.items()}


def main() -> None:
    database_url = resolve_seed_database_url()
    engine = create_app_engine(database_url)
    create_all(engine)
    with Session(engine) as session:
        counts = seed_demo_data(session)
    print("[seed] database:", database_url)
    for name, count in counts.items():
        print(f"[seed] {name}: {count}")


if __name__ == "__main__":
    main()
