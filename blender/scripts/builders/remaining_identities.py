"""Final signature identities: five consequence nightmares and Sacred Flame.

These are intentionally silhouette-led. Each creature has one unmistakable
shape language at the 48px projection size: crossed tool, walking roots, bell,
open rib cage, or coal sack. The Sacred Flame is a broad stone-and-gold beacon,
not a second generic campfire.

All meshes use only the shared Abbey material library and remain comfortably
inside the character/prop budgets declared by their specs.
"""

from __future__ import annotations

import math

import bpy

from asset_framework import add_anchor, register_builder
from builders._shapes import (
    add_box,
    add_cone,
    add_cylinder,
    add_icosphere,
    add_torus,
)


@register_builder("dead_worker_lowpoly")
def build_dead_worker(spec: dict) -> list[bpy.types.Object]:
    """A corpse bent under its old labour, facing -Y."""
    objects: list[bpy.types.Object] = []
    ash = "mat_ash"
    cloth = "mat_canvas"
    iron = "mat_iron"

    # dragging_legs: one planted, one trailing behind at a dead angle
    objects.append(
        add_box(
            "planted_leg",
            ash,
            size=(0.16, 0.18, 0.70),
            location=(-0.14, -0.03, 0.35),
            rotation=(math.radians(5.0), 0.0, math.radians(-4.0)),
        )
    )
    objects.append(
        add_box(
            "dragging_leg",
            ash,
            size=(0.15, 0.18, 0.74),
            location=(0.19, 0.18, 0.34),
            rotation=(math.radians(-15.0), 0.0, math.radians(10.0)),
        )
    )
    objects.append(
        add_box(
            "dragging_foot",
            ash,
            size=(0.17, 0.34, 0.10),
            location=(0.22, 0.39, 0.06),
            rotation=(0.0, 0.0, math.radians(8.0)),
        )
    )

    # broken_back: two offset blocks create a readable forward fold
    objects.append(
        add_box(
            "hips",
            cloth,
            size=(0.48, 0.34, 0.34),
            location=(0.0, 0.05, 0.84),
            rotation=(math.radians(5.0), 0.0, 0.0),
        )
    )
    objects.append(
        add_box(
            "broken_back",
            cloth,
            size=(0.54, 0.36, 0.70),
            location=(0.0, -0.13, 1.26),
            rotation=(math.radians(25.0), 0.0, 0.0),
        )
    )
    objects.append(
        add_box(
            "torn_apron",
            cloth,
            size=(0.40, 0.05, 0.58),
            location=(0.0, -0.37, 1.05),
            rotation=(math.radians(18.0), 0.0, 0.0),
        )
    )

    # bowed_head hangs below the shoulder line
    objects.append(
        add_box(
            "bowed_head",
            ash,
            size=(0.25, 0.26, 0.27),
            location=(0.0, -0.36, 1.55),
            rotation=(math.radians(38.0), 0.0, 0.0),
        )
    )

    # limp_arms reach below the waist and still close around the mattock
    for index, side in enumerate((1, -1)):
        objects.append(
            add_box(
                f"limp_arm_{index}",
                ash,
                size=(0.13, 0.14, 0.72),
                location=(side * 0.34, -0.20, 1.05),
                rotation=(
                    math.radians(9.0),
                    0.0,
                    side * math.radians(7.0),
                ),
            )
        )
        objects.append(
            add_box(
                f"hand_{index}",
                ash,
                size=(0.14, 0.15, 0.16),
                location=(side * 0.38, -0.25, 0.68),
            )
        )

    # mattock: broad horizontal read across the body, with a hooked iron head
    objects.append(
        add_cylinder(
            "mattock_handle",
            iron,
            radius=0.045,
            depth=1.18,
            vertices=6,
            location=(0.0, -0.33, 0.67),
            rotation=(0.0, math.radians(90.0), 0.0),
        )
    )
    objects.append(
        add_box(
            "mattock_head",
            iron,
            size=(0.13, 0.10, 0.46),
            location=(-0.58, -0.33, 0.74),
            rotation=(0.0, math.radians(-12.0), 0.0),
        )
    )

    # wrist_chain: three oversized links survive the sprite downsample
    for index in range(3):
        objects.append(
            add_torus(
                f"wrist_chain_{index}",
                iron,
                major_radius=0.075,
                minor_radius=0.025,
                major_segments=6,
                minor_segments=4,
                location=(0.39, -0.25, 0.60 - index * 0.14),
                rotation=(math.radians(90.0), 0.0, math.radians(90.0 * (index % 2))),
            )
        )

    objects.append(add_anchor("tool", (0.0, -0.33, 0.67), anchor_type="interaction"))
    return objects


