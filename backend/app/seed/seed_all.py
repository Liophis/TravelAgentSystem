import os
import sys
from pathlib import Path

from sqlalchemy import delete, select
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
    DiaryMedia,
    Facility,
    FacilityCategory,
    Food,
    IndoorEdge,
    IndoorNode,
    MapEdge,
    MapNode,
    Restaurant,
    User,
    UserBehaviorLog,
    UserFavorite,
    UserInterest,
    UserProfile,
    UserRating,
)
from app.algorithms.route_planning import approximate_distance_meters
from app.services.diary_service import rebuild_diary_search_index
from app.services.user_service import hash_password
from app.seed.real_destinations import DESTINATION_SEED_SOURCE_NOTE, build_real_destination_seed
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
        ensure_incremental_demo_data(session)
        session.commit()
        return count_seeded_data(session)

    center_lng, center_lat = BUPT_SHAHE_CENTER

    users = [
        User(username=f"user{i:02d}", email=f"user{i:02d}@example.com", password_hash=hash_password("demo123456"))
        for i in range(1, 11)
    ]
    session.add_all(users)
    session.flush()
    for index, user in enumerate(users):
        session.add(UserProfile(user_id=user.id, nickname=f"游客 {index + 1}", avatar_url=None))
        for tag in INTEREST_TAGS[index % len(INTEREST_TAGS) : index % len(INTEREST_TAGS) + 2]:
            session.add(UserInterest(user_id=user.id, tag=tag))

    destinations = _ensure_real_destinations(session)

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
            destination_id=destinations[index % len(destinations)].id,
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
    session.flush()

    for index, user in enumerate(users):
        target_destination = destinations[(index * 3) % len(destinations)]
        target_food = foods[(index * 5) % len(foods)]
        session.add(
            UserFavorite(
                user_id=user.id,
                target_type="destination",
                target_id=target_destination.id,
                note="种子收藏，用于演示收藏影响推荐。",
            )
        )
        session.add(
            UserRating(
                user_id=user.id,
                target_type="destination",
                target_id=target_destination.id,
                rating=4.2 + (index % 4) * 0.2,
            )
        )
        session.add(
            UserBehaviorLog(
                user_id=user.id,
                target_type="destination",
                target_id=target_destination.id,
                action="view",
                metadata_text="seed browse event",
            )
        )
        session.add(
            UserFavorite(
                user_id=user.id,
                target_type="food",
                target_id=target_food.id,
                note="种子美食收藏。",
            )
        )

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
    session.flush()
    for diary in diaries:
        rebuild_diary_search_index(session, diary)
    session.add_all(
        [
            DiaryMedia(
                diary_id=diaries[index].id,
                media_type="image",
                url=f"/media/seed/diary-{index + 1}.jpg",
                caption="沙河校区游记示例图片",
            )
            for index in range(3)
        ]
    )

    _seed_indoor_navigation(session)

    session.commit()
    return count_seeded_data(session)


def ensure_incremental_demo_data(session: Session) -> None:
    users = list(session.scalars(select(User).order_by(User.id).limit(10)).all())
    destinations = _ensure_real_destinations(session)
    restaurants = list(session.scalars(select(Restaurant).order_by(Restaurant.id)).all())
    foods = list(session.scalars(select(Food).order_by(Food.id)).all())
    diaries = list(session.scalars(select(Diary).order_by(Diary.id)).all())
    if not users or not destinations:
        return

    for restaurant in restaurants:
        if restaurant.destination_id is None:
            nearest = min(
                destinations,
                key=lambda destination: approximate_distance_meters(
                    (restaurant.lng, restaurant.lat),
                    (destination.lng, destination.lat),
                ),
            )
            restaurant.destination_id = nearest.id

    if session.scalar(select(UserFavorite).limit(1)) is None:
        for index, user in enumerate(users):
            destination = destinations[(index * 3) % len(destinations)]
            session.add(
                UserFavorite(
                    user_id=user.id,
                    target_type="destination",
                    target_id=destination.id,
                    note="增量种子收藏，用于演示收藏影响推荐。",
                )
            )
            if foods:
                food = foods[(index * 5) % len(foods)]
                session.add(
                    UserFavorite(
                        user_id=user.id,
                        target_type="food",
                        target_id=food.id,
                        note="增量种子美食收藏。",
                    )
                )

    if session.scalar(select(UserRating).limit(1)) is None:
        for index, user in enumerate(users):
            destination = destinations[(index * 3) % len(destinations)]
            session.add(
                UserRating(
                    user_id=user.id,
                    target_type="destination",
                    target_id=destination.id,
                    rating=4.2 + (index % 4) * 0.2,
                )
            )

    if session.scalar(select(UserBehaviorLog).limit(1)) is None:
        for index, user in enumerate(users):
            destination = destinations[(index * 3) % len(destinations)]
            session.add(
                UserBehaviorLog(
                    user_id=user.id,
                    target_type="destination",
                    target_id=destination.id,
                    action="view",
                    metadata_text="incremental seed browse event",
                )
            )

    for diary in diaries:
        rebuild_diary_search_index(session, diary)

    if diaries and session.scalar(select(DiaryMedia).limit(1)) is None:
        session.add_all(
            [
                DiaryMedia(
                    diary_id=diaries[index].id,
                    media_type="image",
                    url=f"/media/seed/diary-{index + 1}.jpg",
                    caption="沙河校区游记示例图片",
                )
                for index in range(min(3, len(diaries)))
            ]
        )


