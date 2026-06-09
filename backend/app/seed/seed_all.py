import os
import sys
from pathlib import Path

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from app.core.config import settings
from app.core.scenes import DEFAULT_SCENE_KEY
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
from app.algorithms.compression import compress_text
from app.algorithms.route_planning import approximate_distance_meters
from app.services.diary_service import rebuild_diary_search_index
from app.services.user_service import ADMIN_ROLE, NORMAL_USER_ROLE, hash_password
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

    normal_users = [
        User(
            username=f"user{i:02d}",
            email=f"user{i:02d}@example.com",
            password_hash=hash_password("demo123456"),
            role=NORMAL_USER_ROLE,
        )
        for i in range(1, 11)
    ]
    admin_user = User(
        username="admin01",
        email="admin01@example.com",
        password_hash=hash_password("admin123456"),
        role=ADMIN_ROLE,
    )
    users = [*normal_users, admin_user]
    session.add_all(users)
    session.flush()
    for index, user in enumerate(normal_users):
        session.add(UserProfile(user_id=user.id, nickname=f"游客 {index + 1}", avatar_url=None))
        for tag in INTEREST_TAGS[index % len(INTEREST_TAGS) : index % len(INTEREST_TAGS) + 2]:
            session.add(UserInterest(user_id=user.id, tag=tag))
    session.add(UserProfile(user_id=admin_user.id, nickname="管理员 1", avatar_url=None))

    destinations = _ensure_real_destinations(session)

    grid_cols = 15
    grid_rows = 12
    nodes = []
    for row in range(grid_rows):
        for col in range(grid_cols):
            index = row * grid_cols + col
            nodes.append(
                MapNode(
                    scene_key=DEFAULT_SCENE_KEY,
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
                scene_key=DEFAULT_SCENE_KEY,
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
                scene_key=DEFAULT_SCENE_KEY,
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
                scene_key=DEFAULT_SCENE_KEY,
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

    for index, user in enumerate(normal_users):
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

    diary_destinations = _diary_destination_pool(destinations)
    diaries = [
        _build_seed_diary(normal_users[index % len(normal_users)].id, diary_destinations[index], index)
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
                caption="目的地游记示例图片",
            )
            for index in range(3)
        ]
    )

    _seed_indoor_navigation(session)

    session.commit()
    return count_seeded_data(session)


def ensure_incremental_demo_data(session: Session) -> None:
    _ensure_existing_user_roles(session)
    _ensure_demo_admin(session)
    users = list(
        session.scalars(
            select(User)
            .where(User.role == NORMAL_USER_ROLE)
            .order_by(User.id)
            .limit(10)
        ).all()
    )
    destinations = _ensure_real_destinations(session)
    restaurants = list(session.scalars(select(Restaurant).order_by(Restaurant.id)).all())
    foods = list(session.scalars(select(Food).order_by(Food.id)).all())
    diaries = list(session.scalars(select(Diary).order_by(Diary.id)).all())
    if not users or not destinations:
        return

    _seed_indoor_navigation(session)

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

    diary_destinations = _diary_destination_pool(destinations)
    for index, diary in enumerate(diaries):
        _refresh_seed_diary_if_needed(diary, diary_destinations[index % len(diary_destinations)], index)
        rebuild_diary_search_index(session, diary)

    if diaries and session.scalar(select(DiaryMedia).limit(1)) is None:
        session.add_all(
            [
                DiaryMedia(
                    diary_id=diaries[index].id,
                    media_type="image",
                    url=f"/media/seed/diary-{index + 1}.jpg",
                    caption="目的地游记示例图片",
                )
                for index in range(min(3, len(diaries)))
            ]
        )


def _ensure_existing_user_roles(session: Session) -> None:
    for user in session.scalars(select(User)).all():
        if not user.role:
            user.role = NORMAL_USER_ROLE


def _ensure_demo_admin(session: Session) -> User:
    admin = session.scalar(select(User).where(User.username == "admin01"))
    if admin is None:
        admin = User(
            username="admin01",
            email="admin01@example.com",
            password_hash=hash_password("admin123456"),
            role=ADMIN_ROLE,
        )
        session.add(admin)
        session.flush()
        session.add(UserProfile(user_id=admin.id, nickname="管理员 1", avatar_url=None))
    else:
        admin.role = ADMIN_ROLE
        if admin.profile is None:
            session.add(UserProfile(user_id=admin.id, nickname="管理员 1", avatar_url=None))
    return admin


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
    _seed_teaching_building_indoor_navigation(session)
    _seed_science_museum_indoor_navigation(session)


def _seed_teaching_building_indoor_navigation(session: Session) -> None:
    building_name = "综合教学楼"
    if session.scalar(select(IndoorNode).where(IndoorNode.building_name == building_name).limit(1)) is not None:
        return
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