@register_builder("root_walker_lowpoly")
def build_root_walker(spec: dict) -> list[bpy.types.Object]:
    """An uprooted trunk walking on a radial crown of roots."""
    objects: list[bpy.types.Object] = []
    wood = "mat_dark_wood"
    foliage = "mat_foliage"
    void = "mat_nightmare_black"

    # splayed_roots: six long wedges give it a completely non-humanoid base
    for index, angle_deg in enumerate((5.0, 62.0, 122.0, 184.0, 242.0, 304.0)):
        angle = math.radians(angle_deg)
        objects.append(
            add_cone(
                f"splayed_root_{index}",
                wood,
                radius=0.14,
                radius_top=0.045,
                depth=1.18,
                vertices=5,
                location=(math.cos(angle) * 0.47, math.sin(angle) * 0.47, 0.16),
                rotation=(0.0, math.radians(72.0), angle),
            )
        )

    # split_trunk: two leaning halves leave a black crack between them
    objects.append(
        add_cone(
            "split_trunk_left",
            wood,
            radius=0.38,
            radius_top=0.24,
            depth=1.70,
            vertices=7,
            location=(-0.18, 0.0, 1.05),
            rotation=(0.0, math.radians(-7.0), math.radians(-4.0)),
        )
    )
    objects.append(
        add_cone(
            "split_trunk_right",
            wood,
            radius=0.34,
            radius_top=0.18,
            depth=1.55,
            vertices=7,
            location=(0.22, 0.03, 1.10),
            rotation=(0.0, math.radians(9.0), math.radians(7.0)),
        )
    )
    objects.append(
        add_box(
            "hollow_heart",
            void,
            size=(0.30, 0.08, 0.50),
            location=(0.02, -0.34, 1.17),
            rotation=(math.radians(4.0), 0.0, math.radians(5.0)),
        )
    )

    # crooked_branch_arms: strong unequal diagonals
    objects.append(
        add_cylinder(
            "long_branch_arm",
            wood,
            radius=0.10,
            depth=1.48,
            vertices=6,
            location=(-0.67, 0.0, 1.70),
            rotation=(0.0, math.radians(-58.0), math.radians(-18.0)),
        )
    )
    objects.append(
        add_cylinder(
            "long_branch_finger",
            wood,
            radius=0.055,
            depth=0.58,
            vertices=5,
            location=(-1.17, -0.05, 2.16),
            rotation=(0.0, math.radians(-35.0), math.radians(15.0)),
        )
    )
    objects.append(
        add_cylinder(
            "short_branch_arm",
            wood,
            radius=0.11,
            depth=1.00,
            vertices=6,
            location=(0.58, 0.02, 1.56),
            rotation=(0.0, math.radians(58.0), math.radians(12.0)),
        )
    )
    objects.append(
        add_cylinder(
            "short_branch_finger",
            wood,
            radius=0.05,
            depth=0.46,
            vertices=5,
            location=(0.95, -0.04, 1.82),
            rotation=(0.0, math.radians(37.0), math.radians(-18.0)),
        )
    )

    # dead_crown: sparse, asymmetric clumps rather than a healthy tree canopy
    objects.append(
        add_icosphere(
            "dead_crown_left",
            foliage,
            radius=0.34,
            subdivisions=1,
            location=(-0.28, 0.02, 2.25),
            scale=(1.15, 0.75, 0.75),
        )
    )
    objects.append(
        add_icosphere(
            "dead_crown_high",
            foliage,
            radius=0.27,
            subdivisions=1,
            location=(0.20, 0.04, 2.48),
            scale=(0.75, 0.65, 1.10),
        )
    )

    objects.append(add_anchor("heart", (0.02, -0.38, 1.17), anchor_type="interaction"))
    return objects


