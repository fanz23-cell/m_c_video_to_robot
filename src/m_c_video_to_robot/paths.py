from __future__ import annotations

import os
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_ISAAC_ROOT = "../Mind bot Isaac Sim"


def load_dotenv(path: Path | None = None) -> None:
    """Load simple KEY=VALUE lines from .env without adding a dependency."""

    env_path = REPO_ROOT / ".env" if path is None else path
    if not env_path.exists():
        return
    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value


def repo_path(*parts: str | Path) -> Path:
    return REPO_ROOT.joinpath(*parts)


def resolve_from_repo(raw: str | Path) -> Path:
    path = Path(raw)
    if path.is_absolute():
        return path
    return (REPO_ROOT / path).resolve()


def isaac_root() -> Path:
    load_dotenv()
    raw = os.environ.get("MINDBOT_ISAAC_ROOT", DEFAULT_ISAAC_ROOT)
    return resolve_from_repo(raw)


def relative_to_repo(path: str | Path) -> str:
    path = Path(path)
    if not path.is_absolute():
        return path.as_posix()
    try:
        return path.resolve().relative_to(REPO_ROOT).as_posix()
    except ValueError:
        return os.path.relpath(path.resolve(), REPO_ROOT)


def ensure_inside_repo(path: str | Path) -> Path:
    resolved = resolve_from_repo(path)
    try:
        resolved.relative_to(REPO_ROOT)
    except ValueError as exc:
        raise ValueError(f"Path must be inside this repository: {path}") from exc
    return resolved
