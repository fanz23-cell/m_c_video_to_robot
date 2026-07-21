#!/usr/bin/env python3
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]


@dataclass(frozen=True)
class RequiredAsset:
    rel_path: str
    source: str
    next_command: str


ASSETS = [
    RequiredAsset(
        "third_party/GVHMR/inputs/checkpoints/body_models/smplx/SMPLX_NEUTRAL.npz",
        "Register and download SMPL-X from https://smpl-x.is.tue.mpg.de/",
        "./.venv-tools/bin/python scripts/check_gvhmr_assets.py",
    ),
    RequiredAsset(
        "third_party/GVHMR/inputs/checkpoints/body_models/smpl/SMPL_NEUTRAL.pkl",
        "Register and download SMPL from https://smpl.is.tue.mpg.de/",
        "./.venv-tools/bin/python scripts/check_gvhmr_assets.py",
    ),
    RequiredAsset(
        "third_party/GVHMR/inputs/checkpoints/gvhmr/gvhmr_siga24_release.ckpt",
        "GVHMR official Google Drive listed in third_party/GVHMR/docs/INSTALL.md",
        "./scripts/extract_human_motion.sh --video data/input_videos/test.mp4 --static-camera",
    ),
    RequiredAsset(
        "third_party/GVHMR/inputs/checkpoints/hmr2/epoch=10-step=25000.ckpt",
        "GVHMR official Google Drive listed in third_party/GVHMR/docs/INSTALL.md",
        "./scripts/extract_human_motion.sh --video data/input_videos/test.mp4 --static-camera",
    ),
    RequiredAsset(
        "third_party/GVHMR/inputs/checkpoints/vitpose/vitpose-h-multi-coco.pth",
        "GVHMR official Google Drive listed in third_party/GVHMR/docs/INSTALL.md",
        "./scripts/extract_human_motion.sh --video data/input_videos/test.mp4 --static-camera",
    ),
    RequiredAsset(
        "third_party/GVHMR/inputs/checkpoints/yolo/yolov8x.pt",
        "GVHMR official Google Drive listed in third_party/GVHMR/docs/INSTALL.md",
        "./scripts/extract_human_motion.sh --video data/input_videos/test.mp4 --static-camera",
    ),
    RequiredAsset(
        "third_party/GMR/assets/body_models/smplx/SMPLX_NEUTRAL.pkl",
        "Register and download SMPL-X from https://smpl-x.is.tue.mpg.de/",
        "./scripts/retarget_to_mindbot.sh --gvhmr-output outputs/test/gvhmr/test/hmr4d_results.pt",
    ),
]


def main() -> None:
    missing = [asset for asset in ASSETS if not (REPO_ROOT / asset.rel_path).exists()]
    if not missing:
        print("[OK] Required GVHMR/GMR model assets are present.")
        return
    print("[ERROR] Missing licensed model/checkpoint files:\n")
    for asset in missing:
        path = Path(asset.rel_path)
        print(f"- file: {path.name}")
        print(f"  directory: {path.parent.as_posix()}")
        print(f"  source: {asset.source}")
        print(f"  after download: {asset.next_command}")
    raise SystemExit(1)


if __name__ == "__main__":
    main()