@register_builder("bell_mimic_lowpoly")
def build_bell_mimic(spec: dict) -> list[bpy.types.Object]:
    """A cracked iron bell carried by thin jointed legs, facing -Y."""
    objects: list[bpy.types.Object] = []
    iron = "mat_iron"
    void = "mat_nightmare_black"
    ember = "mat_ember"

    # jointed_legs: insect-like and far too thin for the bell's weight
    for index, side in enumerate((1, -1)):
        objects.append(
            add_box(
                f"upper_leg_{index}",
                void,
                size=(0.12, 0.14, 0.56),
                location=(side * 0.30, 0.02, 0.46),
                rotation=(0.0, 0.0, side * math.radians(17.0)),
            )
        )
        objects.append(
            add_box(
                f"lower_leg_{index}",
                void,
                size=(0.10, 0.32, 0.46),
                location=(side * 0.42, -0.09, 0.20),
                rotation=(math.radians(32.0), 0.0, side * math.radians(-9.0)),
            )
        )

    # bell_body: flared iron mass with a thick rim
    objects.append(
        add_cone(
            "bell_body",
            iron,
            radius=0.65,
            radius_top=0.34,
            depth=0.92,
            vertices=10,
            location=(0.0, 0.0, 1.18),
        )
    )
    objects.append(
        add_torus(
            "split_rim",
            iron,
            major_radius=0.58,
            minor_radius=0.09,
            major_segments=10,
            minor_segments=4,
            location=(0.0, 0.0, 0.72),
        )
    )
    # A forward-facing void turns the lower rim into an open mouth at iso view.
    objects.append(
        add_box(
            "mouth_void",
            void,
            size=(0.62, 0.10, 0.30),
            location=(0.0, -0.52, 0.83),
            rotation=(math.radians(-5.0), 0.0, 0.0),
        )
    )
    objects.append(
        add_box(
            "rim_crack",
            void,
            size=(0.08, 0.11, 0.42),
            location=(0.22, -0.49, 1.05),
            rotation=(0.0, 0.0, math.radians(18.0)),
        )
    )

    # clapper_tongue: the only hot colour, hanging below the mouth
    objects.append(
        add_cylinder(
            "clapper_stem",
            ember,
            radius=0.055,
            depth=0.52,
            vertices=6,
            location=(0.0, -0.02, 0.62),
        )
    )
    objects.append(
        add_icosphere(
            "clapper_tongue",
            ember,
            radius=0.14,
            subdivisions=1,
            location=(0.0, -0.02, 0.34),
            scale=(0.75, 0.75, 1.0),
        )
    )

    # crooked_yoke: lopsided timber shape rendered in iron, like a false gallows
    objects.append(
        add_box(
            "crooked_yoke",
            iron,
            size=(1.22, 0.18, 0.18),
            location=(0.0, 0.0, 1.82),
            rotation=(0.0, 0.0, math.radians(6.0)),
        )
    )
    objects.append(
        add_box(
            "yoke_post",
            iron,
            size=(0.16, 0.18, 0.62),
            location=(-0.48, 0.0, 1.62),
            rotation=(0.0, 0.0, math.radians(-8.0)),
        )
    )
    objects.append(
        add_torus(
            "hanger",
            iron,
            major_radius=0.14,
            minor_radius=0.04,
            major_segments=8,
            minor_segments=4,
            location=(0.0, 0.0, 1.70),
            rotation=(math.radians(90.0), 0.0, 0.0),
        )
    )

    objects.append(add_anchor("bell", (0.0, -0.52, 1.05), anchor_type="interaction"))
    return objects


