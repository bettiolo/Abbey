#!/usr/bin/env python3
"""Synchronize spec-generated identity sprites into the projection manifest.

The renderer writes PNG sheets from asset specs.  This tool records their exact
hashes, source spec/GLB provenance, deterministic slices, and catalog mappings,
then removes the matching roles from the honest unresolved list.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import struct
from pathlib import Path

MANIFEST_RELATIVE = Path(
    "unity/Assets/_Game/Art/Placeholders/MerchantShadeMiniWorld/manifest.json"
)
SPEC_ROOT_RELATIVE = Path("blender/asset_specs")
GLB_ROOT_RELATIVE = Path("blender/generated/glb")
SPRITE_ROOT_RELATIVE = Path(
    "unity/Assets/_Game/Art/Placeholders/MerchantShadeMiniWorld/"
    "AbbeyGeneratedIdentity"
)
RENDERER_RELATIVE = Path("blender/scripts/render_identity_sprites.py")
SOURCE_KIND = "abbeySpecGenerated"
VIEW_ORDER = ("south", "east", "north", "west")


class SyncError(RuntimeError):
    """Raised when committed source or generated sprite data is incomplete."""


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def png_dimensions(path: Path) -> tuple[int, int]:
    header = path.read_bytes()[:24]
    if (
        len(header) != 24
        or header[:8] != b"\x89PNG\r\n\x1a\n"
        or header[12:16] != b"IHDR"
    ):
        raise SyncError(f"not a PNG: {path}")
    return struct.unpack(">II", header[16:24])


def repository_path(repo_root: Path, path: Path) -> str:
    return path.resolve().relative_to(repo_root.resolve()).as_posix()


def projection_specs(repo_root: Path) -> list[tuple[Path, dict]]:
    specs: list[tuple[Path, dict]] = []
    for path in sorted((repo_root / SPEC_ROOT_RELATIVE).rglob("*.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        projection = data.get("sprite_projection")
        if isinstance(projection, dict) and projection.get("enabled") is True:
            specs.append((path, data))
    if not specs:
        raise SyncError("no asset specs declare sprite_projection.enabled")
    return specs


def build_file_record(
    repo_root: Path,
    spec_path: Path,
    spec: dict,
    renderer_hash: str,
) -> tuple[dict, dict[str, str]]:
    asset_id = spec["id"]
    projection = spec["sprite_projection"]
    filename = projection.get("filename", f"abbey_generated_{asset_id}.png")
    sprite_path = repo_root / SPRITE_ROOT_RELATIVE / filename
    glb_path = repo_root / GLB_ROOT_RELATIVE / f"{asset_id}.glb"
    if not sprite_path.is_file():
        raise SyncError(f"{asset_id}: generated sprite is missing: {sprite_path}")
    if not glb_path.is_file():
        raise SyncError(f"{asset_id}: generated GLB is missing: {glb_path}")

    cell_size = int(projection["cell_size"])
    views = projection["views"]
    if (
        not isinstance(views, list)
        or not views
        or len(set(views)) != len(views)
        or any(view not in VIEW_ORDER for view in views)
    ):
        raise SyncError(f"{asset_id}: invalid views {views!r}")
    width, height = png_dimensions(sprite_path)
    expected = (cell_size * len(views), cell_size)
    if (width, height) != expected:
        raise SyncError(
            f"{asset_id}: expected {expected[0]}x{expected[1]}, got {width}x{height}"
        )

    file_id = f"abbey_identity_{asset_id}"
    slice_refs: dict[str, str] = {}
    slices: list[dict] = []
    for index, view in enumerate(views):
        name = f"{file_id}_{view}"
        slices.append(
            {
                "name": name,
                "rect": {
                    "x": index * cell_size,
                    "y": 0,
                    "width": cell_size,
                    "height": cell_size,
                },
            }
        )
        slice_refs[view] = f"{file_id}:{name}"

    record = {
        "fileId": file_id,
        "category": "abbeyIdentity",
        "sourceKind": SOURCE_KIND,
        "sourceAssetId": asset_id,
        "sourcePath": repository_path(repo_root, spec_path),
        "sourceSha256": sha256(spec_path),
        "sourceGlbPath": repository_path(repo_root, glb_path),
        "sourceGlbSha256": sha256(glb_path),
        "sourceRendererPath": RENDERER_RELATIVE.as_posix(),
        "sourceRendererSha256": renderer_hash,
        "abbeyPath": repository_path(repo_root, sprite_path),
        "sha256": sha256(sprite_path),
        "dimensions": {"width": width, "height": height},
        "expectedDimensions": {"width": width, "height": height},
        "sheetCellSize": {"width": cell_size, "height": cell_size},
        "importMode": "multiple",
        "pixelsPerUnit": cell_size,
        "orientation": "cameraFacingXZ",
        "pivot": [0.5, 0.0],
        "slices": slices,
    }
    return record, slice_refs


def build_entry(mapping: dict, slice_refs: dict[str, str]) -> dict:
    default = slice_refs.get("south") or next(iter(slice_refs.values()))
    directional = (
        {view: slice_refs[view] for view in VIEW_ORDER}
        if all(view in slice_refs for view in VIEW_ORDER)
        else None
    )
    return {
        "stableRoleId": mapping["stable_role_id"],
        "assetId": mapping["asset_id"],
        "roles": mapping["roles"],
        "componentTypeNames": mapping["component_type_names"],
        "defaultSprite": default,
        "directionalSprites": directional,
        "walkAnimation": None,
        "visualScale": mapping["visual_scale"],
        "anchorOffset": mapping["anchor_offset"],
        "roleSortOffset": mapping["sort_offset"],
        "phaseTint": mapping["phase_tint"],
        "authoredFootprint": mapping["authored_footprint"],
        "fallbackPolicy": "reversible3D",
        "temporaryIdentityProxy": False,
    }


def synchronize(repo_root: Path, manifest: dict) -> dict:
    renderer_path = repo_root / RENDERER_RELATIVE
    if not renderer_path.is_file():
        raise SyncError(f"renderer is missing: {renderer_path}")
    renderer_hash = sha256(renderer_path)

    generated_files: list[dict] = []
    generated_entries: list[dict] = []
    resolved_asset_ids: set[str] = set()
    resolved_stable_ids: set[str] = set()
    for spec_path, spec in projection_specs(repo_root):
        record, slice_refs = build_file_record(
            repo_root, spec_path, spec, renderer_hash
        )
        generated_files.append(record)
        mappings = spec["sprite_projection"].get("catalog_entries")
        if not isinstance(mappings, list) or not mappings:
            raise SyncError(f"{spec['id']}: catalog_entries must be non-empty")
        for mapping in mappings:
            entry = build_entry(mapping, slice_refs)
            if entry["assetId"] in resolved_asset_ids:
                raise SyncError(f"duplicate generated asset mapping: {entry['assetId']}")
            if entry["stableRoleId"] in resolved_stable_ids:
                raise SyncError(
                    f"duplicate generated stable role: {entry['stableRoleId']}"
                )
            resolved_asset_ids.add(entry["assetId"])
            resolved_stable_ids.add(entry["stableRoleId"])
            generated_entries.append(entry)

    retained_files = [
        item
        for item in manifest.get("files", [])
        if item.get("sourceKind") != SOURCE_KIND
    ]
    retained_entries = [
        item
        for item in manifest.get("entries", [])
        if item.get("assetId") not in resolved_asset_ids
        and item.get("stableRoleId") not in resolved_stable_ids
    ]
    unresolved = [
        item
        for item in manifest.get("unresolvedRoles", [])
        if item.get("assetId") not in resolved_asset_ids
    ]

    manifest["files"] = retained_files + sorted(
        generated_files, key=lambda item: item["fileId"]
    )
    manifest["entries"] = retained_entries + sorted(
        generated_entries, key=lambda item: item["stableRoleId"]
    )
    manifest["unresolvedRoles"] = unresolved
    manifest["generatedIdentitySource"] = {
        "kind": SOURCE_KIND,
        "ownership": "Abbey project-generated derivative presentation",
        "sourceContract": "validated asset spec + generated GLB",
        "generatorPath": RENDERER_RELATIVE.as_posix(),
        "generatorSha256": renderer_hash,
        "paletteContract": "shared Abbey materials, quantized lighting, one-pixel outline",
    }
    manifest["finalVisualGateBlocked"] = bool(unresolved)
    if unresolved:
        manifest["finalVisualGateBlockReason"] = (
            f"{len(unresolved)} signature roles still lack an approved sprite source; "
            "identity-preserving reversible 3D fallbacks remain."
        )
    else:
        manifest["finalVisualGateBlockReason"] = ""
    return manifest


def serialized(manifest: dict) -> str:
    return json.dumps(manifest, indent=2, ensure_ascii=False) + "\n"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--repo-root", type=Path, default=Path(__file__).resolve().parents[1]
    )
    parser.add_argument("--check", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    repo_root = args.repo_root.resolve()
    manifest_path = repo_root / MANIFEST_RELATIVE
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    expected = serialized(synchronize(repo_root, manifest))
    current = manifest_path.read_text(encoding="utf-8")
    if args.check:
        if current != expected:
            print("ERROR: identity sprite records in manifest.json are stale")
            return 1
        print("Identity sprite manifest records are synchronized")
        return 0
    manifest_path.write_text(expected, encoding="utf-8")
    print(
        "Synchronized identity sprite manifest: "
        f"{sum(1 for item in manifest['files'] if item.get('sourceKind') == SOURCE_KIND)} "
        f"generated sheets, {len(manifest['unresolvedRoles'])} unresolved roles"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
