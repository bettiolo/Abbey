"""Render deterministic pixel sheets from validated Abbey asset specs.

The source asset remains the normal spec + builder + GLB pipeline.  This script
adds a derived presentation artifact for specs that declare ``sprite_projection``.
It never changes the source mesh or its generated GLB.

Usage:

    blender -b --factory-startup -P blender/scripts/render_identity_sprites.py -- \
      --repo-root . --all

For visual tuning, one asset can be rendered without first editing its spec:

    blender -b --factory-startup -P blender/scripts/render_identity_sprites.py -- \
      --repo-root . --asset bellkeeper_lowpoly --cell-size 32 \
      --views south,east,north,west --output /tmp/bellkeeper.png
"""

from __future__ import annotations

import argparse
import json
import math
import os
import random
import sys
import tempfile
from pathlib import Path

import bpy
import numpy as np
from mathutils import Euler, Vector

_SCRIPTS_DIR = str(Path(__file__).resolve().parent)
if _SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, _SCRIPTS_DIR)

import asset_framework as fw
from generate_asset import generate_asset

RENDER_SCALE = 4
RENDER_SEED = 1729
CAMERA_PITCH_DEG = 30.0
CAMERA_YAW_DEG = 45.0
VIEW_YAWS = {
    "south": 0.0,
    "east": 90.0,
    "north": 180.0,
    "west": 270.0,
}
DEFAULT_OUTPUT_ROOT = Path(
    "unity/Assets/_Game/Art/Placeholders/MerchantShadeMiniWorld/"
    "AbbeyGeneratedIdentity"
)


def parse_args() -> argparse.Namespace:
    argv = sys.argv
    if "--" in argv:
        argv = argv[argv.index("--") + 1 :]
    else:
        argv = []
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--asset")
    parser.add_argument("--cell-size", type=int, default=32)
    parser.add_argument("--views", default="south")
    parser.add_argument("--output", type=Path)
    parser.add_argument("--output-root", type=Path, default=DEFAULT_OUTPUT_ROOT)
    args = parser.parse_args(argv)
    if not args.all and not args.asset:
        parser.error("one of --all or --asset is required")
    if args.all and args.asset:
        parser.error("--all and --asset are mutually exclusive")
    return args


def load_projection_specs(repo_root: Path) -> list[tuple[Path, dict]]:
    result: list[tuple[Path, dict]] = []
    spec_root = repo_root / "blender" / "asset_specs"
    for path in sorted(spec_root.rglob("*.json")):
        spec = json.loads(path.read_text(encoding="utf-8"))
        projection = spec.get("sprite_projection")
        if isinstance(projection, dict) and projection.get("enabled") is True:
            result.append((path, spec))
    return result


def configure_scene(cell_size: int) -> bpy.types.Scene:
    scene = bpy.context.scene
    scene.frame_set(1)
    scene.render.engine = "BLENDER_EEVEE"
    scene.render.resolution_x = cell_size * RENDER_SCALE
    scene.render.resolution_y = cell_size * RENDER_SCALE
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.render.image_settings.color_mode = "RGBA"
    scene.render.film_transparent = True
    if hasattr(scene.render, "film_transparent_glass"):
        scene.render.film_transparent_glass = True
    scene.render.filter_size = 0.01
    scene.render.use_file_extension = True
    scene.render.use_overwrite = True
    scene.render.use_placeholder = False
    scene.render.image_settings.color_depth = "8"
    try:
        scene.view_settings.look = "Medium High Contrast"
    except TypeError:
        scene.view_settings.look = "AgX - Medium High Contrast"
    scene.view_settings.view_transform = "AgX"
    scene.view_settings.exposure = 0.0
    scene.view_settings.gamma = 1.0
    if hasattr(scene, "eevee"):
        # Supersampling is handled explicitly by RENDER_SCALE. A single EEVEE
        # sample and stable, unjittered direct lighting avoid nudging pixels
        # across palette boundaries between otherwise identical bakes. Cast
        # shadows are supplied by Unity; disabling them here also prevents
        # coplanar ruin meshes from producing order-dependent shadow pixels.
        scene.eevee.taa_render_samples = 1
        scene.eevee.taa_samples = 1
        scene.eevee.use_taa_reprojection = False
        scene.eevee.use_shadows = False
    return scene


def clear_render_rig() -> None:
    for obj in list(bpy.context.scene.objects):
        if obj.name.startswith("sprite_bake_"):
            bpy.data.objects.remove(obj, do_unlink=True)


