from __future__ import annotations

from pathlib import Path

from .paths import repo_path
from .robot_asset import ROBOT_NAME, generated_model_path


def register_mindbot(gmr_params, robot_xml: Path, ik_config: Path) -> None:
    """Register MindBot in GMR without editing the upstream params.py file."""

    gmr_params.ROBOT_XML_DICT[ROBOT_NAME] = Path(robot_xml)
    gmr_params.IK_CONFIG_DICT.setdefault("smplx", {})
    gmr_params.IK_CONFIG_DICT["smplx"][ROBOT_NAME] = Path(ik_config)
    gmr_params.ROBOT_BASE_DICT[ROBOT_NAME] = "waist_link"
    gmr_params.VIEWER_CAM_DISTANCE_DICT[ROBOT_NAME] = 1.2


def register_default_mindbot(gmr_params, prefer_xml: bool = True) -> Path:
    robot_model = generated_model_path(prefer_xml=prefer_xml)
    ik_config = repo_path("configs", "smplx_to_mindbot.json")
    register_mindbot(gmr_params, robot_model, ik_config)
    return robot_model
