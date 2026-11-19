# CENTS Asset Sourcing and Blender Workflow

**Authority:** The creator's explicit requirements and the current CENTS design documents take precedence over older scripts, generated assets, examples, and workflow history.

## 1. Non-negotiable production-store requirement

The CENTS starter business must use an **already-built, complete convenience-store environment sourced from an existing downloadable 3D asset**.

The selected source model must already contain the building and its architectural environment: floor, walls, ceiling, storefront, windows/glazing, entrance/doors, and architectural lighting or fixtures. Prefer a source that also includes its retail shelving, beverage coolers, checkout, and interior arrangement.

**Do not create the store building or shell in Blender or in game code.** Do not generate a floor, walls, ceiling, roof, storefront, entrance, windows, or architectural lighting from primitives. Do not assemble a pretend "premade building" from individual downloaded walls, doors, windows, and floor pieces. That is still constructing the building and does not satisfy the requirement.

A complete environment is one existing authored environment asset (or a source package explicitly sold/published as a complete store scene). Blender may be used only to inspect, validate, convert, optimize, or make narrowly scoped, approved edits to that imported environment. Importing the complete scene and preserving its architecture is the default.

## 2. Required sourcing and approval sequence

1. Search for complete convenience-store environments, not isolated fixtures or generic retail kits.
2. Match the CENTS brief before considering technical convenience: a conventional independent neighborhood convenience store, not a Japanese konbini, futuristic/cyberpunk shop, supermarket, petrol station, or big-box store.
3. Inspect actual model previews and, whenever downloadable, inspect the actual model geometry and materials. Do not select from a title or thumbnail alone.
4. Verify the exact license and commercial-game permissions. Record the source page, creator, license, attribution requirements, modification rights, and redistribution restrictions.
5. Check scale, layout, camera suitability, mobile performance, and whether the environment has the architectural elements required above.
6. Present the candidate and any meaningful compromises for creator approval when its visual identity or fit is uncertain.
7. Download and integrate the complete environment asset. Keep its source architecture intact.
8. Only then add, replace, or adjust individual fixtures and gameplay objects where required. Preserve approved CENTS merchandise families when practical.
9. Validate the imported result in the actual CENTS runtime and inspect fresh screenshots. A successful download, import, export, or build is not visual approval.

If no suitable free asset is found, continue searching and report the limitation. Do not quietly fall back to a procedural shell or a fixture kit.

## 3. CENTS visual direction

The game's confirmed art direction is **stylized realism**.

- Grounded, recognizable real-world objects and believable construction.
- A deliberate, coherent authored visual identity across shape, silhouette, proportion, material, color, and lighting.
- More visibly art-directed than photorealism, without becoming toy-like, generic low-poly, plastic, or conventional cartoon rendering.
- Avoid thick outlines, global cel-shading bands, and post-processing as substitutes for authored asset identity.

The first business is a conventional, standalone neighborhood convenience store. Avoid Japanese-hybrid, futuristic, cyberpunk, supermarket, petrol-station, and oversized industrial cues. Keep final store branding and palette open unless the creator confirms them.

## 4. Blender's permitted role

Blender remains useful for:
- Inspecting source scenes, mesh bounds, transforms, materials, UVs, and object organization.
- Converting an existing complete environment to a runtime-compatible format.
- Optimizing imported geometry, textures, and draw calls without changing its identity.
- Fixing import/export defects and making explicitly approved, limited edits.
- Creating or refining separate merchandise and gameplay props where the creator has approved that work.

Blender is **not** authorized to generate the production store architecture. No script or workflow may recreate the rejected store-shell generator under another name.

## 5. Retired production path

The scripted cents_convenience_rebuild.py store-shell builder and the retail_store_kit.py complete-store generator are retired and must not be restored as the production-store path. The automated Blender workflow must not generate or publish a procedural CENTS convenience-store building. Standalone material, district, and merchandise studies may continue, but they are not the production store and must not be presented as one.

Older generated retail-store-kit.glb files are not evidence of a pre-built source environment and must not be used to claim this requirement has been met.

## 6. Quality and release checks

Before calling the production environment integrated:
- [ ] The source is one complete, pre-built convenience-store environment.
- [ ] The source is visually appropriate for the conventional neighborhood-store brief.
- [ ] The exact commercial-use license has been checked and recorded.
- [ ] The downloaded model itself has been inspected, not just its preview image.
- [ ] The source architecture remains intact; no scripted shell was generated.
- [ ] Any fixture changes are limited to concrete gameplay or compatibility needs.
- [ ] Scale, materials, textures, normals, transforms, and object bounds are validated.
- [ ] CENTS tests, typecheck, and production build pass.
- [ ] The live preview is restarted and a fresh screenshot is captured.
- [ ] The actual in-game view is visually inspected before approval.

**Core rule:** Source the complete store. Do not build the building.