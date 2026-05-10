import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from sqlalchemy import create_engine
from sqlalchemy.orm import close_all_sessions, sessionmaker

os.environ.setdefault("DEBUG", "false")
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.api import routes
from app.models import TripChatRequest
from app.db.models import Base, POI
from app.services.xhs_content_service import XHSContentService


class TravelApiFlowTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp_dir = tempfile.TemporaryDirectory()
        cls.db_path = Path(cls.temp_dir.name) / "test_travel_agent.db"
        cls.engine = create_engine(
            f"sqlite:///{cls.db_path}",
            connect_args={"check_same_thread": False},
        )
        cls.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=cls.engine)
        Base.metadata.create_all(bind=cls.engine)

        cls.original_session_local = routes.SessionLocal
        routes.SessionLocal = cls.SessionLocal

        cls._seed_data()

        routes.poi_service.trie = routes.POIService().trie
        routes.poi_service.graph = routes.POIService().graph
        routes.route_service.graph = routes.poi_service.graph

    @classmethod
    def tearDownClass(cls):
        close_all_sessions()
        routes.SessionLocal = cls.original_session_local
        Base.metadata.drop_all(bind=cls.engine)
        cls.engine.dispose()
        cls.temp_dir.cleanup()

    @classmethod
    def _seed_data(cls):
        db = cls.SessionLocal()
        try:
            db.add_all(
                [
                    POI(
                        name="故宫博物院",
                        city="北京",
                        type="景区",
                        latitude=39.9163,
                        longitude=116.3972,
                        floor=1,
                        description="北京市中心的帝制建筑群，适合历史文化体验。",
                    ),
                    POI(
                        name="北京动物园",
                        city="北京",
                        type="动物园",
                        latitude=39.9389,
                        longitude=116.3390,
                        floor=1,
                        description="适合休闲散步，也适合亲子活动。",
                    ),
                    POI(
                        name="颐和园",
                        city="北京",
                        type="公园",
                        latitude=39.9997,
                        longitude=116.2755,
                        floor=1,
                        description="皇家园林，适合自然风光与休闲体验。",
                    ),
                ]
            )
            db.commit()
        finally:
            db.close()

    def setUp(self):
        routes.poi_service.trie = routes.POIService().trie
        routes.poi_service.graph = routes.POIService().graph
        routes.route_service.graph = routes.poi_service.graph

    def test_generate_trip_returns_structured_plan(self):
        db = self.SessionLocal()
        try:
            payload = routes.generate_trip(
                city="北京",
                start_date="2026-05-10",
                end_date="2026-05-12",
                travel_days=3,
                transportation="公共交通",
                accommodation="舒适型酒店",
                preferences=["历史文化", "休闲"],
                free_text_input="节奏放松",
                db=db,
            )
        finally:
            db.close()

        self.assertTrue(payload["success"])
        self.assertEqual(payload["data"]["city"], "北京")
        self.assertEqual(len(payload["data"]["days"]), 3)
        self.assertIn("overall_suggestions", payload["data"])
        self.assertGreater(payload["data"]["budget"]["total"], 0)
        self.assertEqual(payload["data"]["days"][0]["attractions"][0]["name"], "故宫博物院")
        self.assertTrue(payload["data"]["content_sources"])
        self.assertTrue(payload["data"]["recommendation_reasons"])
        self.assertTrue(payload["data"]["days"][0]["attractions"][0]["recommendation_reasons"])
        self.assertEqual(payload["data"]["days"][0]["attractions"][0]["content_sources"][0]["source_label"], "小红书公开内容")

    def test_route_endpoint_prefers_amap_payload_shape(self):
        fake_amap_result = {
            "success": True,
            "distance": 4500,
            "duration": 900,
            "steps": [
                {"lat": 39.9163, "lng": 116.3972, "action": "开始"},
                {"lat": 39.9280, "lng": 116.3680, "action": "向西北行驶"},
                {"lat": 39.9389, "lng": 116.3390, "action": "到达"},
            ],
        }

        with patch.object(routes.route_service.amap_service, "get_route_via_amap", return_value=fake_amap_result):
            db = self.SessionLocal()
            try:
                payload = routes.find_route(1, 2, db)
            finally:
                db.close()

        self.assertEqual(payload["source"], "amap")
        self.assertGreaterEqual(len(payload["path_nodes"]), 2)
        self.assertEqual(payload["start_poi"]["name"], "故宫博物院")
        self.assertEqual(payload["end_poi"]["name"], "北京动物园")

    def test_trip_chat_uses_trip_context(self):
        trip_plan = {
            "city": "北京",
            "start_date": "2026-05-10",
            "end_date": "2026-05-12",
            "overall_suggestions": "优先选择历史文化与休闲体验。",
            "budget": {
                "total_attractions": 210,
                "total_hotels": 1080,
                "total_meals": 360,
                "total_transportation": 120,
                "total": 1770,
            },
            "days": [
                {
                    "date": "2026-05-10",
                    "day_index": 0,
                    "description": "第 1 天重点安排：故宫博物院",
                    "transportation": "公共交通",
                    "accommodation": "舒适型酒店",
                    "attractions": [
                        {"name": "故宫博物院"},
                    ],
                    "meals": [],
                }
            ],
            "weather_info": [],
        }

        payload = routes.ask_trip_chat(
            TripChatRequest(
                message="这份行程预算合理吗？",
                trip_plan=trip_plan,
                history=[],
            )
        )
        self.assertTrue(payload.success)
        self.assertIn("预算", payload.reply)
        self.assertIn("北京", payload.reply)

    def test_xhs_content_service_falls_back_to_builtin_samples(self):
        service = XHSContentService()
        with patch.object(service, "_load_external_candidates", return_value=[]):
            bundle = service.enrich_trip_plan(
                city="北京",
                preferences=["历史文化"],
                pois=[type("PoiStub", (), {"name": "故宫博物院"})()],
            )

        self.assertTrue(bundle["uses_fallback"])
        self.assertTrue(bundle["notes"])
        self.assertEqual(bundle["sources"][0]["origin"], "local_sample")


if __name__ == "__main__":
    unittest.main()