def configure_lighting() -> None:
    world = bpy.context.scene.world
    if world is None:
        world = bpy.data.worlds.new("sprite_bake_world")
        bpy.context.scene.world = world
    world.use_nodes = True
    background = world.node_tree.nodes.get("Background")
    if background is not None:
        background.inputs["Color"].default_value = (0.42, 0.50, 0.58, 1.0)
        background.inputs["Strength"].default_value = 0.65

    sun_data = bpy.data.lights.new("sprite_bake_sun", "SUN")
    sun_data.color = (1.0, 0.91, 0.76)
    sun_data.energy = 3.2
    # Soft sun shadows use stochastic samples in EEVEE. Hard shadows survive
    # the deliberate 4x downsample well and keep the bake byte-deterministic.
    sun_data.angle = 0.0
    sun = bpy.data.objects.new("sprite_bake_sun", sun_data)
    sun.rotation_euler = Euler(
        (math.radians(50.0), math.radians(-8.0), math.radians(65.0)), "XYZ"
    )
    fw.link_object(sun)


def hide_non_visual_objects(root: bpy.types.Object) -> None:
    for obj in fw.iter_asset_objects(root):
        name = obj.name.lower()
        is_non_visual = (
            name.endswith(fw.COLLISION_SUFFIX.lower())
            or "collision" in name
            or obj.type == "EMPTY"
        )
        obj.hide_render = is_non_visual


def setup_camera(root: bpy.types.Object, padding: float) -> None:
    dims = fw.measure_dimensions(root)
    low = Vector(dims["min"])
    high = Vector(dims["max"])
    center = (low + high) / 2.0
    maximum = max(dims["width"], dims["depth"], dims["height"], 0.1)

    camera_data = bpy.data.cameras.new("sprite_bake_camera")
    camera_data.type = "ORTHO"
    camera_data.ortho_scale = maximum * max(1.05, padding)
    camera_data.clip_start = 0.01
    camera_data.clip_end = max(100.0, maximum * 20.0)
    camera = bpy.data.objects.new("sprite_bake_camera", camera_data)
    rotation = Euler(
        (
            math.radians(90.0 - CAMERA_PITCH_DEG),
            0.0,
            math.radians(CAMERA_YAW_DEG),
        ),
        "XYZ",
    )
    camera.rotation_euler = rotation
    forward = rotation.to_matrix() @ Vector((0.0, 0.0, -1.0))
    camera.location = center - forward * max(10.0, maximum * 6.0)
    fw.link_object(camera)
    bpy.context.scene.camera = camera


def downsample_pixel_art(
    source: np.ndarray,
    cell_size: int,
    outline: tuple[float, float, float],
    color_steps: int,
) -> np.ndarray:
    high = cell_size * RENDER_SCALE
    rgba = source.reshape(high, high, 4)
    rgba = rgba.reshape(
        cell_size, RENDER_SCALE, cell_size, RENDER_SCALE, 4
    ).mean(axis=(1, 3))

    alpha = rgba[:, :, 3]
    opaque = alpha >= 0.18
    output = np.zeros_like(rgba)

    # One-pixel silhouette outline keeps identity readable at gameplay zoom.
    dilated = opaque.copy()
    for dy, dx in (
        (-1, -1), (-1, 0), (-1, 1),
        (0, -1),            (0, 1),
        (1, -1),  (1, 0),   (1, 1),
    ):
        shifted = np.zeros_like(opaque)
        source_y = slice(max(0, -dy), min(cell_size, cell_size - dy))
        source_x = slice(max(0, -dx), min(cell_size, cell_size - dx))
        target_y = slice(max(0, dy), min(cell_size, cell_size + dy))
        target_x = slice(max(0, dx), min(cell_size, cell_size + dx))
        shifted[target_y, target_x] = opaque[source_y, source_x]
        dilated |= shifted

    outline_mask = dilated & ~opaque
    output[outline_mask, :3] = outline
    output[outline_mask, 3] = 1.0

    rgb = np.clip(rgba[:, :, :3], 0.0, 1.0)
    steps = max(2, color_steps) - 1
    rgb = np.round(rgb * steps) / steps
    output[opaque, :3] = rgb[opaque]
    output[opaque, 3] = 1.0

    visible_y, visible_x = np.nonzero(output[:, :, 3] > 0.5)
    if len(visible_x) == 0:
        return output
    shift_y = 1 - int(visible_y.min())
    current_center_x = (float(visible_x.min()) + float(visible_x.max())) * 0.5
    target_center_x = (cell_size - 1) * 0.5
    shift_x = int(round(target_center_x - current_center_x))
    if shift_x == 0 and shift_y == 0:
        return output

    anchored = np.zeros_like(output)
    source_x0 = max(0, -shift_x)
    source_x1 = min(cell_size, cell_size - shift_x)
    source_y0 = max(0, -shift_y)
    source_y1 = min(cell_size, cell_size - shift_y)
    target_x0 = source_x0 + shift_x
    target_x1 = source_x1 + shift_x
    target_y0 = source_y0 + shift_y
    target_y1 = source_y1 + shift_y
    anchored[target_y0:target_y1, target_x0:target_x1] = output[
        source_y0:source_y1, source_x0:source_x1
    ]
    return anchored


