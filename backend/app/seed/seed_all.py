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
from app.algorithms.route_planning import approximate_distance_meters
from app.seed.sample_data import (
    BUPT_BUILDING_NAMES,
    BUPT_FACILITY_PREFIXES,
    BUPT_FOOD_NAMES,
    BUPT_RESTAURANT_NAMES,
    BUPT_SHAHE_CENTER,
    FACILITY_CATEGORIES,
    FOOD_CUISINES,
    INTEREST_TAGS,
)


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

    grid_cols = 15
    grid_rows = 12
    nodes = []
    for row in range(grid_rows):
        for col in range(grid_cols):
            index = row * grid_cols + col
            nodes.append(
                MapNode(
                    external_id=f"bupt-node-{index + 1}",
                    name=f"校园路口 R{row + 1:02d}-C{col + 1:02d}",
                    lng=center_lng + (col - grid_cols // 2) * 0.00018,
                    lat=center_lat + (row - grid_rows // 2) * 0.00016,
                )
            )
    session.add_all(nodes)
    session.flush()
    edges = []

    def node_at(row: int, col: int) -> MapNode:
        return nodes[row * grid_cols + col]

    def add_edge(from_node: MapNode, to_node: MapNode, allowed_modes: list[str]) -> None:
        distance = round(approximate_distance_meters((from_node.lng, from_node.lat), (to_node.lng, to_node.lat)))
        congestion = round(0.72 + (len(edges) % 8) * 0.035, 2)
        walk_speed = 1.25
        bike_speed = 3.8 if "bike" in allowed_modes else 0.0
        electric_cart_speed = 5.2 if "electric_cart" in allowed_modes else 0.0
        edges.append(
            MapEdge(
                from_node_id=from_node.id,
                to_node_id=to_node.id,
                distance=distance,
                walk_time=distance / (walk_speed * congestion),
                congestion=congestion,
                walk_speed=walk_speed,
                bike_speed=bike_speed,
                electric_cart_speed=electric_cart_speed,
                allowed_modes=allowed_modes,
                geometry=[[from_node.lng, from_node.lat], [to_node.lng, to_node.lat]],
            )
        )

    for row in range(grid_rows):
        for col in range(grid_cols):
            if col < grid_cols - 1:
                modes = ["walk", "bike"]
                if row in {grid_rows // 2 - 1, grid_rows // 2}:
                    modes.append("electric_cart")
                add_edge(node_at(row, col), node_at(row, col + 1), modes)
            if row < grid_rows - 1:
                modes = ["walk", "bike"]
                if col == grid_cols // 2:
                    modes.append("electric_cart")
                add_edge(node_at(row, col), node_at(row + 1, col), modes)
            if row < grid_rows - 1 and col < grid_cols - 1:
                add_edge(node_at(row, col), node_at(row + 1, col + 1), ["walk"])
            if row < grid_rows - 1 and col > 0:
                add_edge(node_at(row, col), node_at(row + 1, col - 1), ["walk"])
    session.add_all(edges)

    buildings = []
    for index in range(60):
        lng = center_lng + ((index % 10) - 5) * 0.00028
        lat = center_lat + ((index // 10) - 3) * 0.00024
        name = BUPT_BUILDING_NAMES[index % len(BUPT_BUILDING_NAMES)]
        buildings.append(
            Building(
                name=f"{name} {index // len(BUPT_BUILDING_NAMES) + 1}" if index >= len(BUPT_BUILDING_NAMES) else name,
                category=["teaching", "service", "dormitory", "sports"][index % 4],
                polygon=[
                    [lng, lat],
                    [lng + 0.00016, lat],
                    [lng + 0.00016, lat + 0.00013],
                    [lng, lat + 0.00013],
                ],
                description="Campus-density seed building polygon. 校园建筑数据。",
            )
        )
    session.add_all(buildings)

    categories = [FacilityCategory(code=code, name=name) for code, name in FACILITY_CATEGORIES]
    session.add_all(categories)
    session.flush()
    facilities = []
    for index in range(120):
        category = categories[index % len(categories)]
        nearest_node = nodes[(index * 7) % len(nodes)]
        prefixes = BUPT_FACILITY_PREFIXES.get(category.code, [category.name])
        facilities.append(
            Facility(
                name=f"{prefixes[index % len(prefixes)]} {index // len(prefixes) + 1}",
                category_id=category.id,
                nearest_node_id=nearest_node.id,
                lng=nearest_node.lng + ((index % 3) - 1) * 0.00003,
                lat=nearest_node.lat + ((index % 4) - 2) * 0.000025,
                description="Campus-density seed facility.",
            )
        )
    session.add_all(facilities)

    restaurants = [
        Restaurant(
            name=BUPT_RESTAURANT_NAMES[index],
            lng=center_lng + ((index % 4) - 2) * 0.00032,
            lat=center_lat + ((index // 4) - 1) * 0.00028,
            heat=120 - index * 3,
        )
        for index in range(len(BUPT_RESTAURANT_NAMES))
    ]
    session.add_all(restaurants)
    session.flush()
    foods = []
    for index in range(72):
        foods.append(
            Food(
                restaurant_id=restaurants[index % len(restaurants)].id,
                name=f"{BUPT_FOOD_NAMES[index % len(BUPT_FOOD_NAMES)]} {index // len(BUPT_FOOD_NAMES) + 1}",
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
