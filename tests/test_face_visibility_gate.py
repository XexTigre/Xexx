from __future__ import annotations

import json
import struct
import sys
from pathlib import Path

ROOT = Path(__file__).parents[1]
sys.path.insert(0, str(ROOT))
from src.face_visibility_gate import inspect_glb


def _quad(x0, x1, y0, y1, z):
    return [(x0, y0, z), (x1, y0, z), (x1, y1, z), (x0, y1, z)]


def _write_glb(path: Path, *, patch=False, patch_textured=False, patch_double=True, mouthbag_front=False, include_lips=True):
    binary = bytearray()
    buffer_views = []
    accessors = []

    def add_positions(values):
        while len(binary) % 4:
            binary.append(0)
        offset = len(binary)
        for value in values:
            binary.extend(struct.pack("<3f", *value))
        view = len(buffer_views)
        buffer_views.append({"buffer": 0, "byteOffset": offset, "byteLength": len(values) * 12})
        accessor = len(accessors)
        accessors.append({"bufferView": view, "componentType": 5126, "count": len(values), "type": "VEC3"})
        return accessor

    def add_indices():
        values = [0, 1, 2, 0, 2, 3]
        while len(binary) % 4:
            binary.append(0)
        offset = len(binary)
        for value in values:
            binary.extend(struct.pack("<H", value))
        view = len(buffer_views)
        buffer_views.append({"buffer": 0, "byteOffset": offset, "byteLength": len(values) * 2})
        accessor = len(accessors)
        accessors.append({"bufferView": view, "componentType": 5123, "count": len(values), "type": "SCALAR"})
        return accessor

    def primitive(positions, material):
        return {"attributes": {"POSITION": add_positions(positions)}, "indices": add_indices(), "material": material}

    materials = [
        {"name": "BodyTexture", "pbrMetallicRoughness": {"baseColorTexture": {"index": 0}}},
        {"name": "Patch", "doubleSided": patch_double, "pbrMetallicRoughness": ({"baseColorTexture": {"index": 0}} if patch_textured else {"baseColorFactor": [0.6, 0.3, 0.2, 1]})},
        {"name": "Lips", "pbrMetallicRoughness": {"baseColorFactor": [0.01, 0.01, 0.01, 1]}},
        {"name": "MouthBag", "pbrMetallicRoughness": {"baseColorFactor": [0.03, 0.01, 0.01, 1]}},
    ]
    meshes = []
    nodes = []
    head_primitives = [primitive(_quad(-0.5, 0.5, 0.0, 1.0, 0.0), 0)]
    if patch:
        head_primitives.append(primitive(_quad(-0.30, 0.30, 0.35, 0.65, 0.19), 1))
    meshes.append({"name": "Head_Geo_Input", "primitives": head_primitives})
    nodes.append({"name": "Head_Geo_Input", "mesh": 0})
    if include_lips:
        meshes.append({"name": "UpperLip_Component", "primitives": [primitive(_quad(-0.14, 0.14, 0.51, 0.55, 0.20), 2)]})
        nodes.append({"name": "UpperLip_Component", "mesh": len(meshes) - 1})
        meshes.append({"name": "LowerLip_Component", "primitives": [primitive(_quad(-0.14, 0.14, 0.45, 0.49, 0.20), 2)]})
        nodes.append({"name": "LowerLip_Component", "mesh": len(meshes) - 1})
    bag_z = 0.30 if mouthbag_front else -0.20
    meshes.append({"name": "MouthBag_Component", "primitives": [primitive(_quad(-0.10, 0.10, 0.46, 0.54, bag_z), 3)]})
    nodes.append({"name": "MouthBag_Component", "mesh": len(meshes) - 1})
    doc = {
        "asset": {"version": "2.0"},
        "scene": 0,
        "scenes": [{"nodes": list(range(len(nodes)))}],
        "nodes": nodes,
        "meshes": meshes,
        "materials": materials,
        "textures": [{"source": 0}],
        "images": [{"uri": "data:image/png;base64,iVBORw0KGgo="}],
        "buffers": [{"byteLength": len(binary)}],
        "bufferViews": buffer_views,
        "accessors": accessors,
    }
    json_bytes = json.dumps(doc, separators=(",", ":")).encode()
    while len(json_bytes) % 4:
        json_bytes += b" "
    while len(binary) % 4:
        binary.append(0)
    total = 12 + 8 + len(json_bytes) + 8 + len(binary)
    raw = bytearray(struct.pack("<4sII", b"glTF", 2, total))
    raw.extend(struct.pack("<II", len(json_bytes), 0x4E4F534A))
    raw.extend(json_bytes)
    raw.extend(struct.pack("<II", len(binary), 0x004E4942))
    raw.extend(binary)
    path.write_bytes(raw)


def test_safe_textured_face_passes(tmp_path):
    path = tmp_path / "safe.glb"
    _write_glb(path)
    assert inspect_glb(path, "+Z")["decision"] == "FACE_VISIBILITY_LOCAL_PASS"


def test_opaque_untextured_patch_is_rejected(tmp_path):
    path = tmp_path / "bad_patch.glb"
    _write_glb(path, patch=True)
    report = inspect_glb(path, "+Z")
    codes = {finding["code"] for finding in report["findings"]}
    assert report["decision"] == "REJECTED"
    assert {"OPAQUE_UNTEXTURED_FACE_PATCH", "FACE_PATCH_OCCLUDES_MOUTH", "DOUBLE_SIDED_FACE_PATCH"} <= codes


def test_textured_patch_is_not_rejected_by_material_gate(tmp_path):
    path = tmp_path / "textured_patch.glb"
    _write_glb(path, patch=True, patch_textured=True, patch_double=False)
    assert inspect_glb(path, "+Z")["decision"] == "FACE_VISIBILITY_LOCAL_PASS"


def test_external_mouthbag_visibility_is_rejected(tmp_path):
    path = tmp_path / "bag_front.glb"
    _write_glb(path, mouthbag_front=True)
    report = inspect_glb(path, "+Z")
    assert report["decision"] == "REJECTED"
    assert "MOUTHBAG_VISIBLE_FROM_EXTERNAL_FRONT" in {finding["code"] for finding in report["findings"]}


def test_missing_lips_blocks(tmp_path):
    path = tmp_path / "missing_lips.glb"
    _write_glb(path, include_lips=False)
    assert inspect_glb(path, "+Z")["decision"] == "BLOCKED"
