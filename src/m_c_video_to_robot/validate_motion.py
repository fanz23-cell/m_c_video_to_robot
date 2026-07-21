from __future__ import annotations

import argparse
import json
from pathlib import Path

from .limits import validate_motion
from .motion_format import load_motion
from .robot_asset import load_official_spec


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate a MindBot motion bundle.")
    parser.add_argument("--motion", required=True, type=Path)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    motion = load_motion(args.motion)
    spec = load_official_spec()
    result = validate_motion(
        motion["joint_names"],
        motion["joint_positions"],
        motion["timestamps"],
        spec.joint_limits,
    )
    print(json.dumps(result, indent=2, sort_keys=True))
    if not result["ok"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
