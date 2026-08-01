from __future__ import annotations

import json
import math
import sys
from pathlib import Path

import bpy
from mathutils import Vector


def script_args() -> list[str]:
    if "--" not in sys.argv:
        return []
    return sys.argv[sys.argv.index("--") + 1 :]


def get_or_create_collection(name: str, parent: bpy.types.Collection) -> bpy.types.Collection:
    collection = bpy.data.collections.get(name) or bpy.data.collections.new(name)
    if collection.name not in {child.name for child in parent.children}:
        parent.children.link(collection)
    return collection


def create_empty(name: str, collection: bpy.types.Collection, location=(0.0, 0.0, 0.0)) -> bpy.types.Object:
    obj = bpy.data.objects.new(name, None)
    obj.empty_display_type = "PLAIN_AXES"
    obj.location = location
    collection.objects.link(obj)
    return obj


def create_audit_camera(
    name: str,
    angle_deg: float,
    camera_collection: bpy.types.Collection,
    target: bpy.types.Object,
) -> bpy.types.Object:
    camera_data = bpy.data.cameras.new(name)
    camera_data.type = "ORTHO"
    camera_data.ortho_scale = 8.0
    camera = bpy.data.objects.new(name, camera_data)
    radius = 12.0
    height = 3.25
    angle = math.radians(angle_deg)
    camera.location = (radius * math.sin(angle), -radius * math.cos(angle), height)
    constraint = camera.constraints.new(type="TRACK_TO")
    constraint.target = target
    constraint.track_axis = "TRACK_NEGATIVE_Z"
    constraint.up_axis = "UP_Y"
    camera_collection.objects.link(camera)
    return camera


def main() -> int:
    args = script_args()
    if len(args) != 1:
        raise SystemExit("Uso: create_roblox_workspace.py -- caminho/arquivo.blend")
    output = Path(args[0]).resolve()
    output.parent.mkdir(parents=True, exist_ok=True)

    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = bpy.context.scene
    scene.name = "ROBLOX_CONTRACT_SCENE"
    scene.unit_settings.system = "NONE"
    scene.unit_settings.system_rotation = "DEGREES"
    scene.render.engine = "BLENDER_EEVEE_NEXT"
    scene.render.resolution_x = 1024
    scene.render.resolution_y = 1024
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.render.film_transparent = False

    if scene.world is None:
        scene.world = bpy.data.worlds.new("ROBLOX_NEUTRAL_WORLD")
    scene.world.use_nodes = True
    background = scene.world.node_tree.nodes.get("Background")
    if background:
        background.inputs[0].default_value = (0.035, 0.035, 0.035, 1.0)
        background.inputs[1].default_value = 0.8

    root = scene.collection
    reference = get_or_create_collection("00_REFERENCE_LOCKED", root)
    source = get_or_create_collection("10_SOURCE_IMMUTABLE", root)
    working = get_or_create_collection("20_WORKING_COPY", root)
    support = get_or_create_collection("30_RIG_CAGES_ATTACHMENTS", root)
    evidence = get_or_create_collection("40_EVIDENCE", root)
    quarantine = get_or_create_collection("90_QUARANTINE", root)
    export = get_or_create_collection("99_EXPORT", root)
    cameras = get_or_create_collection("AUDIT_CAMERAS", evidence)
    lights = get_or_create_collection("AUDIT_LIGHTS", evidence)

    origin = create_empty("RBX_ORIGIN_GROUND_CENTER", reference, (0.0, 0.0, 0.0))
    target = create_empty("RBX_AUDIT_TARGET", reference, (0.0, 0.0, 3.25))
    export_root = create_empty("RBX_EXPORT_ROOT", export, (0.0, 0.0, 0.0))
    export_root["pipeline_required"] = True

    for angle in range(0, 360, 30):
        create_audit_camera(f"AUDIT_CAM_{angle:03d}", angle, cameras, target)

    sun_data = bpy.data.lights.new("AUDIT_SUN", type="SUN")
    sun_data.energy = 2.0
    sun = bpy.data.objects.new("AUDIT_SUN", sun_data)
    sun.rotation_euler = (math.radians(35), math.radians(-20), math.radians(25))
    lights.objects.link(sun)

    area_data = bpy.data.lights.new("AUDIT_FILL", type="AREA")
    area_data.energy = 700.0
    area_data.shape = "DISK"
    area_data.size = 5.0
    area = bpy.data.objects.new("AUDIT_FILL", area_data)
    area.location = (-4.0, -5.0, 6.0)
    direction = Vector(target.location) - area.location
    area.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()
    lights.objects.link(area)

    scene.camera = bpy.data.objects["AUDIT_CAM_000"]
    scene["environment_id"] = "roblox-blender-4.5-lts"
    scene["blender_version_lock"] = "4.5.12"
    scene["one_blender_unit_equals_one_stud"] = True
    scene["blender_up_axis"] = "+Z"
    scene["studio_up_axis"] = "+Y"
    scene["avatar_setup_front_axis"] = "-Z"
    scene["r15_final_front_axis"] = "+Z"
    scene["source_collection"] = source.name
    scene["working_collection"] = working.name
    scene["support_collection"] = support.name
    scene["quarantine_collection"] = quarantine.name
    scene["export_collection"] = export.name

    manifest = {
        "environment_id": scene["environment_id"],
        "blender_version": bpy.app.version_string,
        "unit_system": scene.unit_settings.system,
        "rotation": scene.unit_settings.system_rotation,
        "collections": [collection.name for collection in root.children],
        "audit_cameras": [f"AUDIT_CAM_{angle:03d}" for angle in range(0, 360, 30)],
        "rules": {
            "source_immutable": True,
            "autoexec_disabled_for_automation": True,
            "exported_artifact_must_be_reopened": True,
            "studio_validation_is_separate": True,
        },
    }
    text = bpy.data.texts.new("ROBLOX_ENVIRONMENT_MANIFEST.json")
    text.write(json.dumps(manifest, indent=2, ensure_ascii=False))

    bpy.ops.wm.save_as_mainfile(filepath=str(output), check_existing=False)
    print(json.dumps({"status": "PASS", "workspace": str(output), "manifest": manifest}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