def _ensure_real_destinations(session: Session) -> list[Destination]:
    seed_rows = build_real_destination_seed()
    destinations = list(session.scalars(select(Destination).order_by(Destination.id)).all())
    should_refresh = (
        len(destinations) < len(seed_rows)
        or any(destination.name.startswith("北邮沙河导览点") for destination in destinations[:20])
    )
    if not should_refresh:
        return destinations

    seeded: list[Destination] = []
    for index, row in enumerate(seed_rows):
        if index < len(destinations):
            destination = destinations[index]
        else:
            destination = Destination(
                name=row["name"],
                category=row["category"],
                description="",
                lng=row["lng"],
                lat=row["lat"],
                rating=row["rating"],
                popularity=row["popularity"],
            )
            session.add(destination)
            destinations.append(destination)
        _apply_real_destination_row(destination, row)
        seeded.append(destination)

    session.flush()
    seeded_ids = [destination.id for destination in seeded]
    if seeded_ids:
        session.execute(delete(DestinationTag).where(DestinationTag.destination_id.in_(seeded_ids)))
    for destination, row in zip(seeded, seed_rows):
        for tag in row["tags"]:
            session.add(DestinationTag(destination_id=destination.id, tag=tag))
    session.flush()
    return seeded


def _apply_real_destination_row(destination: Destination, row: dict[str, object]) -> None:
    category_label = "学校" if row["category"] == "school" else "景区"
    destination.name = str(row["name"])
    destination.category = str(row["category"])
    destination.description = (
        f"{row['province']}{row['city']}真实{category_label}目的地。"
        f"用于旅游推荐、搜索、热度/评分排序和个性化兴趣匹配。"
        f"{DESTINATION_SEED_SOURCE_NOTE}"
    )
    destination.lng = float(row["lng"])
    destination.lat = float(row["lat"])
    destination.rating = float(row["rating"])
    destination.popularity = int(row["popularity"])


def _seed_indoor_navigation(session: Session) -> None:
    building_name = "综合教学楼"
    nodes: list[IndoorNode] = []
    lookup: dict[str, IndoorNode] = {}

    def add_node(key: str, floor: int, name: str, node_type: str, x: float, y: float) -> None:
        node = IndoorNode(
            building_name=building_name,
            floor=floor,
            name=name,
            node_type=node_type,
            x=x,
            y=y,
        )
        nodes.append(node)
        lookup[key] = node

    add_node("f1-gate", 1, "一层大门", "entrance", 0, 0)
    for floor in range(1, 4):
        prefix = ["一", "二", "三"][floor - 1]
        add_node(f"f{floor}-hall", floor, f"{prefix}层大厅", "hall", 20, 0)
        add_node(f"f{floor}-elevator", floor, f"{prefix}层电梯", "elevator", 36, 0)
        add_node(f"f{floor}-stairs", floor, f"{prefix}层楼梯", "stairs", 52, 0)
        add_node(f"f{floor}-toilet", floor, f"{prefix}层卫生间", "toilet", 68, 0)
        add_node(f"f{floor}-room-a", floor, f"{floor}01 教室", "room", 36, 24)
        add_node(f"f{floor}-room-b", floor, f"{floor}05 教室", "room", 68, 24)

    session.add_all(nodes)
    session.flush()

    edges: list[IndoorEdge] = []

    def add_edge(from_key: str, to_key: str, distance: float, access_type: str) -> None:
        speed = 1.15 if access_type == "corridor" else 0.7
        if access_type == "elevator":
            speed = 0.5
        edges.append(
            IndoorEdge(
                building_name=building_name,
                from_node_id=lookup[from_key].id,
                to_node_id=lookup[to_key].id,
                distance=distance,
                duration=distance / speed,
                access_type=access_type,
            )
        )

    add_edge("f1-gate", "f1-hall", 20, "corridor")
    for floor in range(1, 4):
        add_edge(f"f{floor}-hall", f"f{floor}-elevator", 16, "corridor")
        add_edge(f"f{floor}-elevator", f"f{floor}-stairs", 16, "corridor")
        add_edge(f"f{floor}-stairs", f"f{floor}-toilet", 16, "corridor")
        add_edge(f"f{floor}-elevator", f"f{floor}-room-a", 24, "corridor")
        add_edge(f"f{floor}-stairs", f"f{floor}-room-b", 24, "corridor")
    for floor in range(1, 3):
        add_edge(f"f{floor}-elevator", f"f{floor + 1}-elevator", 4, "elevator")
        add_edge(f"f{floor}-stairs", f"f{floor + 1}-stairs", 12, "stairs")

    session.add_all(edges)


def count_seeded_data(session: Session) -> dict[str, int]:
    models = {
        "users": User,
        "user_favorites": UserFavorite,
        "user_ratings": UserRating,
        "user_behavior_logs": UserBehaviorLog,
        "destinations": Destination,
        "map_nodes": MapNode,
        "map_edges": MapEdge,
        "buildings": Building,
        "facility_categories": FacilityCategory,
        "facilities": Facility,
        "indoor_nodes": IndoorNode,
        "indoor_edges": IndoorEdge,
        "restaurants": Restaurant,
        "foods": Food,
        "diaries": Diary,
        "diary_media": DiaryMedia,
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
