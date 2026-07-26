# P2D reversible sprite-projection candidate

Validated locally on 2026-07-26 at runtime commit `0f2d678` with Unity `6000.5.2f1`.

## Implemented candidate

- Curated and pinned the official Merchant Shade / octoshrimpy Mini World Sprites archive
  under CC0 1.0. The hybrid committed catalog contains 48 sheets, 381 deterministic
  slices, and 78 mapped Abbey roles.
- Added a spec-owned identity bake for roles that the generic pack cannot represent.
  Sixteen validated Abbey asset specs now produce palette-quantized, bottom-anchored
  sprite sheets from their generated GLBs with exact spec, renderer, and output hashes
  plus a cross-exporter structural GLB fingerprint. Repeated Blender runs produce
  byte-identical PNGs.
- Generated texture import settings and `MiniWorldSpriteProjectionCatalog.asset` from the
  manifest; the importer and validator reject source drift, path traversal, bad geometry,
  duplicate identities, invalid footprints, and catalog drift.
- Added a reversible presentation child that never changes gameplay-root transforms,
  collision, movement, jobs, combat, or tick order. Disabling projection restores every
  legacy renderer's previous enabled state.
- Added four-direction walk animation, camera-facing actors/buildings/props, dense stable
  projected-depth ordering, reversible authored wall footprints, phase tint, runtime-spawn
  registration, and XZ-tiled terrain patches.
- Committed a data-owned projection switch and style asset; disabling the switch before
  regenerating a map restores legacy renderers and legacy obstacle footprints.
- Integrated both generated maps while preserving scene names and all existing gameplay
  components.

## Authoritative verification

- Unity MCP gate: passed; Prototype01 and Map2Prototype built.
- Sprite manifest/import/catalog validation: passed.
- EditMode: 418/418 passed.
- PlayMode: 72/72 passed.
- Unity console errors: 0.
- Canonical images inspected: `day_camp`, `dusk_recall`, `night_attack`, `morning_after`,
  `map2_grove_day`, and `map2_false_bell_night`.
- `./tools/check_all.sh`: OK; design 7/7, assets 357 passed / 8 skipped, Blender changed
  verification clean. Unity batch steps skipped because the MCP editor held the project
  lock; the authoritative MCP results above cover them.

## Honest visual blocker

The identity bake resolves 17 of the 23 original gaps: the Bellkeeper, Black Hound, Stag,
ruined bell tower, cloister and repair state, campfire, lantern post, charcoal kiln,
shipwreck pieces, hound chain, Pale Hound, Drowned Sailor, Lantern Moth, Chain Hound, and
Faceless Saint. Six roles remain unresolved: Dead Worker, Root Walker, Bell Mimic, Hollow
Deer, Charcoal Dead, and Sacred Flame. The manifest records every missing role and its
reason; those objects deliberately retain the reversible 3D identity instead of receiving
a misleading substitute.

Consequently this branch is a draft technical candidate, not an approved final art pass.
`P2D-07` remains in progress and `GATE-P2D-ART` remains pending until those gaps are either
filled from reviewed compatible sources or explicitly accepted at the human art review.
