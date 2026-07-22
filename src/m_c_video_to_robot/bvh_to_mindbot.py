from __future__ import annotations

import argparse
from pathlib import Path

from .bvh_loader import BVH_COORDINATE_TRANSFORMS, load_bvh_human_frames
from .retarget_core import WAIST_MODE_CHOICES, retarget_human_frames_to_mindbot
from .robot_asset import ROBOT_NAME


def retarget_bvh_to_mindbot(args: argparse.Namespace) -> dict[str, Path]:
    start = max(args.start_frame, 0)
    human_frames, fps, bvh_report = load_bvh_human_frames(
        args.bvh,
        target_fps=float(args.target_fps),
        scale=float(args.scale),
        coordinate_mode=args.coordinate_mode,
        start_frame=start,
        end_frame=args.end_frame,
    )
    return retarget_human_frames_to_mindbot(
        human_frames=human_frames,
        fps=fps,
        output_dir=args.output_dir,
        source_kind="bvh",
        source_motion_file=args.bvh,
        source_video=None,
        actual_human_height=None,
        waist_mode=args.waist_mode,
        rebuild_model=args.rebuild_model,
        preview=args.preview,
        verbose=args.verbose,
        frame_start=start,
        frame_end=args.end_frame,
        source_report=bvh_report,
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Retarget BVH skeleton motion to MindBot joint motion.")
    parser.add_argument("--bvh", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    parser.add_argument("--robot", default=ROBOT_NAME, choices=[ROBOT_NAME])
    parser.add_argument("--target-fps", type=float, default=30.0)
    parser.add_argument("--start-frame", type=int, default=0)
    parser.add_argument("--end-frame", type=int, default=None)
    parser.add_argument("--scale", type=float, default=0.01, help="BVH position scale; use 0.01 for centimeters to meters.")
    parser.add_argument(
        "--coordinate-mode",
        choices=tuple(BVH_COORDINATE_TRANSFORMS.keys()),
        default="y_up_z_forward",
        help="How to map BVH axes into the human frame used by this project.",
    )
    parser.add_argument(
        "--waist-mode",
        choices=WAIST_MODE_CHOICES,
        default="torso_heading",
        help="How to drive waist_joint. The default tracks smoothed shoulder/hip torso heading.",
    )
    parser.add_argument("--rebuild-model", action="store_true")
    parser.add_argument("--preview", action=argparse.BooleanOptionalAction, default=True)
    parser.add_argument("--verbose", action="store_true")
    return parser.parse_args()


def main() -> None:
    retarget_bvh_to_mindbot(parse_args())


if __name__ == "__main__":
    main()
