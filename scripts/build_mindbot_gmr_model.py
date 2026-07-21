#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from m_c_video_to_robot.build_model import build_model  # noqa: E402
from m_c_video_to_robot.paths import relative_to_repo  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description="Build the generated MindBot model used by GMR.")
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()
    model_path = build_model(force=args.force)
    print(relative_to_repo(model_path))


if __name__ == "__main__":
    main()