def _seed_science_museum_indoor_navigation(session: Session) -> None:
    building_name = "中国科学技术馆主展厅"
    existing_nodes = list(session.scalars(select(IndoorNode).where(IndoorNode.building_name == building_name)).all())
    if existing_nodes:
        existing_edges = list(
            session.scalars(select(IndoorEdge).where(IndoorEdge.building_name == building_name)).all()
        )
        if len(existing_nodes) >= 57 and len(existing_edges) >= 74:
            return
        session.execute(delete(IndoorEdge).where(IndoorEdge.building_name == building_name))
        session.execute(delete(IndoorNode).where(IndoorNode.building_name == building_name))
        session.flush()

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

    # B1: restaurant, auditorium, storage, and vertical traffic.
    add_node("b1-elevator", -1, "B1 电梯厅", "elevator", 42, 0)
    add_node("b1-stairs", -1, "B1 楼梯间", "stairs", 56, 0)
    add_node("b1-escalator", -1, "B1 扶梯", "escalator", 70, 0)
    add_node("b1-restaurant", -1, "B1 观众餐厅", "restaurant", 26, 22)
    add_node("b1-auditorium", -1, "B1 报告厅", "room", 42, 40)
    add_node("b1-storage", -1, "B1 存包取物点", "service", 60, 28)
    add_node("b1-toilet", -1, "B1 卫生间", "toilet", 78, 26)
    add_node("b1-parking", -1, "B1 停车场通道", "service", 14, 42)

    # 1F: entrance, lobby, services, and vertical traffic.
    add_node("f1-west-entrance", 1, "西门入口", "entrance", 10, 0)
    add_node("f1-security", 1, "一层安检口", "security", 22, 0)
    add_node("f1-lobby", 1, "一层大厅", "hall", 36, 0)
    add_node("f1-ticket", 1, "一层票务中心", "service", 20, 24)
    add_node("f1-storage", 1, "一层存包处", "service", 34, 26)
    add_node("f1-service", 1, "一层服务台", "service", 48, 24)
    add_node("f1-elevator", 1, "一层电梯厅", "elevator", 58, 0)
    add_node("f1-stairs", 1, "一层楼梯间", "stairs", 70, 0)
    add_node("f1-escalator", 1, "一层扶梯", "escalator", 82, 0)
    add_node("f1-toilet", 1, "一层卫生间", "toilet", 72, 26)
    add_node("f1-store", 1, "一层文创商店", "store", 86, 28)

    floor_halls = {
        2: ("探索与发现", "exhibit"),
        3: ("科技与生活", "exhibit"),
        4: ("挑战与未来", "exhibit"),
    }
    for floor, (title, node_type) in floor_halls.items():
        add_node(f"f{floor}-elevator", floor, f"{floor}F 电梯厅", "elevator", 24, 0)
        add_node(f"f{floor}-stairs", floor, f"{floor}F 楼梯间", "stairs", 38, 0)
        add_node(f"f{floor}-escalator", floor, f"{floor}F 扶梯", "escalator", 52, 0)
        add_node(f"f{floor}-hall", floor, f"{floor}F 中央大厅", "hall", 66, 0)
        add_node(f"f{floor}-a", floor, f"{floor}F {title} A 厅", node_type, 18, 28)
        add_node(f"f{floor}-b", floor, f"{floor}F {title} B 厅", node_type, 38, 36)
        add_node(f"f{floor}-c", floor, f"{floor}F {title} C 厅", node_type, 62, 36)
        add_node(f"f{floor}-d", floor, f"{floor}F {title} D 厅", node_type, 82, 28)
        add_node(f"f{floor}-toilet", floor, f"{floor}F 卫生间", "toilet", 88, 0)
        add_node(f"f{floor}-service", floor, f"{floor}F 服务点", "service", 74, 20)

    add_node("f5-elevator", 5, "5F 电梯厅", "elevator", 24, 0)
    add_node("f5-stairs", 5, "5F 楼梯间", "stairs", 38, 0)
    add_node("f5-escalator", 5, "5F 扶梯", "escalator", 52, 0)
    add_node("f5-hall", 5, "5F 中央大厅", "hall", 66, 0)
    add_node("f5-temporary-a", 5, "5F 短期展厅 A", "exhibit", 30, 32)
    add_node("f5-temporary-b", 5, "5F 短期展厅 B", "exhibit", 58, 38)
    add_node("f5-theater", 5, "5F 科学影像厅", "room", 80, 28)
    add_node("f5-toilet", 5, "5F 卫生间", "toilet", 88, 0)

    session.add_all(nodes)
    session.flush()

    edges: list[IndoorEdge] = []

    def add_edge(from_key: str, to_key: str, distance: float, access_type: str) -> None:
        speed = {
            "corridor": 1.15,
            "elevator": 0.35,
            "stairs": 0.65,
            "escalator": 0.55,
        }.get(access_type, 1.0)
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

    add_edge("b1-elevator", "b1-stairs", 12, "corridor")
    add_edge("b1-stairs", "b1-escalator", 12, "corridor")
    add_edge("b1-elevator", "b1-restaurant", 24, "corridor")
    add_edge("b1-elevator", "b1-auditorium", 28, "corridor")
    add_edge("b1-auditorium", "b1-storage", 18, "corridor")
    add_edge("b1-storage", "b1-toilet", 16, "corridor")
    add_edge("b1-restaurant", "b1-parking", 26, "corridor")

    add_edge("f1-west-entrance", "f1-security", 12, "corridor")
    add_edge("f1-security", "f1-lobby", 14, "corridor")
    add_edge("f1-lobby", "f1-ticket", 20, "corridor")
    add_edge("f1-lobby", "f1-storage", 18, "corridor")
    add_edge("f1-lobby", "f1-service", 12, "corridor")
    add_edge("f1-lobby", "f1-elevator", 20, "corridor")
    add_edge("f1-elevator", "f1-stairs", 12, "corridor")
    add_edge("f1-stairs", "f1-escalator", 12, "corridor")
    add_edge("f1-stairs", "f1-toilet", 18, "corridor")
    add_edge("f1-escalator", "f1-store", 20, "corridor")

    for floor in range(2, 5):
        add_edge(f"f{floor}-elevator", f"f{floor}-stairs", 12, "corridor")
        add_edge(f"f{floor}-stairs", f"f{floor}-escalator", 12, "corridor")
        add_edge(f"f{floor}-escalator", f"f{floor}-hall", 14, "corridor")
        add_edge(f"f{floor}-elevator", f"f{floor}-hall", 20, "corridor")
        add_edge(f"f{floor}-hall", f"f{floor}-a", 24, "corridor")
        add_edge(f"f{floor}-a", f"f{floor}-b", 18, "corridor")
        add_edge(f"f{floor}-b", f"f{floor}-c", 18, "corridor")
        add_edge(f"f{floor}-c", f"f{floor}-d", 18, "corridor")
        add_edge(f"f{floor}-hall", f"f{floor}-service", 16, "corridor")
        add_edge(f"f{floor}-service", f"f{floor}-toilet", 18, "corridor")
        add_edge(f"f{floor}-d", f"f{floor}-toilet", 16, "corridor")

    add_edge("f5-elevator", "f5-stairs", 12, "corridor")
    add_edge("f5-stairs", "f5-escalator", 12, "corridor")
    add_edge("f5-escalator", "f5-hall", 14, "corridor")
    add_edge("f5-elevator", "f5-hall", 20, "corridor")
    add_edge("f5-hall", "f5-temporary-a", 22, "corridor")
    add_edge("f5-temporary-a", "f5-temporary-b", 22, "corridor")
    add_edge("f5-temporary-b", "f5-theater", 24, "corridor")
    add_edge("f5-hall", "f5-toilet", 22, "corridor")
    add_edge("f5-theater", "f5-toilet", 18, "corridor")

    vertical_pairs = [("b1", "f1"), ("f1", "f2"), ("f2", "f3"), ("f3", "f4"), ("f4", "f5")]
    for lower, upper in vertical_pairs:
        add_edge(f"{lower}-elevator", f"{upper}-elevator", 6, "elevator")
        add_edge(f"{lower}-stairs", f"{upper}-stairs", 18, "stairs")
        add_edge(f"{lower}-escalator", f"{upper}-escalator", 14, "escalator")

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


