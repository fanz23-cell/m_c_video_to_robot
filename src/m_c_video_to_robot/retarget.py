from __future__ import annotations

import argparse
from pathlib import Path

from .paths import repo_path
from .retarget_core import WAIST_MODE_CHOICES, ensure_model_exists as _ensure_model_exists, retarget_human_frames_to_mindbot
from .robot_asset import ROBOT_NAME

def retarget_gvhmr_to_mindbot(args: argparse.Namespace) -> dict[str, Path]:
    from general_motion_retargeting.utils.smpl import get_gvhmr_data_offline_fast, load_gvhmr_pred_file

    body_model_root = Path(args.smplx_body_models) if args.smplx_body_models else repo_path("third_party", "GMR", "assets", "body_models")
    smplx_data, body_model, smplx_output, actual_human_height = load_gvhmr_pred_file(args.gvhmr_output, body_model_root)
    human_frames, aligned_fps = get_gvhmr_data_offline_fast(
        smplx_data,
        body_model,
        smplx_output,
        tgt_fps=args.target_fps,
    )
    start = max(args.start_frame, 0)
    end = len(human_frames) if args.end_frame is None else min(args.end_frame, len(human_frames))
    if start >= end:
        raise ValueError(f"Invalid frame range: start={start}, end={end}")
    return retarget_human_frames_to_mindbot(
        human_frames=human_frames[start:end],
        fps=float(aligned_fps),
        output_dir=args.output_dir,
        source_kind="gvhmr",
        source_motion_file=args.gvhmr_output,
        source_video=args.source_video,
        actual_human_height=float(actual_human_height),
        waist_mode=args.waist_mode,
        rebuild_model=args.rebuild_model,
        preview=args.preview,
        verbose=args.verbose,
        frame_start=start,
        frame_end=end,
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Retarget GVHMR hmr4d_results.pt to MindBot joint motion.")
    parser.add_argument("--gvhmr-output", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    parser.add_argument("--source-video", type=Path, default=None)
    parser.add_argument("--robot", default=ROBOT_NAME, choices=[ROBOT_NAME])
    parser.add_argument("--target-fps", type=int, default=30)
    parser.add_argument("--start-frame", type=int, default=0)
    parser.add_argument("--end-frame", type=int, default=None)
    parser.add_argument("--smplx-body-models", type=Path, default=None)
    parser.add_argument("--rebuild-model", action="store_true")
    parser.add_argument(
        "--waist-mode",
        choices=WAIST_MODE_CHOICES,
        default="torso_heading",
        help="How to drive waist_joint. The default tracks smoothed shoulder/hip torso heading.",
    )
    parser.add_argument("--preview", action=argparse.BooleanOptionalAction, default=True)
    parser.add_argument("--verbose", action="store_true")
    return parser.parse_args()


def main() -> None:
    retarget_gvhmr_to_mindbot(parse_args())


if __name__ == "__main__":
    main()
