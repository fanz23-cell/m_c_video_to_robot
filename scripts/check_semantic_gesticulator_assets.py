from __future__ import annotations

import argparse
from pathlib import Path


def _default_sg_root() -> Path:
    return Path("third_party") / "Semantic-Gesticulator-Official" / "SG_code"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Check optional Semantic-Gesticulator files.")
    parser.add_argument("--sg-root", type=Path, default=_default_sg_root())
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    root = args.sg_root
    required_files = [
        root / "generate_gestures.py",
        root / "generate_semantic_gestures.py",
        root / "requirements.txt",
        root / "pretrained_models" / "rqvae.pt",
        root / "pretrained_models" / "gpt_0.pt",
        root / "pretrained_models" / "gpt_1.pt",
        root / "pretrained_models" / "gpt_2.pt",
        root / "pretrained_models" / "gpt_3.pt",
        root / "Data" / "SG_processed" / "audio_feature_scaler.sav",
        root / "Data" / "SG_processed" / "motion_data_template.pkl",
        root / "Data" / "SG_processed" / "config.json",
        root / "Data" / "SG_processed" / "body_scaler.sav",
        root / "SG_pipeline" / "all_mocap_extracted_new.npz",
    ]
    required_dirs = [
        root / "retrieval_model",
    ]

    missing = [path for path in required_files if not path.is_file()]
    missing.extend(path for path in required_dirs if not path.is_dir())
    if not missing:
        print("[OK] Semantic-Gesticulator code and model assets are present.")
        return

    print("[MISSING] Semantic-Gesticulator is not fully ready.")
    for path in missing:
        print(f"- {path}")
    print()
    print("Run ./scripts/setup_semantic_gesticulator.sh for code/dependencies, then download official upstream assets:")
    print("https://github.com/LuMen-ze/Semantic-Gesticulator-Official")


if __name__ == "__main__":
    main()