def _build_seed_diary(user_id: int, destination: Destination, index: int) -> Diary:
    title, body = _seed_diary_title_body(destination, index)
    compressed_body, original_size, compressed_size = compress_text(body)
    return Diary(
        user_id=user_id,
        destination_id=destination.id,
        title=title,
        body="",
        compressed_body=compressed_body,
        original_size=original_size,
        compressed_size=compressed_size,
        views=index * 3,
    )


def _diary_destination_pool(destinations: list[Destination]) -> list[Destination]:
    scenic_destinations = [destination for destination in destinations if destination.category != "school"]
    return scenic_destinations or destinations


def _refresh_seed_diary_if_needed(diary: Diary, destination: Destination, index: int) -> None:
    if not diary.title.startswith("沙河校区游记") and "Stage 2" not in diary.body:
        return
    title, body = _seed_diary_title_body(destination, index)
    compressed_body, original_size, compressed_size = compress_text(body)
    diary.destination_id = destination.id
    diary.title = title
    diary.body = ""
    diary.compressed_body = compressed_body
    diary.original_size = original_size
    diary.compressed_size = compressed_size


def _seed_diary_title_body(destination: Destination, index: int) -> tuple[str, str]:
    category_label = "高校" if destination.category == "school" else "景区"
    focus_points = [
        "入口动线、核心景观点和休息设施",
        "游客热度、评价口碑和周边餐饮",
        "展馆路线、拍照点和服务设施",
        "步行距离、游览节奏和夜景体验",
    ]
    focus = focus_points[index % len(focus_points)]
    title = f"{destination.name}旅行日记：{focus}"
    body = (
        f"这次把{destination.name}作为{category_label}目的地来记录。"
        f"出发前我先查看了目的地热度、评分和相关游记，实际到达后重点观察了{focus}。"
        f"游览过程中，路线安排以少走回头路为目标，先到达标志性区域，再补充参观周边空间。"
        f"如果同行者对历史文化、校园氛围或自然景观感兴趣，{destination.name}都适合作为半日到一日行程。"
        f"这篇日记用于演示目的地相关游记检索、热度排序、评分交流、正文全文搜索以及压缩存储。"
    )
    return title, body


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
