from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.algorithms.coordinates import wgs84_to_gcj02
from app.db.init_db import create_all
from app.seed.sample_data import BUPT_SHAHE_CENTER
from app.seed.seed_all import seed_demo_data
from app.services import amap_route_service, route_service
from app.services.amap_route_service import plan_amap_walking_route


def test_amap_walking_route_converts_polyline_back_to_wgs84(monkeypatch) -> None:
    start_lng, start_lat = BUPT_SHAHE_CENTER
    end_lng, end_lat = start_lng + 0.001, start_lat + 0.001
    start_gcj = wgs84_to_gcj02(start_lng, start_lat)
    end_gcj = wgs84_to_gcj02(end_lng, end_lat)
    calls = []

    def fake_get(url, params, timeout):
        calls.append({"url": url, "params": params, "timeout": timeout})
        return FakeResponse(
            {
                "status": "1",
                "route": {
                    "paths": [
                        {
                            "distance": "188",
                            "duration": "162",
                            "steps": [
                                {
                                    "instruction": "沿校园路步行",
                                    "distance": "188",
                                    "duration": "162",
                                    "polyline": f"{start_gcj[0]},{start_gcj[1]};{end_gcj[0]},{end_gcj[1]}",
                                }
                            ],
                        }
                    ]
                },
            }
        )

    monkeypatch.setattr(amap_route_service.httpx, "get", fake_get)

    route = plan_amap_walking_route("secret-key", start_lng, start_lat, end_lng, end_lat)

    assert calls[0]["url"] == amap_route_service.AMAP_WALKING_ROUTE_ENDPOINT
    assert calls[0]["params"]["origin"] == f"{start_gcj[0]},{start_gcj[1]}"
    assert route["distance"] == 188
    assert route["duration"] == 162
    assert route["steps"][0]["text"] == "沿校园路步行"
    assert abs(route["path"][0][0] - start_lng) < 0.00002
    assert abs(route["path"][-1][1] - end_lat) < 0.00002


def test_route_service_auto_uses_amap_walking_when_key_exists(monkeypatch) -> None:
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    create_all(engine)
    monkeypatch.setattr(route_service.settings, "amap_web_api_key", "secret-key")

    def fake_plan_amap_walking_route(**kwargs):
        return {
            "distance": 123,
            "duration": 111,
            "path": [[kwargs["start_lng"], kwargs["start_lat"]], [kwargs["end_lng"], kwargs["end_lat"]]],
            "steps": [{"text": "真实步行路线", "distance": 123}],
            "algorithm_trace": {
                "stage": "stage-21-real-route-planning",
                "algorithm": "AMap Web Service walking route",
                "topology_source": "AMap walking route service",
            },
        }

    monkeypatch.setattr(route_service, "plan_amap_walking_route", fake_plan_amap_walking_route)

    with Session(engine) as session:
        seed_demo_data(session)
        route = route_service.plan_route_from_db(
            session,
            {
                "start_lng": BUPT_SHAHE_CENTER[0],
                "start_lat": BUPT_SHAHE_CENTER[1],
                "end_lng": BUPT_SHAHE_CENTER[0] + 0.001,
                "end_lat": BUPT_SHAHE_CENTER[1] + 0.001,
                "mode": "walk",
                "route_source": "auto",
            },
        )

    assert route["route_source"] == "amap_walking"
    assert route["distance"] == 123
    assert route["algorithm_trace"]["topology_source"] == "AMap walking route service"


class FakeResponse:
    def __init__(self, payload):
        self.payload = payload

    def raise_for_status(self) -> None:
        return None

    def json(self):
        return self.payload
