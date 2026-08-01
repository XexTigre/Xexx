from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ENV = ROOT / "blender_env"


def test_environment_lock_is_consistent() -> None:
    lock = json.loads((ENV / "environment.lock.json").read_text(encoding="utf-8"))
    assert lock["blender"]["version"] == "4.5.12"
    assert lock["blender"]["release_series"] == "4.5 LTS"
    assert lock["blender"]["source_commit"] == "84afd5f785f7"
    assert lock["roblox_workspace"]["blender_unit_system"] == "NONE"
    assert lock["roblox_workspace"]["one_blender_unit_equals_one_stud"] is True
    assert lock["roblox_workspace"]["avatar_setup_front_axis"] == "-Z"
    assert lock["roblox_workspace"]["r15_final_front_axis"] == "+Z"


def test_bootstraps_pin_same_version_and_verify_sha256() -> None:
    linux = (ENV / "bootstrap_linux.sh").read_text(encoding="utf-8")
    windows = (ENV / "bootstrap_windows.ps1").read_text(encoding="utf-8")
    for content in (linux, windows):
        assert "4.5.12" in content
        assert "blender-4.5.12.sha256" in content or "blender-$Version.sha256" in content
        assert "--disable-autoexec" in content
        assert "--factory-startup" in content
        assert "--python-exit-code" in content


def test_workspace_generator_contains_roblox_contract() -> None:
    source = (ENV / "scripts" / "create_roblox_workspace.py").read_text(encoding="utf-8")
    for required in (
        'scene.unit_settings.system = "NONE"',
        'scene.unit_settings.system_rotation = "DEGREES"',
        '"10_SOURCE_IMMUTABLE"',
        '"20_WORKING_COPY"',
        '"90_QUARANTINE"',
        '"99_EXPORT"',
        'scene["avatar_setup_front_axis"] = "-Z"',
        'scene["r15_final_front_axis"] = "+Z"',
    ):
        assert required in source


def test_workflow_executes_real_blender_smoke_test() -> None:
    workflow = (ROOT / ".github" / "workflows" / "blender-environment.yml").read_text(encoding="utf-8")
    assert "bootstrap_linux.sh" in workflow
    assert "ROBLOX_CONTRACT_WORKSPACE_4_5.blend" in workflow
    assert "validate_workspace.py" in workflow
    assert "actions/upload-artifact@v4" in workflow
