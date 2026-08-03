#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import os
import shutil
import time
import zipfile
from pathlib import Path
from typing import Any

import requests

ROOT = Path("temp/public_3d_assets")
DOWNLOADS = ROOT / "downloads"
OUT = ROOT / "bundle"
ASSETS = OUT / "assets" / "kenney"
LICENSES = OUT / "licenses"

PACKS: list[dict[str, Any]] = [
    {
        "slug": "prototype_kit",
        "title": "Prototype Kit",
        "category": "characters_buildings_vehicles_prototyping",
        "page": "https://www.kenney.nl/assets/prototype-kit",
        "url": "https://www.kenney.nl/media/pages/assets/prototype-kit/4d3b7073ed-1724832076/kenney_prototype-kit.zip",
        "expected_assets": 145,
    },
    {
        "slug": "mini_market",
        "title": "Mini Market",
        "category": "shops_food_retail_props",
        "page": "https://www.kenney.nl/assets/mini-market",
        "url": "https://www.kenney.nl/media/pages/assets/mini-market/463f38da51-1729865423/kenney_mini-market.zip",
        "expected_assets": 20,
    },
    {
        "slug": "nature_kit",
        "title": "Nature Kit",
        "category": "trees_rocks_foliage_environment",
        "page": "https://kenney.nl/assets/nature-kit",
        "url": "https://kenney.nl/media/pages/assets/nature-kit/37ac38a37b-1677698939/kenney_nature-kit.zip",
        "expected_assets": 330,
    },
    {
        "slug": "furniture_kit",
        "title": "Furniture Kit",
        "category": "interiors_furniture_home_school_office",
        "page": "https://kenney.nl/assets/furniture-kit",
        "url": "https://kenney.nl/media/pages/assets/furniture-kit/440e0608a4-1677580847/kenney_furniture-kit.zip",
        "expected_assets": 140,
    },
    {
        "slug": "platformer_kit",
        "title": "Platformer Kit",
        "category": "obby_platforms_hazards_characters",
        "page": "https://kenney.nl/assets/platformer-kit",
        "url": "https://kenney.nl/media/pages/assets/platformer-kit/1585cf62b4-1775122253/kenney_platformer-kit.zip",
        "expected_assets": 150,
    },
    {
        "slug": "city_roads",
        "title": "City Kit (Roads)",
        "category": "roads_sidewalks_city_environment",
        "page": "https://www.kenney.nl/assets/city-kit-roads",
        "url": "https://www.kenney.nl/media/pages/assets/city-kit-roads/74288c9459-1741864740/kenney_city-kit-roads.zip",
        "expected_assets": 70,
    },
]

MODEL_EXTENSIONS = {".blend", ".glb", ".gltf", ".fbx", ".obj", ".dae", ".stl"}
PRIMARY_PRIORITY = [".glb", ".gltf", ".blend", ".fbx", ".obj"]
USER_AGENT = "RobloxVideoFactoryAssetCollector/1.0 (+https://github.com/XexTigre/Xexx)"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def download(session: requests.Session, pack: dict[str, Any], destination: Path) -> list[dict[str, Any]]:
    attempts: list[dict[str, Any]] = []
    urls = [pack["url"]]
    if "www.kenney.nl" in pack["url"]:
        urls.append(pack["url"].replace("www.kenney.nl", "kenney.nl"))
    elif "kenney.nl" in pack["url"]:
        urls.append(pack["url"].replace("kenney.nl", "www.kenney.nl", 1))

    for url in dict.fromkeys(urls):
        for attempt in range(1, 4):
            try:
                with session.get(url, stream=True, timeout=(30, 180), allow_redirects=True) as response:
                    record = {
                        "url": url,
                        "attempt": attempt,
                        "status": response.status_code,
                        "content_type": response.headers.get("content-type"),
                        "final_url": response.url,
                    }
                    response.raise_for_status()
                    with destination.open("wb") as handle:
                        for chunk in response.iter_content(chunk_size=1024 * 1024):
                            if chunk:
                                handle.write(chunk)
                    record["bytes"] = destination.stat().st_size
                    attempts.append(record)
                    if destination.stat().st_size < 1024:
                        raise RuntimeError("arquivo baixado é pequeno demais")
                    return attempts
            except Exception as exc:
                attempts.append({"url": url, "attempt": attempt, "error": str(exc)})
                destination.unlink(missing_ok=True)
                time.sleep(attempt * 2)
    raise RuntimeError(f"falha ao baixar {pack['title']}: {attempts}")


