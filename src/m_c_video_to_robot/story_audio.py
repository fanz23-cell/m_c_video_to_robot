from __future__ import annotations

import argparse
import shutil
import subprocess
from pathlib import Path


def _read_text(args: argparse.Namespace) -> str:
    if args.text_file:
        return Path(args.text_file).read_text(encoding="utf-8").strip()
    if args.text:
        return str(args.text).strip()
    raise ValueError("Provide --text or --text-file when --audio is not supplied.")


def synthesize_text_to_wav(text: str, output: str | Path, *, voice: str | None = None) -> Path:
    output_path = Path(output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    if not text.strip():
        raise ValueError("Cannot synthesize empty text.")

    for command in ("espeak-ng", "espeak"):
        executable = shutil.which(command)
        if executable is None:
            continue
        cmd = [executable]
        if voice:
            cmd.extend(["-v", voice])
        cmd.extend(["-w", str(output_path), text])
        subprocess.run(cmd, check=True)
        return output_path

    raise RuntimeError(
        "No local text-to-speech command was found. Install espeak-ng, or pass an existing WAV file with --audio."
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Create a WAV narration file from text for Semantic-Gesticulator.")
    parser.add_argument("--text", default="")
    parser.add_argument("--text-file", type=Path, default=None)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--voice", default=None, help="Optional espeak/espeak-ng voice id, for example en-us or zh.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    output = synthesize_text_to_wav(_read_text(args), args.output, voice=args.voice)
    print(output)


if __name__ == "__main__":
    main()
