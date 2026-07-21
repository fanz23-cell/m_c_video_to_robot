from __future__ import annotations

import shutil
from pathlib import Path
import xml.etree.ElementTree as ET

from .paths import repo_path
from .robot_asset import CONTROLLED_JOINT_NAMES, find_official_urdf


KEEP_FIXED_JOINTS = ("left_arm_tcp_joint", "right_arm_tcp_joint")


def _mesh_filename(mesh) -> str | None:
    filename = mesh.attrib.get("filename")
    if not filename:
        return None
    if filename.startswith("package://"):
        return filename.removeprefix("package://").lstrip("/")
    return filename


def _copy_meshes(root: ET.Element, source_dir: Path, output_dir: Path) -> None:
    mesh_dir = output_dir / "meshes"
    mesh_dir.mkdir(parents=True, exist_ok=True)
    for mesh in root.findall(".//mesh"):
        filename = _mesh_filename(mesh)
        if not filename:
            continue
        source = source_dir / filename
        if not source.exists():
            source = source_dir / "meshes" / Path(filename).name
        if source.exists():
            shutil.copy2(source, mesh_dir / source.name)
            mesh.set("filename", f"meshes/{source.name}")


def _filter_urdf(root: ET.Element) -> None:
    keep_joint_names = set(CONTROLLED_JOINT_NAMES) | set(KEEP_FIXED_JOINTS)
    keep_links = {"base_link"}
    changed = True
    while changed:
        changed = False
        for joint in root.findall("joint"):
            if joint.attrib.get("name") not in keep_joint_names:
                continue
            parent = joint.find("parent").attrib["link"]
            child = joint.find("child").attrib["link"]
            if parent in keep_links and child not in keep_links:
                keep_links.add(child)
                changed = True

    for joint in list(root.findall("joint")):
        parent = joint.find("parent").attrib["link"]
        child = joint.find("child").attrib["link"]
        if joint.attrib.get("name") not in keep_joint_names or parent not in keep_links or child not in keep_links:
            root.remove(joint)
    for link in list(root.findall("link")):
        if link.attrib.get("name") not in keep_links:
            root.remove(link)


def _try_write_mujoco_xml(urdf_path: Path, xml_path: Path) -> Path | None:
    try:
        import mujoco as mj

        model = mj.MjModel.from_xml_path(str(urdf_path))
        mj.mj_saveLastXML(str(xml_path), model)
        return xml_path
    except Exception as exc:
        note = xml_path.with_suffix(".conversion_failed.txt")
        note.write_text(f"MuJoCo XML conversion failed:\n{exc}\n", encoding="utf-8")
        return None


def build_model(*, force: bool = False, output_dir: Path | None = None) -> Path:
    source_urdf = find_official_urdf()
    output_dir = repo_path("build", "mindbot_gmr") if output_dir is None else output_dir
    output_dir.mkdir(parents=True, exist_ok=True)
    output_urdf = output_dir / "mindbot.urdf"
    output_xml = output_dir / "mindbot.xml"
    if output_xml.exists() and not force:
        return output_xml
    if output_urdf.exists() and not force:
        return output_urdf

    tree = ET.parse(source_urdf)
    root = tree.getroot()
    root.set("name", "mindbot_dual_arm")
    _filter_urdf(root)
    _copy_meshes(root, source_urdf.parent, output_dir)
    tree.write(output_urdf, encoding="utf-8", xml_declaration=True)
    return _try_write_mujoco_xml(output_urdf, output_xml) or output_urdf