def choose_primary(files: list[Path]) -> tuple[str | None, list[Path]]:
    for suffix in PRIMARY_PRIORITY:
        selected = [p for p in files if p.suffix.lower() == suffix]
        if selected:
            return suffix.removeprefix("."), selected
    return None, []


def relative_posix(path: Path, base: Path) -> str:
    return path.relative_to(base).as_posix()


def main() -> int:
    if ROOT.exists():
        shutil.rmtree(ROOT)
    DOWNLOADS.mkdir(parents=True)
    ASSETS.mkdir(parents=True)
    LICENSES.mkdir(parents=True)

    session = requests.Session()
    session.headers.update({"User-Agent": USER_AGENT, "Accept": "application/zip,*/*;q=0.8"})

    catalog: dict[str, Any] = {
        "generated_at_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "review_status": "PENDING",
        "license_policy": "Somente pacotes verificados como CC0 foram incluídos.",
        "sources_reviewed": [
            {
                "name": "Kenney",
                "status": "SELECTED_AND_DOWNLOADED",
                "license": "CC0 1.0",
                "reason": "assets estilizados, leves e adequados a vídeos 3D rápidos",
                "url": "https://www.kenney.nl/assets",
            },
            {
                "name": "Quaternius",
                "status": "VERIFIED_NOT_BUNDLED",
                "license": "CC0 nos packs verificados",
                "reason": "boa fonte complementar; downloads gratuitos passam pelo fluxo do itch.io",
                "url": "https://quaternius.com/packs.html",
            },
            {
                "name": "Poly Haven",
                "status": "VERIFIED_NOT_BUNDLED",
                "license": "CC0",
                "reason": "excelente para modelos realistas, HDRIs e materiais; menos alinhado ao estilo low-poly deste pacote inicial",
                "url": "https://polyhaven.com/",
            },
        ],
        "packs": [],
        "summary": {},
    }

    all_primary: list[dict[str, Any]] = []
    failures: list[dict[str, Any]] = []

    for pack in PACKS:
        archive = DOWNLOADS / f"{pack['slug']}.zip"
        pack_record: dict[str, Any] = {**pack, "license": "CC0 1.0", "review": {}}
        try:
            attempts = download(session, pack, archive)
            pack_record["download_attempts"] = attempts
            pack_record["archive_bytes"] = archive.stat().st_size
            pack_record["archive_sha256"] = sha256_file(archive)

            with zipfile.ZipFile(archive) as zf:
                bad = zf.testzip()
                if bad:
                    raise RuntimeError(f"ZIP corrompido no membro {bad}")
                names = zf.namelist()
                pack_record["zip_members"] = len(names)
                destination = ASSETS / pack["slug"]
                destination.mkdir(parents=True, exist_ok=True)
                zf.extractall(destination)

            model_files = sorted(
                p for p in (ASSETS / pack["slug"]).rglob("*")
                if p.is_file() and p.suffix.lower() in MODEL_EXTENSIONS
            )
            primary_format, primary_files = choose_primary(model_files)
            format_counts: dict[str, int] = {}
            for file in model_files:
                key = file.suffix.lower().removeprefix(".")
                format_counts[key] = format_counts.get(key, 0) + 1

            for file in primary_files:
                all_primary.append({
                    "id": f"kenney/{pack['slug']}/{file.stem}",
                    "pack": pack["slug"],
                    "title": file.stem,
                    "category": pack["category"],
                    "format": file.suffix.lower().removeprefix("."),
                    "path": relative_posix(file, OUT),
                    "bytes": file.stat().st_size,
                    "license": "CC0 1.0",
                    "source_page": pack["page"],
                })

            pack_record["model_files_total_all_formats"] = len(model_files)
            pack_record["format_counts"] = format_counts
            pack_record["primary_format"] = primary_format
            pack_record["primary_asset_count"] = len(primary_files)
            pack_record["review"] = {
                "download_verified": True,
                "zip_integrity_verified": True,
                "extraction_verified": True,
                "model_files_found": bool(model_files),
                "primary_format_found": bool(primary_files),
                "status": "APPROVED" if model_files and primary_files else "REJECTED",
            }
            if pack_record["review"]["status"] != "APPROVED":
                failures.append({"pack": pack["slug"], "error": "nenhum formato primário encontrado"})
        except Exception as exc:
            pack_record["review"] = {"status": "REJECTED"}
            pack_record["error"] = str(exc)
            failures.append({"pack": pack["slug"], "error": str(exc)})
        catalog["packs"].append(pack_record)

    catalog["summary"] = {
        "packs_requested": len(PACKS),
        "packs_approved": sum(1 for p in catalog["packs"] if p["review"].get("status") == "APPROVED"),
        "packs_rejected": sum(1 for p in catalog["packs"] if p["review"].get("status") != "APPROVED"),
        "primary_assets_indexed": len(all_primary),
        "formats": sorted({a["format"] for a in all_primary}),
        "total_extracted_bytes": sum(p.stat().st_size for p in ASSETS.rglob("*") if p.is_file()),
    }
    catalog["review_status"] = "APPROVED" if not failures and all_primary else "PARTIAL"
    catalog["failures"] = failures

    (OUT / "asset_catalog.json").write_text(
        json.dumps({"assets": all_primary}, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    (OUT / "download_review.json").write_text(
        json.dumps(catalog, indent=2, ensure_ascii=False), encoding="utf-8"
    )

    license_text = """Kenney assets included in this bundle are licensed under Creative Commons CC0 1.0 Universal.\n\nOfficial source: https://www.kenney.nl/assets\nLicense deed: https://creativecommons.org/publicdomain/zero/1.0/\n\nAttribution is not required by CC0, but retaining source information is recommended for provenance.\n"""
    (LICENSES / "KENNEY_CC0.txt").write_text(license_text, encoding="utf-8")

    sources_md = [
        "# Bibliotecas 3D públicas verificadas",
        "",
        "Revisão realizada em 3 de agosto de 2026.",
        "",
        "## Incluída no pacote",
        "",
        "### Kenney",
        "",
        "- Licença dos seis packs: **CC0 1.0**.",
        "- Selecionada por oferecer modelos low-poly leves, consistentes e adequados a vídeos verticais estilizados.",
        "- Os arquivos originais dos packs foram preservados, incluindo os formatos distribuídos pelo autor.",
        "",
        "## Verificadas como fontes complementares",
        "",
        "### Quaternius",
        "",
        "- Os packs revisados informam licença CC0 e formatos FBX, OBJ, glTF e, em algumas versões, Blend.",
        "- Não foi incluída nesta coleta porque o download gratuito atual passa pelo fluxo interativo do itch.io.",
        "",
        "### Poly Haven",
        "",
        "- Todos os assets são CC0.",
        "- A API pública permite uso pessoal e comercial; integração com a API ao vivo pede crédito visível à Poly Haven.",
        "- É mais indicada para HDRIs, materiais PBR e objetos realistas do que para o estilo low-poly inicial.",
        "",
        "## Resultado da coleta",
        "",
        f"- Packs aprovados: **{catalog['summary']['packs_approved']}/{len(PACKS)}**",
        f"- Assets no formato primário indexados: **{len(all_primary)}**",
        f"- Status: **{catalog['review_status']}**",
    ]
    (OUT / "THIRD_PARTY_ASSETS.md").write_text("\n".join(sources_md) + "\n", encoding="utf-8")

    readme = f"""# Biblioteca pública de assets 3D\n\nStatus da revisão: **{catalog['review_status']}**\n\nEste pacote contém seis coleções CC0 da Kenney, preservadas em `assets/kenney/`, além de um catálogo JSON com os modelos no melhor formato disponível para importação.\n\n## Conteúdo\n\n- Prototype Kit\n- Mini Market\n- Nature Kit\n- Furniture Kit\n- Platformer Kit\n- City Kit (Roads)\n\n## Importação no Blender\n\nPrefira os caminhos listados em `asset_catalog.json`. A ordem de preferência usada foi GLB, glTF, Blend, FBX e OBJ.\n\n## Licença\n\nOs assets incluídos são CC0. Consulte `licenses/KENNEY_CC0.txt` e preserve `download_review.json` para rastreabilidade.\n"""
    (OUT / "README.md").write_text(readme, encoding="utf-8")

    print(json.dumps(catalog["summary"], indent=2, ensure_ascii=False))
    return 0 if catalog["review_status"] == "APPROVED" else 2


if __name__ == "__main__":
    raise SystemExit(main())