@register_builder("hollow_deer_lowpoly")
def build_hollow_deer(spec: dict) -> list[bpy.types.Object]:
    """A skeletal deer with an open black rib cage, facing -Y."""
    objects: list[bpy.types.Object] = []
    bone = "mat_bone"
    void = "mat_nightmare_black"
    ash = "mat_ash"

    # thin_legs: stilt-like, with the front pair slightly buckled
    leg_positions = (
        (-0.28, -0.40, 0.53, 5.0),
        (0.28, -0.40, 0.53, -7.0),
        (-0.28, 0.48, 0.53, -4.0),
        (0.28, 0.48, 0.53, 6.0),
    )
    for index, (x, y, z, lean) in enumerate(leg_positions):
        objects.append(
            add_box(
                f"thin_leg_{index}",
                ash,
                size=(0.11, 0.12, 1.06),
                location=(x, y, z),
                rotation=(math.radians(lean), 0.0, math.radians(lean * 0.45)),
            )
        )

    # hollow_body: black void mass is deliberately enclosed by pale ribs
    objects.append(
        add_box(
            "hollow_body",
            void,
            size=(0.62, 1.22, 0.54),
            location=(0.0, 0.05, 1.22),
        )
    )
    objects.append(
        add_box(
            "haunches",
            ash,
            size=(0.66, 0.48, 0.60),
            location=(0.0, 0.53, 1.23),
            rotation=(math.radians(-8.0), 0.0, 0.0),
        )
    )

    # exposed_ribs: three pale hoops around the void cavity
    for index, y in enumerate((-0.26, 0.02, 0.30)):
        objects.append(
            add_torus(
                f"exposed_rib_{index}",
                bone,
                major_radius=0.34,
                minor_radius=0.045,
                major_segments=8,
                minor_segments=4,
                location=(0.0, y, 1.24),
                rotation=(math.radians(90.0), 0.0, 0.0),
            )
        )
    objects.append(
        add_box(
            "spine",
            bone,
            size=(0.10, 1.18, 0.10),
            location=(0.0, 0.05, 1.48),
        )
    )

    # lowered_skull and long neck
    objects.append(
        add_box(
            "neck",
            ash,
            size=(0.22, 0.62, 0.28),
            location=(0.0, -0.64, 1.44),
            rotation=(math.radians(42.0), 0.0, 0.0),
        )
    )
    objects.append(
        add_box(
            "lowered_skull",
            bone,
            size=(0.32, 0.46, 0.28),
            location=(0.0, -0.96, 1.25),
            rotation=(math.radians(18.0), 0.0, 0.0),
        )
    )
    objects.append(
        add_box(
            "void_face",
            void,
            size=(0.20, 0.07, 0.16),
            location=(0.0, -1.20, 1.24),
        )
    )

    # broken_antlers: attached pedicles and mismatched beams, unlike the noble stag
    for index, side in enumerate((1, -1)):
        objects.append(
            add_box(
                f"antler_pedicle_{index}",
                bone,
                size=(0.08, 0.09, 0.28),
                location=(side * 0.11, -0.98, 1.48),
                rotation=(0.0, side * math.radians(10.0), side * math.radians(-5.0)),
            )
        )
        objects.append(
            add_box(
                f"antler_beam_{index}",
                bone,
                size=(0.08, 0.09, 0.52 if side > 0 else 0.38),
                location=(side * 0.22, -0.98, 1.70 if side > 0 else 1.63),
                rotation=(0.0, side * math.radians(18.0), side * math.radians(-16.0)),
            )
        )
        if side > 0:
            objects.append(
                add_box(
                    f"antler_tine_{index}",
                    bone,
                    size=(0.07, 0.07, 0.30),
                    location=(side * 0.37, -0.98, 1.90),
                    rotation=(0.0, side * math.radians(14.0), side * math.radians(-34.0)),
                )
            )

    objects.append(add_anchor("head", (0.0, -1.20, 1.25), anchor_type="interaction"))
    return objects


@register_builder("charcoal_dead_lowpoly")
def build_charcoal_dead(spec: dict) -> list[bpy.types.Object]:
    """A blackened corpse bowed under a charcoal sack, facing -Y."""
    objects: list[bpy.types.Object] = []
    coal = "mat_nightmare_black"
    ash = "mat_ash"
    ember = "mat_ember"

    # brittle_legs and angular feet
    for index, side in enumerate((1, -1)):
        objects.append(
            add_box(
                f"brittle_leg_{index}",
                coal,
                size=(0.13, 0.14, 0.68),
                location=(side * 0.15, 0.03, 0.34),
                rotation=(math.radians(-5.0), 0.0, side * math.radians(8.0)),
            )
        )
        objects.append(
            add_box(
                f"burned_foot_{index}",
                coal,
                size=(0.15, 0.28, 0.09),
                location=(side * 0.16, -0.08, 0.05),
            )
        )

    # burned_body is narrow; the sack supplies the silhouette's weight
    objects.append(
        add_box(
            "burned_body",
            coal,
            size=(0.42, 0.30, 0.88),
            location=(0.0, -0.04, 1.10),
            rotation=(math.radians(15.0), 0.0, 0.0),
        )
    )
    objects.append(
        add_icosphere(
            "charcoal_sack",
            coal,
            radius=0.47,
            subdivisions=1,
            location=(0.0, 0.30, 1.30),
            rotation=(math.radians(-14.0), 0.0, math.radians(7.0)),
            scale=(0.90, 0.70, 1.25),
        )
    )
    objects.append(
        add_box(
            "sack_lip",
            ash,
            size=(0.42, 0.18, 0.12),
            location=(0.0, 0.26, 1.84),
            rotation=(math.radians(-10.0), 0.0, math.radians(7.0)),
        )
    )

    # ash_crust on shoulders and forearms
    objects.append(
        add_box(
            "ash_crust",
            ash,
            size=(0.60, 0.34, 0.17),
            location=(0.0, -0.13, 1.50),
            rotation=(math.radians(15.0), 0.0, 0.0),
        )
    )
    for index, side in enumerate((1, -1)):
        objects.append(
            add_box(
                f"brittle_arm_{index}",
                coal,
                size=(0.12, 0.14, 0.68),
                location=(side * 0.31, -0.14, 1.08),
                rotation=(math.radians(8.0), 0.0, side * math.radians(8.0)),
            )
        )
        objects.append(
            add_box(
                f"ash_forearm_{index}",
                ash,
                size=(0.13, 0.15, 0.23),
                location=(side * 0.35, -0.18, 0.79),
            )
        )

    # bowed_head plus three chunky ember cracks
    objects.append(
        add_box(
            "bowed_head",
            coal,
            size=(0.25, 0.25, 0.29),
            location=(0.0, -0.31, 1.64),
            rotation=(math.radians(34.0), 0.0, 0.0),
        )
    )
    objects.append(
        add_box(
            "ember_chest",
            ember,
            size=(0.07, 0.05, 0.34),
            location=(-0.07, -0.22, 1.18),
            rotation=(0.0, 0.0, math.radians(16.0)),
        )
    )
    objects.append(
        add_box(
            "ember_face",
            ember,
            size=(0.10, 0.05, 0.05),
            location=(0.05, -0.45, 1.62),
            rotation=(0.0, 0.0, math.radians(-12.0)),
        )
    )
    objects.append(
        add_box(
            "ember_sack",
            ember,
            size=(0.06, 0.05, 0.22),
            location=(0.22, 0.62, 1.34),
            rotation=(0.0, 0.0, math.radians(-24.0)),
        )
    )

    objects.append(add_anchor("ember", (-0.07, -0.24, 1.18), anchor_type="interaction"))
    return objects