def render_view(
    scene: bpy.types.Scene,
    root: bpy.types.Object,
    yaw_degrees: float,
    cell_size: int,
    outline: tuple[float, float, float],
    color_steps: int,
) -> np.ndarray:
    root.rotation_euler[2] = math.radians(yaw_degrees)
    bpy.context.view_layer.update()
    descriptor, temporary_name = tempfile.mkstemp(suffix=".png")
    os.close(descriptor)
    temporary = Path(temporary_name)
    scene.render.filepath = str(temporary)
    try:
        bpy.ops.render.render(write_still=True)
        rendered = bpy.data.images.load(str(temporary), check_existing=False)
        try:
            expected = scene.render.resolution_x * scene.render.resolution_y * 4
            pixels = np.empty(expected, dtype=np.float32)
            rendered.pixels.foreach_get(pixels)
            return downsample_pixel_art(
                pixels, cell_size, outline, color_steps
            )
        finally:
            bpy.data.images.remove(rendered)
    finally:
        temporary.unlink(missing_ok=True)


def save_atlas(path: Path, cells: list[np.ndarray]) -> None:
    if not cells:
        raise ValueError("cannot save an empty sprite atlas")
    path.parent.mkdir(parents=True, exist_ok=True)
    height, width, _ = cells[0].shape
    atlas = np.concatenate(cells, axis=1)
    image = bpy.data.images.new(
        f"sprite_bake_{path.stem}",
        width=width * len(cells),
        height=height,
        alpha=True,
        float_buffer=False,
    )
    try:
        image.colorspace_settings.name = "sRGB"
        image.pixels.foreach_set(atlas.astype(np.float32).reshape(-1))
        image.filepath_raw = str(path)
        image.file_format = "PNG"
        image.save()
    finally:
        bpy.data.images.remove(image)


def render_asset(
    repo_root: Path,
    asset_id: str,
    projection: dict,
    output: Path,
) -> None:
    random.seed(RENDER_SEED)
    np.random.seed(RENDER_SEED)
    result = generate_asset(asset_id)
    root = result["root"]
    hide_non_visual_objects(root)

    cell_size = int(projection.get("cell_size", 32))
    views = projection.get("views", ["south"])
    if not isinstance(views, list) or not views:
        raise ValueError(f"{asset_id}: sprite_projection.views must be a non-empty list")
    if any(view not in VIEW_YAWS for view in views):
        raise ValueError(f"{asset_id}: unknown sprite view in {views}")
    if cell_size < 16 or cell_size > 128 or cell_size % 16:
        raise ValueError(f"{asset_id}: cell_size must be 16..128 and divisible by 16")

    clear_render_rig()
    scene = configure_scene(cell_size)
    configure_lighting()
    setup_camera(root, float(projection.get("camera_padding", 1.35)))
    outline_values = projection.get("outline_color", [0.08, 0.07, 0.065])
    outline = tuple(float(value) for value in outline_values)
    color_steps = int(projection.get("color_steps", 12))
    cells = [
        render_view(
            scene,
            root,
            VIEW_YAWS[view],
            cell_size,
            outline,
            color_steps,
        )
        for view in views
    ]
    save_atlas(output, cells)
    print(
        f"Rendered {asset_id}: {len(cells)} view(s), {cell_size}px cells -> "
        f"{output.relative_to(repo_root) if output.is_relative_to(repo_root) else output}"
    )


def main() -> int:
    args = parse_args()
    repo_root = args.repo_root.resolve()
    fw.REPO_ROOT = repo_root
    fw.SPEC_DIR = repo_root / "blender" / "asset_specs"

    if args.asset:
        projection = {
            "cell_size": args.cell_size,
            "views": [value.strip() for value in args.views.split(",") if value.strip()],
            "camera_padding": 1.35,
            "outline_color": [0.08, 0.07, 0.065],
            "color_steps": 12,
        }
        output = args.output or (
            repo_root / args.output_root / f"abbey_generated_{args.asset}.png"
        )
        render_asset(repo_root, args.asset, projection, output.resolve())
        return 0

    specs = load_projection_specs(repo_root)
    if not specs:
        raise RuntimeError("no asset specs declare sprite_projection.enabled")
    for _, spec in specs:
        projection = spec["sprite_projection"]
        filename = projection.get(
            "filename", f"abbey_generated_{spec['id']}.png"
        )
        output = (repo_root / args.output_root / filename).resolve()
        render_asset(repo_root, spec["id"], projection, output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
