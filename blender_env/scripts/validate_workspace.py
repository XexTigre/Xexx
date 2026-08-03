from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import bpy


def script_args() -> list[str]:
    if "--" not in sys.argv:
        return []
    return sys.argv[sys.argv.index("--") + 1 :]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args(script_args())

    scene = bpy.context.scene
    required_collections = {
        "00_REFERENCE_LOCKED",
        "10_SOURCE_IMMUTABLE",
        "20_WORKING_COPY",
        "30_RIG_CAGES_ATTACHMENTS",
        "40_EVIDENCE",
        "90_QUARANTINE",
        "99_EXPORT",
    }
    cameras = [obj for obj in bpy.data.objects if obj.name.startswith("AUDIT_CAM_") and obj.type == "CAMERA"]

    checks = {
        "version_4_5_12": bpy.app.version_string.startswith("4.5.12"),
        "unit_system_none": scene.unit_settings.system == "NONE",
        "rotation_degrees": scene.unit_settings.system_rotation == "DEGREES",
        "all_required_collections": required_collections.issubset(set(bpy.data.collections.keys())),
        "twelve_audit_cameras": len(cameras) == 12,
        "origin_exists": "RBX_ORIGIN_GROUND_CENTER" in bpy.data.objects,
        "export_root_exists": "RBX_EXPORT_ROOT" in bpy.data.objects,
        "environment_id": scene.get("environment_id") == "roblox-blender-4.5-lts",
        "one_unit_is_one_stud": scene.get("one_blender_unit_equals_one_stud") is True,
        "avatar_setup_front": scene.get("avatar_setup_front_axis") == "-Z",
        "r15_final_front": scene.get("r15_final_front_axis") == "+Z",
        "manifest_text_exists": "ROBLOX_ENVIRONMENT_MANIFEST.json" in bpy.data.texts,
    }

    report = {
        "schema_version": "1.0.0",
        "status": "PASS" if all(checks.values()) else "FAIL",
        "blend_file": bpy.data.filepath,
        "checks": checks,
        "camera_names": sorted(obj.name for obj in cameras),
        "collections": sorted(bpy.data.collections.keys()),
    }
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
