import os
import json
import sys
import tempfile
import unittest
import subprocess
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
from scripts.fetch_tripstar_xhs_bundle import _pick_query_city


class TravelApiFlowTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp_dir = tempfile.TemporaryDirectory()
        cls.db_path = Path(cls.temp_dir.name) / "test_travel_agent.db"
        cls.runtime_xhs_notes_path = Path(cls.temp_dir.name) / "runtime_xhs_notes.json"
        cls.runtime_xhs_meta_path = Path(cls.temp_dir.name) / "runtime_xhs_notes.meta.json"
        cls.engine = create_engine(
            f"sqlite:///{cls.db_path}",
            connect_args={"check_same_thread": False},
        )
        cls.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=cls.engine)
        Base.metadata.create_all(bind=cls.engine)

        cls.original_session_local = routes.SessionLocal
        cls.original_xhs_sample_notes_path = routes.xhs_content_service.settings.xhs_sample_notes_path
        routes.SessionLocal = cls.SessionLocal
        routes.xhs_content_service.settings.xhs_sample_notes_path = ""

        cls._seed_data()

        routes.poi_service.trie = routes.POIService().trie
        routes.poi_service.graph = routes.POIService().graph
        routes.route_service.graph = routes.poi_service.graph
        routes.xhs_content_service.runtime_notes_path = cls.runtime_xhs_notes_path
        routes.xhs_content_service.runtime_meta_path = cls.runtime_xhs_meta_path
        routes.xhs_content_service.clear_imported_notes()

    @classmethod
    def tearDownClass(cls):
        close_all_sessions()
        routes.SessionLocal = cls.original_session_local
        routes.xhs_content_service.settings.xhs_sample_notes_path = cls.original_xhs_sample_notes_path
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
        routes.xhs_content_service.runtime_notes_path = self.runtime_xhs_notes_path
        routes.xhs_content_service.runtime_meta_path = self.runtime_xhs_meta_path
        routes.xhs_content_service.clear_imported_notes()
        routes.xhs_live_fetch_service.content_service.runtime_notes_path = self.runtime_xhs_notes_path
        routes.xhs_live_fetch_service.content_service.runtime_meta_path = self.runtime_xhs_meta_path
        routes.xhs_live_fetch_service.settings.xhs_cookie = ""
        routes.xhs_live_fetch_service.settings.xhs_rap_param = ""

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
        service.runtime_notes_path = self.runtime_xhs_notes_path
        service.runtime_meta_path = self.runtime_xhs_meta_path
        with patch.object(service, "_load_external_candidates", return_value=[]):
            bundle = service.enrich_trip_plan(
                city="北京",
                preferences=["历史文化"],
                pois=[type("PoiStub", (), {"name": "故宫博物院"})()],
            )

        self.assertTrue(bundle["uses_fallback"])
        self.assertTrue(bundle["notes"])
        self.assertEqual(bundle["sources"][0]["origin"], "local_sample")

    def test_imported_xhs_notes_take_priority_over_builtin(self):
        imported_notes = [
            {
                "id": "external-beijing-gugong",
                "title": "真实导入的故宫样例",
                "city": "北京",
                "poi_name": "故宫博物院",
                "tags": ["历史文化"],
                "highlights": ["导入内容优先命中故宫。"],
                "excerpt": "这是外部导入内容。",
            }
        ]

        import_payload = routes.import_xhs_content_source(
            routes.XHSImportPayload(source_name="beijing.json", payload=imported_notes)
        )
        self.assertTrue(import_payload["success"])
        self.assertEqual(import_payload["data"]["active_source"], "runtime_import")
        self.assertEqual(import_payload["data"]["note_count"], 1)

        db = self.SessionLocal()
        try:
            payload = routes.generate_trip(
                city="北京",
                start_date="2026-05-10",
                end_date="2026-05-12",
                travel_days=2,
                transportation="公共交通",
                accommodation="舒适型酒店",
                preferences=["历史文化"],
                free_text_input="",
                db=db,
            )
        finally:
            db.close()

        first_note = payload["data"]["days"][0]["attractions"][0]["travel_notes"][0]
        self.assertEqual(first_note["title"], "真实导入的故宫样例")
        self.assertEqual(first_note["origin"], "external")

    def test_xhs_content_source_status_reports_builtin_after_clear(self):
        routes.import_xhs_content_source(
            routes.XHSImportPayload(
                source_name="temp.json",
                payload=[{"title": "外部样例", "city": "北京", "poi_name": "故宫博物院"}],
            )
        )
        cleared = routes.clear_xhs_content_source_import()

        self.assertTrue(cleared["success"])
        self.assertEqual(cleared["data"]["active_source"], "builtin_fallback")
        self.assertTrue(cleared["data"]["uses_builtin_fallback"])

    def test_refresh_xhs_content_source_uses_tripstar_bridge(self):
        routes.xhs_live_fetch_service.settings.xhs_cookie = "a1=test-cookie"
        helper_payload = {
            "success": True,
            "query": "北京 历史文化 旅游 景点攻略",
            "raw_note_count": 1,
            "data": {
                "city": "北京",
                "search_response": {
                    "data": {
                        "items": [
                            {
                                "id": "live-note-1",
                                "model_type": "note",
                                "note_card": {"display_title": "故宫实时刷新内容"},
                            }
                        ]
                    }
                },
                "detail_response": {
                    "data": {
                        "items": [
                            {
                                "note_card": {
                                    "note_id": "live-note-1",
                                    "title": "故宫实时刷新内容",
                                    "desc": "这是通过 TripStar bridge 刷新的内容。",
                                    "city": "北京",
                                    "poi_name": "故宫博物院",
                                }
                            }
                        ]
                    }
                },
            },
        }

        with patch("app.services.xhs_live_fetch_service.subprocess.run") as mocked_run:
            mocked_run.return_value = subprocess.CompletedProcess(
                args=["python"],
                returncode=0,
                stdout=json.dumps(helper_payload, ensure_ascii=False),
                stderr="",
            )
            payload = routes.refresh_xhs_content_source(
                routes.XHSRefreshPayload(city="北京", keywords="历史文化", max_items=1)
            )

        self.assertTrue(payload["success"])
        self.assertEqual(payload["meta"]["raw_note_count"], 1)
        bundle = routes.xhs_content_service.enrich_trip_plan(
            city="北京",
            preferences=["历史文化"],
            pois=[type("PoiStub", (), {"name": "故宫博物院"})()],
        )
        self.assertEqual(bundle["notes"][0]["title"], "故宫实时刷新内容")

    def test_build_query_candidates_prefers_city_and_pois(self):
        from scripts.fetch_tripstar_xhs_bundle import _build_query_candidates

        candidates = _build_query_candidates("中国-北京", "历史文化 休闲", ["故宫博物院", "颐和园"])
        self.assertEqual(candidates[0], "北京 历史文化 休闲 旅游 景点攻略")
        self.assertIn("北京 故宫博物院 颐和园 攻略", candidates)

    def test_is_note_like_item_accepts_note_variants(self):
        from scripts.fetch_tripstar_xhs_bundle import _is_note_like_item

        self.assertTrue(_is_note_like_item({"model_type": "note_v2", "id": "1"}))
        self.assertTrue(_is_note_like_item({"id": "2", "note_card": {"display_title": "故宫攻略"}}))
        self.assertFalse(_is_note_like_item({"model_type": "user", "id": "3"}))

    def test_live_fetch_service_parses_noisy_helper_stdout(self):
        routes.xhs_live_fetch_service.settings.xhs_cookie = "a1=test-cookie"
        helper_payload = {
            "success": True,
            "query": "北京 旅游 景点攻略",
            "raw_note_count": 1,
            "data": {
                "city": "北京",
                "search_response": {
                    "data": {
                        "items": [
                            {
                                "id": "noisy-note-1",
                                "model_type": "note",
                                "note_card": {"display_title": "日志污染下的故宫内容"},
                            }
                        ]
                    }
                },
                "detail_response": {
                    "data": {
                        "items": [
                            {
                                "note_card": {
                                    "note_id": "noisy-note-1",
                                    "title": "日志污染下的故宫内容",
                                    "desc": "即使前面有日志，也应该能解析 JSON。",
                                    "city": "北京",
                                    "poi_name": "故宫博物院",
                                }
                            }
                        ]
                    }
                },
            },
        }
        noisy_stdout = "[XHS_SIGN] signature JS engine loaded\n" + json.dumps(helper_payload, ensure_ascii=False)

        with patch("app.services.xhs_live_fetch_service.subprocess.run") as mocked_run:
            mocked_run.return_value = subprocess.CompletedProcess(
                args=["python"],
                returncode=0,
                stdout=noisy_stdout,
                stderr="",
            )
            refreshed = routes.xhs_live_fetch_service.refresh_from_tripstar(city="北京", keywords="", max_items=1)

        self.assertEqual(refreshed["query"], "北京 旅游 景点攻略")
        self.assertEqual(refreshed["status"]["active_source"], "runtime_import")

    def test_live_fetch_service_reports_empty_search_results_cleanly(self):
        routes.xhs_live_fetch_service.settings.xhs_cookie = "a1=test-cookie"
        helper_payload = {
            "success": True,
            "query": "北京 旅游 景点攻略",
            "raw_note_count": 0,
            "data": {
                "city": "北京",
                "search_response": {"data": {"items": []}},
                "detail_response": {"data": {"items": []}},
            },
        }

        with patch("app.services.xhs_live_fetch_service.subprocess.run") as mocked_run:
            mocked_run.return_value = subprocess.CompletedProcess(
                args=["python"],
                returncode=0,
                stdout=json.dumps(helper_payload, ensure_ascii=False),
                stderr="",
            )
            with self.assertRaises(Exception) as ctx:
                routes.xhs_live_fetch_service.refresh_from_tripstar(city="北京", keywords="", max_items=1)

        self.assertIn("没有返回可用笔记", str(ctx.exception))

    def test_refresh_trip_http_error_contains_structured_detail(self):
        routes.xhs_live_fetch_service.settings.xhs_cookie = "a1=test-cookie"
        helper_payload = {
            "success": True,
            "query": "北京 攻略",
            "raw_note_count": 0,
            "data": {
                "city": "北京",
                "query_candidates": ["北京 攻略"],
                "search_item_count": 2,
                "search_model_types": ["user", "ad"],
                "search_item_preview": [{"id": "1", "model_type": "user", "title": "", "keys": ["id", "model_type"]}],
                "search_response": {"data": {"items": []}},
                "detail_response": {"data": {"items": []}},
            },
        }

        trip_plan = {"city": "北京", "days": [], "request_summary": {"preferences": []}}
        with patch("app.services.xhs_live_fetch_service.subprocess.run") as mocked_run:
            mocked_run.return_value = subprocess.CompletedProcess(
                args=["python"],
                returncode=0,
                stdout=json.dumps(helper_payload, ensure_ascii=False),
                stderr="",
            )
            with self.assertRaises(Exception) as ctx:
                routes.refresh_xhs_trip_content(
                    routes.XHSRefreshTripPayload(trip_plan=trip_plan, city="北京", keywords="", max_items=1)
                )

        detail = ctx.exception.detail
        self.assertIsInstance(detail, dict)
        self.assertEqual(detail["search_item_count"], 2)
        self.assertEqual(detail["search_model_types"], ["user", "ad"])

    def test_live_fetch_service_writes_debug_log(self):
        routes.xhs_live_fetch_service.settings.xhs_cookie = "a1=test-cookie"
        routes.xhs_live_fetch_service.settings.xhs_rap_param = "rap-debug-token"
        routes.xhs_live_fetch_service.debug_dir = Path(self.temp_dir.name) / "xhs_debug"
        routes.xhs_live_fetch_service.latest_debug_file = routes.xhs_live_fetch_service.debug_dir / "latest.json"
        helper_payload = {
            "success": True,
            "query": "北京 攻略",
            "raw_note_count": 0,
            "data": {
                "city": "北京",
                "query_candidates": ["北京 攻略"],
                "request_debug": {
                    "search": {
                        "url": "https://edith.xiaohongshu.com/api/sns/web/v1/search/notes",
                        "method": "POST",
                        "header_subset": {"user-agent": "Mozilla/5.0 ... Chrome/148.0.0.0", "x-rap-param": "rap-debug-token"},
                        "cookie_presence": {"a1": True, "web_session": False},
                        "cookie_preview": {"a1": "test...okie (11 chars)"},
                        "body": "{\"keyword\":\"北京 攻略\"}",
                    },
                    "detail_requests": [],
                },
                "search_item_count": 1,
                "search_model_types": ["user"],
                "search_item_preview": [{"id": "1", "model_type": "user", "title": "", "keys": ["id", "model_type"]}],
                "search_response": {"data": {"items": []}},
                "detail_response": {"data": {"items": []}},
            },
        }

        with patch("app.services.xhs_live_fetch_service.subprocess.run") as mocked_run:
            mocked_run.return_value = subprocess.CompletedProcess(
                args=["python"],
                returncode=0,
                stdout=json.dumps(helper_payload, ensure_ascii=False),
                stderr="",
            )
            with self.assertRaises(Exception):
                routes.xhs_live_fetch_service.refresh_from_tripstar(city="北京", keywords="", max_items=1)

        latest = routes.xhs_live_fetch_service.get_latest_debug_log()
        self.assertTrue(latest)
        self.assertEqual(latest["parsed_response_summary"]["search_item_count"], 1)
        self.assertEqual(latest["request"]["cookie"], "<masked:14 chars>")
        self.assertEqual(
            latest["parsed_response_summary"]["request_debug"]["search"]["url"],
            "https://edith.xiaohongshu.com/api/sns/web/v1/search/notes",
        )

    def test_refresh_xhs_content_source_requires_cookie(self):
        routes.xhs_live_fetch_service.settings.xhs_cookie = ""
        with self.assertRaises(Exception) as ctx:
            routes.refresh_xhs_content_source(
                routes.XHSRefreshPayload(city="北京", keywords="", max_items=1)
            )
        self.assertIn("小红书 Cookie", str(ctx.exception))

    def test_refresh_xhs_content_source_requires_a1_cookie(self):
        routes.xhs_live_fetch_service.settings.xhs_cookie = "web_session=test-session-only"
        with self.assertRaises(Exception) as ctx:
            routes.refresh_xhs_content_source(
                routes.XHSRefreshPayload(city="北京", keywords="", max_items=1)
            )

        self.assertIn("缺少关键字段：a1", str(ctx.exception))

    def test_refresh_xhs_trip_content_returns_updated_plan(self):
        routes.xhs_live_fetch_service.settings.xhs_cookie = "a1=test-cookie"
        helper_payload = {
            "success": True,
            "query": "北京 历史文化 旅游 景点攻略",
            "raw_note_count": 1,
            "data": {
                "city": "北京",
                "search_response": {
                    "data": {
                        "items": [
                            {
                                "id": "trip-note-1",
                                "model_type": "note",
                                "note_card": {"display_title": "故宫实时更新后的理由"},
                            }
                        ]
                    }
                },
                "detail_response": {
                    "data": {
                        "items": [
                            {
                                "note_card": {
                                    "note_id": "trip-note-1",
                                    "title": "故宫实时更新后的理由",
                                    "desc": "新的实时内容已经回填到当前行程。",
                                    "city": "北京",
                                    "poi_name": "故宫博物院",
                                }
                            }
                        ]
                    }
                },
            },
        }

        trip_plan = {
            "city": "北京",
            "start_date": "2026-05-10",
            "end_date": "2026-05-12",
            "overall_suggestions": "初始建议。",
            "request_summary": {
                "city": "北京",
                "travel_days": 2,
                "transportation": "公共交通",
                "accommodation": "舒适型酒店",
                "preferences": ["历史文化"],
                "free_text_input": "",
                "data_mode": "city_match",
                "data_note": "初始数据说明",
            },
            "days": [
                {
                    "date": "2026-05-10",
                    "day_index": 0,
                    "description": "第 1 天重点安排：故宫博物院",
                    "transportation": "公共交通",
                    "accommodation": "舒适型酒店",
                    "attractions": [
                        {
                            "id": 1,
                            "name": "故宫博物院",
                            "type": "景区",
                            "category": "景区",
                            "address": "北京 · 故宫博物院",
                            "location": {"latitude": 39.9163, "longitude": 116.3972},
                            "latitude": 39.9163,
                            "longitude": 116.3972,
                            "visit_duration": 90,
                            "description": "北京市中心的帝制建筑群，适合历史文化体验。",
                        }
                    ],
                    "meals": [],
                }
            ],
            "weather_info": [],
        }

        with patch("app.services.xhs_live_fetch_service.subprocess.run") as mocked_run:
            mocked_run.return_value = subprocess.CompletedProcess(
                args=["python"],
                returncode=0,
                stdout=json.dumps(helper_payload, ensure_ascii=False),
                stderr="",
            )
            payload = routes.refresh_xhs_trip_content(
                routes.XHSRefreshTripPayload(trip_plan=trip_plan, city="北京", keywords="历史文化", max_items=1)
            )

        self.assertTrue(payload["success"])
        self.assertEqual(payload["data"]["content_sources"][0]["origin"], "external")
        self.assertEqual(payload["data"]["days"][0]["attractions"][0]["travel_notes"][0]["title"], "故宫实时更新后的理由")
        self.assertTrue(payload["data"]["recommendation_reasons"])

    def test_generate_trip_matches_prefixed_city_name(self):
        db = self.SessionLocal()
        try:
            payload = routes.generate_trip(
                city="中国-北京",
                start_date="2026-05-10",
                end_date="2026-05-12",
                travel_days=3,
                transportation="公共交通",
                accommodation="舒适型酒店",
                preferences=["历史文化"],
                free_text_input="",
                db=db,
            )
        finally:
            db.close()

        self.assertEqual(payload["data"]["request_summary"]["data_mode"], "city_match")
        self.assertTrue(payload["data"]["content_sources"])
        self.assertEqual(payload["data"]["content_sources"][0]["origin"], "local_sample")

    def test_refresh_trip_recomputes_city_match_for_prefixed_city(self):
        trip_plan = {
            "city": "中国-北京",
            "start_date": "2026-05-10",
            "end_date": "2026-05-12",
            "overall_suggestions": "初始建议。",
            "request_summary": {
                "city": "中国-北京",
                "travel_days": 1,
                "transportation": "公共交通",
                "accommodation": "舒适型酒店",
                "preferences": ["历史文化"],
                "free_text_input": "",
                "data_mode": "local_sample",
                "data_note": "旧说明",
            },
            "days": [
                {
                    "date": "2026-05-10",
                    "day_index": 0,
                    "description": "第 1 天重点安排：故宫博物院",
                    "transportation": "公共交通",
                    "accommodation": "舒适型酒店",
                    "attractions": [
                        {
                            "id": 1,
                            "name": "故宫博物院",
                            "type": "景区",
                            "category": "景区",
                            "address": "中国-北京 · 故宫博物院",
                            "location": {"latitude": 39.9163, "longitude": 116.3972},
                            "latitude": 39.9163,
                            "longitude": 116.3972,
                            "visit_duration": 90,
                            "description": "北京市中心的帝制建筑群，适合历史文化体验。",
                        }
                    ],
                    "meals": [],
                }
            ],
            "weather_info": [],
        }

        updated = routes._refresh_trip_plan_xhs_enrichment(trip_plan)
        self.assertEqual(updated["request_summary"]["data_mode"], "city_match")

    def test_pick_query_city_prefers_core_city_segment(self):
        self.assertEqual(_pick_query_city("中国-北京"), "北京")
        self.assertEqual(_pick_query_city("北京/中国"), "北京")

    def test_import_tripstar_style_search_bundle(self):
        payload = {
            "city": "北京",
            "search_response": {
                "data": {
                    "items": [
                        {
                            "id": "note-123",
                            "model_type": "note",
                            "note_card": {
                                "display_title": "故宫打卡半日路线",
                                "cover": {"url_default": "https://example.com/gugong.jpg"},
                                "user": {"nickname": "Alice"},
                            },
                        }
                    ]
                }
            },
            "detail_response": {
                "data": {
                    "items": [
                        {
                            "note_card": {
                                "note_id": "note-123",
                                "title": "故宫打卡半日路线",
                                "desc": "建议上午入园，适合历史文化体验。",
                                "city": "北京",
                                "poi_name": "故宫博物院",
                            }
                        }
                    ]
                }
            },
        }

        imported = routes.import_xhs_content_source(
            routes.XHSImportPayload(source_name="tripstar_bundle.json", payload=payload)
        )

        self.assertTrue(imported["success"])
        self.assertEqual(imported["data"]["format_kind"], "xhs_search_items")

        bundle = routes.xhs_content_service.enrich_trip_plan(
            city="北京",
            preferences=["历史文化"],
            pois=[type("PoiStub", (), {"name": "故宫博物院"})()],
        )
        self.assertEqual(bundle["notes"][0]["title"], "故宫打卡半日路线")
        self.assertEqual(bundle["notes"][0]["excerpt"], "建议上午入园，适合历史文化体验。")

    def test_import_third_party_intermediate_payload(self):
        payload = {
            "source_label": "第三方采集结果",
            "items": [
                {
                    "title": "颐和园慢游建议",
                    "city": "北京",
                    "poi_name": "颐和园",
                    "content": "更适合安排在节奏放松的一天。",
                    "tags": ["休闲", "园林"],
                }
            ],
        }

        imported = routes.import_xhs_content_source(
            routes.XHSImportPayload(source_name="third_party.json", payload=payload)
        )

        self.assertTrue(imported["success"])
        self.assertEqual(imported["data"]["format_kind"], "third_party_items")

        bundle = routes.xhs_content_service.enrich_trip_plan(
            city="北京",
            preferences=["休闲"],
            pois=[type("PoiStub", (), {"name": "颐和园"})()],
        )
        self.assertEqual(bundle["notes"][0]["source_label"], "第三方采集结果")
        self.assertEqual(bundle["notes"][0]["poi_name"], "颐和园")


if __name__ == "__main__":
    unittest.main()
