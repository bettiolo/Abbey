# Merchant Shade Mini World sprite placeholders

This folder contains a curated, replaceable subset of Shade and octoshrimpy's
[Free 16x16 Mini World Sprites](https://merchant-shade.itch.io/16x16-mini-world-sprites).
The official itch.io page identifies the pack as **CC0 1.0 Universal**, permits
commercial and noncommercial use and modification, and does not require attribution.
The authors ask that the pack itself not be sold as a standalone asset collection.

`manifest.json` is the source of truth for provenance, hashes, dimensions, exact
bottom-left slice rectangles, import pivots, PPU, stable role mappings, animation
frames, visual scale, sorting, tint participation, authored obstacle footprints, and
honestly unresolved roles. Generic committed PNGs are byte-identical copies of selected
source sheets; the full archive and guide remain in ignored `third_party_cache/`.

`AbbeyGeneratedIdentity/` contains derived sprite sheets for signature objects that the
CC0 pack cannot honestly represent. They are deterministically rendered from the
repository's validated asset specs and generated GLBs by
`blender/scripts/render_identity_sprites.py`. Each generated sheet records the hashes of
its source spec, GLB, renderer, and PNG in the same manifest. They do not change the
license or authorship of the Merchant Shade source sheets.

Acquisition pin:

- itch game: `703908`
- itch upload: `7054436` (`MiniWorldSprites.zip`)
- archive size: `2,084,074` bytes
- SHA-256: `79eb000cfd3f64fee8ac8307f02bb867dc8b4fd7ce5a150119c51dedfa563f1f`
- acquired: `2026-07-10`
- authors: Shade and octoshrimpy
- license: [CC0 1.0 Universal](https://creativecommons.org/publicdomain/zero/1.0/)

Reproduce and validate locally:

```sh
uv run --with-requirements tools/requirements-dev.txt \
  python tools/acquire_merchant_shade_miniworld.py
/opt/homebrew/bin/blender -b --factory-startup \
  -P blender/scripts/render_identity_sprites.py -- --repo-root . --all
uv run --with-requirements tools/requirements-dev.txt \
  python tools/sync_identity_sprite_manifest.py
uv run --with pillow python \
  tools/validate_merchant_shade_miniworld.py --write-reports
uv run --with-requirements tools/requirements-dev.txt \
  python tools/validate_merchant_shade_miniworld.py --with-cache
```

`contact-sheet.png` shows every named slice at integer nearest-neighbour scale, and
`inventory.md` lists every selected source sheet, mapped role, and unresolved role.
The contact sheet is inventory evidence, not runtime art.

The generated identity pass resolves the Bellkeeper, Black Hound, Stag, ruined Bell
Tower, cloister, campfire, lantern, charcoal kiln, shipwreck pieces, hound chain, and
five signature nightmares without dishonest third-party proxies. Six roles remain
explicitly unresolved: Dead Worker, Root Walker, Bell Mimic, Hollow Deer, Charcoal
Dead, and the sacred flame. Those retain the reversible 3D fallback until their own
validated specs and readable sprite sheets exist.
