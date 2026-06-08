import argparse
import sys
from pathlib import Path

if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.core.config import settings
from app.seed.sample_data import BUPT_SHAHE_CENTER
from app.services.amap_route_service import plan_amap_walking_route


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Smoke test AMap walking route without printing the API key.")
    parser.add_argument("--start-lng", type=float, default=BUPT_SHAHE_CENTER[0])
    parser.add_argument("--start-lat", type=float, default=BUPT_SHAHE_CENTER[1])
    parser.add_argument("--end-lng", type=float, default=BUPT_SHAHE_CENTER[0] + 0.003)
    parser.add_argument("--end-lat", type=float, default=BUPT_SHAHE_CENTER[1] + 0.002)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    route = plan_amap_walking_route(
        api_key=settings.amap_web_api_key or "",
        start_lng=args.start_lng,
        start_lat=args.start_lat,
        end_lng=args.end_lng,
        end_lat=args.end_lat,
    )
    print("[amap-route-smoke] source:", route["source"])
    print("[amap-route-smoke] distance:", route["distance"])
    print("[amap-route-smoke] duration:", route["duration"])
    print("[amap-route-smoke] path_points:", len(route["path"]))
    print("[amap-route-smoke] steps:", len(route["steps"]))


if __name__ == "__main__":
    main()
