from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import xml.etree.ElementTree as ET

from .paths import isaac_root, repo_path


ROBOT_NAME = "mindbot_dual_arm"
WAIST_JOINT_NAMES = ("waist_joint",)
LEFT_ARM_JOINT_NAMES = tuple(f"left_arm_joint_{idx}" for idx in range(1, 7))
RIGHT_ARM_JOINT_NAMES = tuple(f"right_arm_joint_{idx}" for idx in range(1, 7))
CONTROLLED_JOINT_NAMES = WAIST_JOINT_NAMES + LEFT_ARM_JOINT_NAMES + RIGHT_ARM_JOINT_NAMES
IGNORED_JOINT_NAMES = ("realsense_pitch_joint",)
LEFT_TCP_LINK = "left_arm_tcp"
RIGHT_TCP_LINK = "right_arm_tcp"

OFFICIAL_URDF_CANDIDATES = (
    "source/mindbot_isaac_sim/mindbot_isaac_sim/assets/data/Robots/MindBotMC1_v0_1/mc1_urdf_v0_1_isaac.urdf",
    "model/MC1_urdf_v0.1/urdf.urdf",
)


@dataclass(frozen=True)
class JointLimit:
    lower: float
    upper: float
    velocity: float
    effort: float


@dataclass(frozen=True)
class JointInfo:
    name: str
    joint_type: str
    parent: str
    child: str
    origin_xyz: tuple[float, float, float]
    origin_rpy: tuple[float, float, float]
    axis_xyz: tuple[float, float, float] | None
    limit: JointLimit | None


@dataclass(frozen=True)
class RobotSpec:
    urdf_path: Path
    joints: dict[str, JointInfo]
    links: tuple[str, ...]

    @property
    def controlled_joint_names(self) -> tuple[str, ...]:
        return CONTROLLED_JOINT_NAMES

    @property
    def joint_limits(self) -> dict[str, JointLimit]:
        return {name: self.joints[name].limit for name in CONTROLLED_JOINT_NAMES if self.joints[name].limit is not None}


def _float_tuple(value: str | None, width: int, default: tuple[float, ...]) -> tuple[float, ...]:
    if value is None:
        return default
    data = tuple(float(part) for part in value.split())
    if len(data) != width:
        raise ValueError(f"Expected {width} floats, got {value!r}")
    return data


def find_official_urdf(root: Path | None = None) -> Path:
    base = isaac_root() if root is None else root
    for candidate in OFFICIAL_URDF_CANDIDATES:
        path = base / candidate
        if path.exists():
            return path
    joined = "\n".join(f"  - ${{MINDBOT_ISAAC_ROOT}}/{candidate}" for candidate in OFFICIAL_URDF_CANDIDATES)
    raise FileNotFoundError(f"Could not find MindBot URDF. Checked:\n{joined}")


def parse_urdf(path: str | Path) -> RobotSpec:
    urdf_path = Path(path)
    root = ET.parse(urdf_path).getroot()
    links = tuple(link.attrib["name"] for link in root.findall("link"))
    joints: dict[str, JointInfo] = {}
    for joint in root.findall("joint"):
        name = joint.attrib["name"]
        origin = joint.find("origin")
        axis = joint.find("axis")
        limit = joint.find("limit")
        limit_info = None
        if limit is not None:
            limit_info = JointLimit(
                lower=float(limit.attrib.get("lower", "-inf")),
                upper=float(limit.attrib.get("upper", "inf")),
                velocity=float(limit.attrib.get("velocity", "inf")),
                effort=float(limit.attrib.get("effort", "inf")),
            )
        joints[name] = JointInfo(
            name=name,
            joint_type=joint.attrib.get("type", ""),
            parent=joint.find("parent").attrib["link"],
            child=joint.find("child").attrib["link"],
            origin_xyz=_float_tuple(origin.attrib.get("xyz") if origin is not None else None, 3, (0.0, 0.0, 0.0)),
            origin_rpy=_float_tuple(origin.attrib.get("rpy") if origin is not None else None, 3, (0.0, 0.0, 0.0)),
            axis_xyz=_float_tuple(axis.attrib.get("xyz"), 3, (0.0, 0.0, 1.0)) if axis is not None else None,
            limit=limit_info,
        )
    return RobotSpec(urdf_path=urdf_path, joints=joints, links=links)


def load_official_spec() -> RobotSpec:
    return parse_urdf(find_official_urdf())


def generated_model_path(prefer_xml: bool = True) -> Path:
    xml_path = repo_path("build", "mindbot_gmr", "mindbot.xml")
    urdf_path = repo_path("build", "mindbot_gmr", "mindbot.urdf")
    if prefer_xml and xml_path.exists():
        return xml_path
    return urdf_path


def assert_expected_controlled_joints(spec: RobotSpec) -> None:
    missing = [name for name in CONTROLLED_JOINT_NAMES if name not in spec.joints]
    if missing:
        raise RuntimeError(f"Official robot asset is missing controlled joints: {missing}")
    for name in CONTROLLED_JOINT_NAMES:
        if spec.joints[name].joint_type != "revolute":
            raise RuntimeError(f"{name} must be revolute, got {spec.joints[name].joint_type!r}")
