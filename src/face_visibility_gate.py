from __future__ import annotations

import argparse
import hashlib
import json
import struct
from pathlib import Path
from typing import Any

_COMPONENT_SIZE = {5120: 1, 5121: 1, 5122: 2, 5123: 2, 5125: 4, 5126: 4}
_COMPONENT_FMT = {5120: "b", 5121: "B", 5122: "h", 5123: "H", 5125: "I", 5126: "f"}
_TYPE_COMPONENTS = {"SCALAR": 1, "VEC2": 2, "VEC3": 3, "VEC4": 4, "MAT4": 16}


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def parse_glb(path: Path) -> tuple[dict[str, Any], bytes]:
    raw = path.read_bytes()
    if len(raw) < 20:
        raise ValueError("GLB_TOO_SHORT")
    magic, version, declared_length = struct.unpack_from("<4sII", raw, 0)
    if magic != b"glTF" or version != 2 or declared_length != len(raw):
        raise ValueError("INVALID_GLB_HEADER")
    offset = 12
    doc = None
    binary = b""
    while offset + 8 <= len(raw):
        chunk_length, chunk_type = struct.unpack_from("<II", raw, offset)
        offset += 8
        chunk = raw[offset : offset + chunk_length]
        offset += chunk_length
        if chunk_type == 0x4E4F534A:
            doc = json.loads(chunk.rstrip(b"\x00 \t\r\n").decode("utf-8"))
        elif chunk_type == 0x004E4942:
            binary = chunk
    if doc is None:
        raise ValueError("MISSING_JSON_CHUNK")
    return doc, binary


def accessor_values(doc: dict[str, Any], binary: bytes, index: int) -> list[tuple[float, ...]]:
    accessor = doc["accessors"][index]
    if "sparse" in accessor:
        raise ValueError("SPARSE_ACCESSOR_NOT_SUPPORTED")
    view = doc["bufferViews"][accessor["bufferView"]]
    component_type = accessor["componentType"]
    component_count = _TYPE_COMPONENTS[accessor["type"]]
    element_size = component_count * _COMPONENT_SIZE[component_type]
    stride = view.get("byteStride", element_size)
    start = view.get("byteOffset", 0) + accessor.get("byteOffset", 0)
    fmt = "<" + _COMPONENT_FMT[component_type] * component_count
    return [
        tuple(struct.unpack_from(fmt, binary, start + i * stride))
        for i in range(accessor["count"])
    ]


def _identity() -> list[list[float]]:
    return [[1.0 if r == c else 0.0 for c in range(4)] for r in range(4)]


def _matmul(a: list[list[float]], b: list[list[float]]) -> list[list[float]]:
    return [[sum(a[r][k] * b[k][c] for k in range(4)) for c in range(4)] for r in range(4)]


def _quat_matrix(rotation: list[float]) -> list[list[float]]:
    x, y, z, w = rotation
    return [
        [1 - 2 * y * y - 2 * z * z, 2 * x * y - 2 * z * w, 2 * x * z + 2 * y * w, 0],
        [2 * x * y + 2 * z * w, 1 - 2 * x * x - 2 * z * z, 2 * y * z - 2 * x * w, 0],
        [2 * x * z - 2 * y * w, 2 * y * z + 2 * x * w, 1 - 2 * x * x - 2 * y * y, 0],
        [0, 0, 0, 1],
    ]


def node_matrix(node: dict[str, Any]) -> list[list[float]]:
    if "matrix" in node:
        values = node["matrix"]
        return [[float(values[c * 4 + r]) for c in range(4)] for r in range(4)]
    t = _identity()
    s = _identity()
    r = _identity()
    if "translation" in node:
        t[0][3], t[1][3], t[2][3] = map(float, node["translation"])
    if "scale" in node:
        s[0][0], s[1][1], s[2][2] = map(float, node["scale"])
    if "rotation" in node:
        r = _quat_matrix([float(v) for v in node["rotation"]])
    return _matmul(_matmul(t, r), s)


def transform_point(matrix: list[list[float]], point: tuple[float, ...]) -> tuple[float, float, float]:
    x, y, z = point[:3]
    return (
        matrix[0][0] * x + matrix[0][1] * y + matrix[0][2] * z + matrix[0][3],
        matrix[1][0] * x + matrix[1][1] * y + matrix[1][2] * z + matrix[1][3],
        matrix[2][0] * x + matrix[2][1] * y + matrix[2][2] * z + matrix[2][3],
    )


def bounds(points: list[tuple[float, float, float]]) -> dict[str, list[float]]:
    return {
        "min": [min(p[i] for p in points) for i in range(3)],
        "max": [max(p[i] for p in points) for i in range(3)],
    }


