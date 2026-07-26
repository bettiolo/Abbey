from __future__ import annotations

import importlib.util
import json
import shutil
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
TOOL_PATH = REPO_ROOT / "tools" / "validate_merchant_shade_miniworld.py"
CURATED = REPO_ROOT / "unity/Assets/_Game/Art/Placeholders/MerchantShadeMiniWorld"
SPEC = importlib.util.spec_from_file_location("merchant_shade_validate", TOOL_PATH)
assert SPEC and SPEC.loader
validator = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(validator)


def copy_curated(tmp_path: Path) -> Path:
    destination = tmp_path / "MerchantShadeMiniWorld"
    shutil.copytree(CURATED, destination)
    return destination


def test_committed_curated_subset_is_self_consistent() -> None:
    result = validator.validate(CURATED)
    assert result == {
        "files": 54,
        "slices": 402,
        "mappedRoles": 84,
        "unresolvedRoles": 0,
    }


def test_validator_rejects_unlisted_png(tmp_path: Path) -> None:
    curated = copy_curated(tmp_path)
    (curated / "Nature/unlisted.png").write_bytes(
        (curated / "Nature/abbey_placeholder_miniworld_trees.png").read_bytes()
    )
    with pytest.raises(validator.ValidationError, match="inventory mismatch"):
        validator.validate(curated)


def test_validator_rejects_binary_hash_drift(tmp_path: Path) -> None:
    curated = copy_curated(tmp_path)
    path = curated / "Terrain/abbey_placeholder_miniworld_grass.png"
    path.write_bytes(path.read_bytes() + b"drift")
    with pytest.raises(validator.ValidationError, match="SHA-256 mismatch"):
        validator.validate(curated)


def test_validator_rejects_unknown_sprite_reference(tmp_path: Path) -> None:
    curated = copy_curated(tmp_path)
    path = curated / "manifest.json"
    manifest = json.loads(path.read_text(encoding="utf-8"))
    manifest["entries"][0]["defaultSprite"] = "missing:missing"
    path.write_text(json.dumps(manifest), encoding="utf-8")
    with pytest.raises(validator.ValidationError, match="unknown sprite reference"):
        validator.validate(curated)


def test_validator_rejects_non_positive_authored_footprint(tmp_path: Path) -> None:
    curated = copy_curated(tmp_path)
    path = curated / "manifest.json"
    manifest = json.loads(path.read_text(encoding="utf-8"))
    building = next(
        entry for entry in manifest["entries"] if entry["authoredFootprint"] is not None
    )
    building["authoredFootprint"] = [0, 2]
    path.write_text(json.dumps(manifest), encoding="utf-8")
    with pytest.raises(validator.ValidationError, match="invalid authoredFootprint"):
        validator.validate(curated)


def test_contact_sheet_rejects_manifest_path_traversal(tmp_path: Path) -> None:
    curated = copy_curated(tmp_path)
    with pytest.raises(validator.ValidationError, match="unsafe report abbeyPath"):
        validator.resolve_under(curated, "../../outside.png", "report abbeyPath")


def test_all_signature_roles_are_resolved_and_final_gate_is_clear() -> None:
    manifest = validator.load_manifest(CURATED)
    assert manifest["finalVisualGateBlocked"] is False
    assert manifest["finalVisualGateBlockReason"] == ""
    assert manifest["unresolvedRoles"] == []

    entries = {item["stableRoleId"]: item for item in manifest["entries"]}
    expected = {
        "role.actor.nightmare.deadWorker": "DeadWorker",
        "role.actor.nightmare.rootWalker": "RootWalker",
        "role.actor.nightmare.bellMimic": "BellMimic",
        "role.actor.nightmare.hollowDeer": "HollowDeer",
        "role.actor.nightmare.charcoalDead": "CharcoalDead",
        "role.prop.sacredFlame": "AbbeyFlame",
    }
    for role, asset_id in expected.items():
        assert entries[role]["assetId"] == asset_id
        assert entries[role]["temporaryIdentityProxy"] is False


def test_signature_roles_use_spec_generated_identity_sheets() -> None:
    manifest = validator.load_manifest(CURATED)
    generated_files = {
        item["fileId"]: item
        for item in manifest["files"]
        if item.get("sourceKind") == "abbeySpecGenerated"
    }
    entries = {item["stableRoleId"]: item for item in manifest["entries"]}
    for role in (
        "role.actor.bellkeeper",
        "role.actor.blackHound",
        "role.actor.stag",
        "role.building.ruinedBellTower",
        "role.prop.shipwreckHull",
        "role.actor.nightmare.deadWorker",
        "role.actor.nightmare.rootWalker",
        "role.actor.nightmare.bellMimic",
        "role.actor.nightmare.hollowDeer",
        "role.actor.nightmare.charcoalDead",
        "role.prop.sacredFlame",
    ):
        entry = entries[role]
        file_id = entry["defaultSprite"].split(":", 1)[0]
        assert generated_files[file_id]["sourceSha256"]
        assert generated_files[file_id]["sourceGlbPath"]
        assert generated_files[file_id]["sourceMetadataPath"]
        assert generated_files[file_id]["sourceGlbStructuralSha256"]
        assert generated_files[file_id]["sourceRendererSha256"]
        assert entry["temporaryIdentityProxy"] is False


def test_structural_glb_fingerprint_ignores_exporter_noise(tmp_path: Path) -> None:
    source = REPO_ROOT / "blender/generated/metadata/bellkeeper_lowpoly.meta.json"
    original = json.loads(source.read_text(encoding="utf-8"))
    rebuilt = json.loads(source.read_text(encoding="utf-8"))
    rebuilt["generated_at"] = "2099-01-01T00:00:00+00:00"
    glb_check = next(
        check
        for check in rebuilt["validation"]["checks"]
        if check["name"] == "glb_exists"
    )
    glb_check["detail"] = (
        "blender/generated/glb/bellkeeper_lowpoly.glb (64720 bytes)"
    )
    rebuilt_path = tmp_path / "rebuilt.meta.json"
    rebuilt_path.write_text(json.dumps(rebuilt), encoding="utf-8")

    assert validator.structural_metadata_sha256(source) == (
        validator.structural_metadata_sha256(rebuilt_path)
    )

    original["triangle_count"] += 1
    changed_path = tmp_path / "changed.meta.json"
    changed_path.write_text(json.dumps(original), encoding="utf-8")
    assert validator.structural_metadata_sha256(source) != (
        validator.structural_metadata_sha256(changed_path)
    )
