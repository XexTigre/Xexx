from __future__ import annotations

import argparse
import json
import platform
import sys
from pathlib import Path

import bpy


def script_args() -> list[str]:
    if "--" not in sys.argv:
        return []
    return sys.argv[sys.argv.index("--") + 1 :]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--expected-version", default="4.5.12")
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args(script_args())

    scene = bpy.context.scene
    scene.unit_settings.system = "NONE"
    scene.unit_settings.system_rotation = "DEGREES"

    checks = {
        "version_matches": bpy.app.version_string.startswith(args.expected_version),
        "background_mode": bool(bpy.app.background),
        "factory_startup_flag": "--factory-startup" in sys.argv,
        "autoexec_disabled_flag": "--disable-autoexec" in sys.argv,
        "python_exit_code_flag": "--python-exit-code" in sys.argv,
        "unit_system_none": scene.unit_settings.system == "NONE",
        "rotation_degrees": scene.unit_settings.system_rotation == "DEGREES",
        "gltf_import_available": hasattr(bpy.ops.import_scene, "gltf"),
        "gltf_export_available": hasattr(bpy.ops.export_scene, "gltf"),
    }

    report = {
        "schema_version": "1.0.0",
        "status": "PASS" if all(checks.values()) else "FAIL",
        "checks": checks,
        "blender": {
            "version": bpy.app.version_string,
            "version_tuple": list(bpy.app.version),
            "build_hash": bpy.app.build_hash.decode("utf-8", errors="replace")
            if isinstance(bpy.app.build_hash, bytes)
            else str(bpy.app.build_hash),
            "binary_path": bpy.app.binary_path,
            "background": bool(bpy.app.background),
        },
        "python": {
            "version": platform.python_version(),
            "executable": sys.executable,
            "platform": platform.platform(),
        },
        "roblox_workspace": {
            "unit_system": scene.unit_settings.system,
            "rotation_unit": scene.unit_settings.system_rotation,
            "blender_up_axis": "+Z",
            "studio_up_axis": "+Y",
            "avatar_setup_front": "-Z",
            "r15_final_front": "+Z",
        },
    }

    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