def triangle_depth(triangle: list[tuple[float, float, float]], x: float, y: float) -> float | None:
    x1, y1, z1 = triangle[0]
    x2, y2, z2 = triangle[1]
    x3, y3, z3 = triangle[2]
    den = (y2 - y3) * (x1 - x3) + (x3 - x2) * (y1 - y3)
    if abs(den) < 1e-12:
        return None
    a = ((y2 - y3) * (x - x3) + (x3 - x2) * (y - y3)) / den
    b = ((y3 - y1) * (x - x3) + (x1 - x3) * (y - y3)) / den
    c = 1.0 - a - b
    if a < -1e-8 or b < -1e-8 or c < -1e-8:
        return None
    return a * z1 + b * z2 + c * z3


def inspect_glb(path: Path, front_axis: str = "+Z", grid_x: int = 29, grid_y: int = 17) -> dict[str, Any]:
    if front_axis not in {"+Z", "-Z"}:
        raise ValueError("front_axis must be +Z or -Z")
    doc, binary = parse_glb(path)
    nodes = doc.get("nodes", [])
    materials = doc.get("materials", [])
    parents: dict[int, int] = {}
    for parent_index, node in enumerate(nodes):
        for child in node.get("children", []):
            parents[child] = parent_index

    def world_matrix(node_index: int) -> list[list[float]]:
        chain = []
        current = node_index
        while True:
            chain.append(node_matrix(nodes[current]))
            if current not in parents:
                break
            current = parents[current]
        result = _identity()
        for matrix in reversed(chain):
            result = _matmul(result, matrix)
        return result

    primitives: list[dict[str, Any]] = []
    node_bounds: dict[str, dict[str, list[float]]] = {}
    for node_index, node in enumerate(nodes):
        if "mesh" not in node:
            continue
        matrix = world_matrix(node_index)
        node_points: list[tuple[float, float, float]] = []
        mesh = doc["meshes"][node["mesh"]]
        for primitive_index, primitive in enumerate(mesh.get("primitives", [])):
            positions = [
                transform_point(matrix, p)
                for p in accessor_values(doc, binary, primitive["attributes"]["POSITION"])
            ]
            indices = [int(v[0]) for v in accessor_values(doc, binary, primitive["indices"])]
            triangles = [
                [positions[indices[i]], positions[indices[i + 1]], positions[indices[i + 2]]]
                for i in range(0, len(indices), 3)
            ]
            material_index = primitive.get("material")
            material = materials[material_index] if material_index is not None else {}
            item = {
                "node": node.get("name", f"node_{node_index}"),
                "primitive_index": primitive_index,
                "material_name": material.get("name", ""),
                "has_base_color_texture": bool(material.get("pbrMetallicRoughness", {}).get("baseColorTexture")),
                "alpha_mode": material.get("alphaMode", "OPAQUE"),
                "double_sided": bool(material.get("doubleSided", False)),
                "bounds": bounds(positions),
                "triangles": triangles,
            }
            primitives.append(item)
            node_points.extend(positions)
        node_bounds[node.get("name", f"node_{node_index}")] = bounds(node_points)

    lip_bounds = [b for name, b in node_bounds.items() if "lip_component" in name.lower()]
    if len(lip_bounds) < 2:
        return {
            "schema_version": "1.0.0",
            "artifact": {"path": str(path), "sha256": sha256_file(path), "front_axis": front_axis},
            "decision": "BLOCKED",
            "release_eligible": False,
            "findings": [{"code": "MISSING_EXTERNAL_LIP_COMPONENTS", "severity": "BLOCKER"}],
        }

    lip_min = [min(b["min"][i] for b in lip_bounds) for i in range(3)]
    lip_max = [max(b["max"][i] for b in lip_bounds) for i in range(3)]
    lip_width = lip_max[0] - lip_min[0]
    lip_height = lip_max[1] - lip_min[1]
    x_min, x_max = lip_min[0] - max(0.01, lip_width * 0.03), lip_max[0] + max(0.01, lip_width * 0.03)
    y_min, y_max = lip_min[1] - max(0.005, lip_height * 0.03), lip_max[1] + max(0.005, lip_height * 0.03)
    lip_front = lip_max[2] if front_axis == "+Z" else lip_min[2]
    front_sign = 1.0 if front_axis == "+Z" else -1.0

    suspicious = []
    for primitive in primitives:
        b = primitive["bounds"]
        overlaps_xy = not (b["max"][0] < x_min or b["min"][0] > x_max or b["max"][1] < y_min or b["min"][1] > y_max)
        reaches_lips = b["max"][2] >= lip_front - 0.02 if front_axis == "+Z" else b["min"][2] <= lip_front + 0.02
        if (
            "head" in primitive["node"].lower()
            and overlaps_xy
            and reaches_lips
            and not primitive["has_base_color_texture"]
            and primitive["alpha_mode"] == "OPAQUE"
        ):
            suspicious.append(primitive)

    xs = [x_min + (x_max - x_min) * i / max(1, grid_x - 1) for i in range(grid_x)]
    ys = [y_min + (y_max - y_min) * i / max(1, grid_y - 1) for i in range(grid_y)]
    frontmost_counts: dict[str, int] = {}
    sample_count = 0
    for y in ys:
        for x in xs:
            hits = []
            for primitive in primitives:
                for triangle in primitive["triangles"]:
                    if x < min(p[0] for p in triangle) or x > max(p[0] for p in triangle):
                        continue
                    if y < min(p[1] for p in triangle) or y > max(p[1] for p in triangle):
                        continue
                    depth = triangle_depth(triangle, x, y)
                    if depth is not None:
                        hits.append((front_sign * depth, primitive))
            if not hits:
                continue
            sample_count += 1
            _, winner = max(hits, key=lambda item: item[0])
            key = f'{winner["node"]}::{winner["material_name"]}'
            frontmost_counts[key] = frontmost_counts.get(key, 0) + 1

    findings = []
    patch_frontmost = 0
    for primitive in suspicious:
        key = f'{primitive["node"]}::{primitive["material_name"]}'
        patch_frontmost += frontmost_counts.get(key, 0)
        width = primitive["bounds"]["max"][0] - primitive["bounds"]["min"][0]
        if width > lip_width * 1.5:
            findings.append({
                "code": "FACE_PATCH_WIDER_THAN_LIPS",
                "severity": "ERROR",
                "node": primitive["node"],
                "material": primitive["material_name"],
                "width_ratio": width / lip_width,
            })
        findings.append({
            "code": "OPAQUE_UNTEXTURED_FACE_PATCH",
            "severity": "ERROR",
            "node": primitive["node"],
            "material": primitive["material_name"],
            "double_sided": primitive["double_sided"],
            "bounds": primitive["bounds"],
        })
        if primitive["double_sided"]:
            findings.append({
                "code": "DOUBLE_SIDED_FACE_PATCH",
                "severity": "ERROR",
                "node": primitive["node"],
                "material": primitive["material_name"],
            })

    patch_ratio = patch_frontmost / sample_count if sample_count else 0.0
    if patch_ratio > 0.005:
        findings.append({
            "code": "FACE_PATCH_OCCLUDES_MOUTH",
            "severity": "ERROR",
            "frontmost_samples": patch_frontmost,
            "sample_count": sample_count,
            "ratio": patch_ratio,
        })

    mouthbag_frontmost = sum(count for key, count in frontmost_counts.items() if "mouthbag" in key.lower() or "mouth_bag" in key.lower())
    mouthbag_ratio = mouthbag_frontmost / sample_count if sample_count else 0.0
    if mouthbag_frontmost:
        findings.append({
            "code": "MOUTHBAG_VISIBLE_FROM_EXTERNAL_FRONT",
            "severity": "ERROR",
            "frontmost_samples": mouthbag_frontmost,
            "sample_count": sample_count,
            "ratio": mouthbag_ratio,
        })

    errors = [finding for finding in findings if finding["severity"] == "ERROR"]
    return {
        "schema_version": "1.0.0",
        "artifact": {"path": str(path), "sha256": sha256_file(path), "front_axis": front_axis},
        "mouth_envelope": {
            "x": [x_min, x_max],
            "y": [y_min, y_max],
            "lip_front_depth": lip_front,
            "lip_width": lip_width,
            "lip_height": lip_height,
        },
        "materials": [
            {
                "index": i,
                "name": material.get("name", ""),
                "has_base_color_texture": bool(material.get("pbrMetallicRoughness", {}).get("baseColorTexture")),
                "alpha_mode": material.get("alphaMode", "OPAQUE"),
                "double_sided": bool(material.get("doubleSided", False)),
            }
            for i, material in enumerate(materials)
        ],
        "frontmost_grid": {
            "grid_x": grid_x,
            "grid_y": grid_y,
            "sample_count": sample_count,
            "counts": dict(sorted(frontmost_counts.items(), key=lambda item: -item[1])),
            "suspicious_patch_ratio": patch_ratio,
            "mouthbag_ratio": mouthbag_ratio,
        },
        "findings": findings,
        "decision": "REJECTED" if errors else "FACE_VISIBILITY_LOCAL_PASS",
        "release_eligible": False,
        "platform_gates": {
            "roblox_avatar_setup_exact_hash": "NOT_RUN",
            "roblox_studio_exact_hash": "NOT_RUN",
            "ugc_marketplace_validation": "NOT_RUN",
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("glb", type=Path)
    parser.add_argument("--front-axis", choices=["+Z", "-Z"], required=True)
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()
    try:
        report = inspect_glb(args.glb, args.front_axis)
    except Exception as exc:
        report = {
            "schema_version": "1.0.0",
            "artifact": {"path": str(args.glb)},
            "decision": "BLOCKED",
            "release_eligible": False,
            "findings": [{"code": type(exc).__name__, "severity": "BLOCKER", "detail": str(exc)}],
        }
    output = json.dumps(report, indent=2, ensure_ascii=False)
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(output + "\n", encoding="utf-8")
    print(output)
    return 0 if report["decision"] == "FACE_VISIBILITY_LOCAL_PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