@register_builder("sacred_flame_t1")
def build_sacred_flame(spec: dict) -> list[bpy.types.Object]:
    """The abbey's eternal flame in a broad, shrine-marked brazier."""
    objects: list[bpy.types.Object] = []
    stone = "mat_old_stone"
    flame = "mat_flame"
    gold = "mat_sacred_gold"

    # brazier and rim: broad enough to read as an objective beacon
    objects.append(
        add_cone(
            "brazier",
            stone,
            radius=0.55,
            radius_top=0.42,
            depth=0.56,
            vertices=8,
            location=(0.0, 0.0, 0.40),
        )
    )
    objects.append(
        add_torus(
            "rim",
            stone,
            major_radius=0.48,
            minor_radius=0.10,
            major_segments=8,
            minor_segments=4,
            location=(0.0, 0.0, 0.68),
        )
    )
    objects.append(
        add_box(
            "plinth",
            stone,
            size=(0.82, 0.82, 0.20),
            location=(0.0, 0.0, 0.10),
            rotation=(0.0, 0.0, math.radians(45.0)),
        )
    )

    # sacred_marks: four heavy gold tabs around the rim
    for index, (x, y, angle) in enumerate(
        ((0.0, -0.52, 0.0), (0.52, 0.0, 90.0), (0.0, 0.52, 0.0), (-0.52, 0.0, 90.0))
    ):
        objects.append(
            add_box(
                f"sacred_mark_{index}",
                gold,
                size=(0.19, 0.07, 0.22),
                location=(x, y, 0.61),
                rotation=(0.0, 0.0, math.radians(angle)),
            )
        )

    # triple_flame: three interlocking, tilted tongues form a crown silhouette
    objects.append(
        add_cone(
            "flame_centre",
            flame,
            radius=0.31,
            depth=1.05,
            vertices=6,
            location=(0.0, 0.0, 1.15),
            rotation=(math.radians(-4.0), 0.0, 0.0),
        )
    )
    objects.append(
        add_cone(
            "flame_left",
            flame,
            radius=0.22,
            depth=0.78,
            vertices=6,
            location=(-0.24, 0.0, 1.06),
            rotation=(0.0, math.radians(-19.0), math.radians(-8.0)),
        )
    )
    objects.append(
        add_cone(
            "flame_right",
            flame,
            radius=0.20,
            depth=0.70,
            vertices=6,
            location=(0.24, 0.03, 1.03),
            rotation=(0.0, math.radians(22.0), math.radians(9.0)),
        )
    )
    objects.append(
        add_icosphere(
            "golden_heart",
            gold,
            radius=0.22,
            subdivisions=1,
            location=(0.0, -0.08, 0.88),
            scale=(1.0, 0.75, 1.20),
        )
    )

    objects.append(add_anchor("flame", (0.0, 0.0, 1.18), anchor_type="light"))
    return objects
