# CENTS AI-Assisted Blender Asset Workflow

This document records the repeatable workflow used to author and validate CENTS retail fixtures and merchandise with Blender Python. It is intended as the starting point for future asset passes. It describes the actual repository pipeline and the design/QA rules learned from the convenience-store fixture rebuild; it is not a claim that every current model has passed visual inspection.

## 1. Repository roles

- `tools/blender/retail_store_kit.py`: store fixtures and architectural retail components (wall bays, gondolas, refrigeration, checkout, ceiling fixtures).
- `tools/blender/cents_packaging.py`: individual merchandise SKUs and placement on fixture shelves.
- `assets/retail-store-kit.glb`: generated runtime asset.
- `.github/workflows/blender-asset-smoke-test.yml`: automated Blender generation, validation, visual asset publication, and model upload.
- CENTS game repository: consumes the generated GLB through an immutable raw GitHub URL in `src/world/loadBlenderRetailStore.ts`.

Keep generic Blender tooling and reusable asset-generation code in this repository. Keep unreleased game logic and private game-specific design notes in the CENTS repository.

## 2. The asset-authoring loop

Use this sequence for every substantial asset change:

1. **Inspect the current generator and scene contract.** Read the target generator, shared helpers, export settings, and the CENTS GLB loader before changing geometry. Record coordinate axes, unit scale, object names, material names, origins, shelf heights, and placement conventions.
2. **Research the real object.** Reference real commercial equipment rather than generic primitives: convenience-store reach-in merchandisers, steel gondola shelving, wall bays, shelf-edge ticket rails, and actual packaged goods. Identify primary silhouette, construction, visible hardware, materials, and how products physically sit in the fixture.
3. **Plan the object as a construction, not a pile of boxes.** Separate primary structure, secondary formed parts, and tertiary details. Model the silhouette and proportions first; then add folded edges, brackets, seams, fasteners, handles, hinges, vents, labels, gaskets, and trim only where they make physical sense.
4. **Build reusable helpers.** Prefer helpers for repeated manufacturing details (beveled panels, formed lips, slotted uprights, shelf brackets, extrusion profiles, labels, handles, hinges, and product closures). Give helpers explicit dimensions, orientation, material, and naming inputs. Avoid a one-off pile of opaque hardcoded mesh calls.
5. **Keep the scene spatially coherent.** Establish fixture dimensions and exact support surfaces before placing products. Derive product positions from shelf deck top surfaces and clearance, not visual guesses. Check door fronts, glass planes, shelf depths, handles, hinges, and rear liners for consistent orientation.
6. **Make products physically complete.** A can needs a closed body and end closures; a bottle needs a continuous body, neck, shoulder, cap, and base; a cup needs a body, rim/lid, and base; flexible pillow packs need front/back print faces joined by a perimeter film or gusset. Avoid two disconnected printed planes masquerading as a package.
7. **Consolidate per SKU only after geometry is assembled.** The packaging generator uses `_consolidate_product(parts, start, label)` and `_emit_product(...)` to create one Blender object per SKU. Joining components improves object organization and export/culling, but **joining is not Boolean union and does not prove mesh connectivity**. Components must physically intersect or be connected by actual geometry; inspect for floating islands and gaps.
8. **Use authored PBR materials.** Assign intentional base color, metallic, roughness, alpha, and emissive values. Metal fixtures should read as coated or brushed metal, not flat gray plastic. Glass should use the runtime-supported glTF alpha workflow and must be evaluated in the actual game renderer. Do not assume alpha blending equals physically accurate refraction.
9. **Export and validate.** Run the repository's Blender asset workflow. Confirm Blender script execution, GLB export, file size, expected object/material presence, and loader compatibility. A successful export is only structural validation, not proof of visual quality.
10. **Inspect the rendered result and iterate.** Capture the live CENTS game view after deployment. Inspect fixture silhouette, scale, placement, occlusion, glass, product contact, intersections, floating pieces, and readability from player height. Change the source generator, rebuild, redeploy, and repeat. Never declare a model visually finished from code or build success alone.

## 3. Fixture-specific construction notes

### Commercial reach-in refrigerators

A convincing commercial merchandiser should read as an insulated refrigerated cabinet, not a transparent box:

- Insulated side cheeks, roof, floor, rear liner, and toe-kick/plinth.
- Multiple framed glass doors with aluminum extrusions, central mullions, magnetic gaskets, handles, and hinges.
- Clear glass panels placed in the door frames; preserve enough frame thickness to read at gameplay distance.
- Internal vertical standards, shelf rails, shelf decks, and front shelf lips.
- Ventilation louvres and compressor/air-return details near the lower cabinet where appropriate.
- Illuminated header/sign band and restrained interior LED channels.
- Products placed behind the glass, aligned to each door bay and resting on the actual shelf decks.

Check that door hardware is on the correct sides, handles are reachable, the glass plane is in front of products, and shelf/product depth does not intersect the door.

### Commercial steel shelving

A convenience-store gondola or wall bay should not look like a timber bookcase:

- Powder-coated steel uprights with repeated adjustment slots.
- Perforated or slotted back panels and structural center spine.
- Formed steel shelf decks with folded front lips and believable depth.
- Cantilever brackets or shelf-support arms beneath each deck.
- Continuous ticket rails with individual price labels.
- Base plinth/kick plate, end frames, end caps, and top sign frame where appropriate.
- Double-sided gondolas need a coherent center spine and shelf decks on both faces.

Check shelf heights against product origins, keep bracketry attached to uprights, and avoid decorative detail that obscures product facings.

## 4. Merchandise construction and QA

- Use a distinct, readable silhouette for each SKU; do not rely on color alone.
- Close the geometry: inspect bottoms, tops, caps, lids, seams, and flexible-pack edges.
- Avoid z-fighting between labels and package surfaces; offset printed surfaces deliberately.
- Ensure every SKU is placed upright unless its design explicitly requires otherwise.
- Derive placement from shelf surface height plus half the product's bounding height and a small clearance.
- Verify that each package has plausible contact with the shelf and does not float, penetrate the deck, or intersect adjacent products.
- Object consolidation is an organizational step only. If disconnected components remain visible, repair the geometry (connect/overlap surfaces or use a controlled Boolean union where appropriate) rather than assuming a joined object is a watertight mesh.
- Check the final exported GLB, not only the Blender viewport: material alpha, normals, transforms, UVs, object origins, and texture references can behave differently after glTF export.

## 5. AI-assisted modeling method

Use AI as a structured modeling and debugging assistant, not as a one-shot text-to-primitives generator:

1. **Planner:** turn the real-world reference into a component list, dimensions, construction order, and spatial constraints.
2. **Retriever:** consult Blender Python API documentation and repository helper patterns before writing code.
3. **Modeler:** implement the components using reusable, parameterized Blender Python functions.
4. **Validator:** check dimensions, transforms, object counts, mesh bounds, normals, material assignments, and placement constraints programmatically.
5. **Visual reviewer:** inspect rendered game captures and identify concrete defects (wrong silhouette, detached details, intersections, incorrect depth, unreadable scale).
6. **Refiner:** make targeted source changes and rerun the exact pipeline. Preserve correct geometry instead of regenerating everything unnecessarily.

Keep a distinction between checks that can be automated (bounds, transforms, missing materials, object counts, file size) and checks that require visual evidence (commercial authenticity, visual hierarchy, believable contact, attractive proportions, readability).

## 6. Current CENTS production-store direction

As of November 18, 2026, the convenience store is the actual game's production environment, not a temporary prototype, sample, or throwaway asset study. Do not describe the current store as a prototype. Design and review it as the first shippable store environment.

The user has reset the visual direction to a classic, conventional convenience store. The previous Japanese-hybrid styling is explicitly dropped. Keep the existing low, light commercial shelving and the useful authored product families, but rebuild the surrounding store environment and replace the custom refrigerator design.

### Preserve and refine

- Keep the current convenience-store wall shelving and low double-sided gondolas, subject to visual review after the new store pass.
- Preserve the existing authored SKU families where they are already working, including Ember Cola and the better-performing package designs.
- Refine snack pouch construction so top heat seals and side seams physically overlap the pouch shell. A joined Blender object is not proof of connected geometry.
- Derive every product origin from the actual shelf top plus a small clearance. Do not retain stale hard-coded elevations after changing fixture geometry.

### Replace

- Replace the custom refrigerator construction with a suitable, commercially reusable, pre-generated glass-door beverage cooler asset when that produces a better result.
- Current selected candidate: Innerscene's double glass-door beverage cooler, 1.2 x 0.787 x 2.0 m, white commercial cabinet, illuminated header, two glass doors, eight wire shelves, condenser grille, and unbranded display stock. It is released under CC0 1.0 and permits commercial use, modification, and redistribution.
- Arrange three cabinets as a continuous beverage wall. Preserve the source model's sensible commercial construction instead of rebuilding it from primitive boxes.
- Rebuild the surrounding store presentation as a classic convenience store: warm neutral interior, practical checkout, readable entrance/storefront, proper ceiling and lighting treatment, and a coherent merchandise layout. Avoid futuristic/Japanese-hybrid cues and oversized industrial fixtures.

### Diagnosed defects and source changes

The November 18 visual handoffs showed nearly opaque black refrigerator fronts, chilled products floating above the cases, and detached-looking pouch seams. Source inspection identified three concrete causes:

1. The custom chilled product elevations did not match the cooler shelf elevations.
2. The game loader applied glTF's default 0.5 alpha cutoff to BLEND materials, discarding low-opacity glass panels. glTF alphaCutoff is only meaningful for MASK materials.
3. The snack pouch top seal and side seams were positioned outside the tapered film shell.

Corrections:
- `tools/blender/cents_packaging.py`: seal positions now follow the pouch shell; chilled merchandise elevations were aligned; gondola merchandise bases were aligned to the current deck tops.
- `src/world/loadBlenderRetailStore.ts`: alpha cutoff is now zero for OPAQUE and BLEND materials, and defaults to 0.5 only for MASK materials.
- `tests/glb-loader.test.js`: added coverage for the alpha-mode behavior.
- `tools/blender/retail_store_kit.py`: imports the selected CC0 double-door cooler asset, places three commercial units, and avoids overlaying a duplicate set of chilled products.
- `.github/workflows/blender-asset-smoke-test.yml`: downloads the CC0 source asset before Blender generation.

Source commits:
- `7c5a9eb3f9c700226092a7978155a2c9c60eae5c` — pouch seam and chilled product shelf alignment.
- `c4f81d97c7b494b718b9c24f249dfd283f553f8b` — gondola product placement alignment.
- `f4cf6d4e4952424731a6611cfac5361e6e52ad46` — import CC0 commercial cooler asset.
- `4ad97028c4ab527871b710daded75fa024b8fe0d` — download the CC0 cooler in the Blender workflow.
- CENTS `c7f79ed398e114b88435d258dfe828ad38fccab6` / `621a7c09ae498e673bdc4044a8c66d5e679b1ce4` — correct glTF alpha handling.
- CENTS `e26241f6ae85fdae3225f8a8d0aac7cbca13e39b` — alpha-mode regression tests.

The current Blender workflow run is pending. The asset must be inspected in Blender and then in the actual CENTS renderer. Do not approve the new coolers or the overall store from successful download, import, export, or build status alone.

## 7. Release checklist

Before saying an asset pass is complete:

- [ ] Blender workflow completed successfully.
- [ ] Generated GLB exists and its byte size is recorded.
- [ ] Export contains expected fixture and SKU objects/materials.
- [ ] GLB URL in the game loader points to the exact immutable asset commit.
- [ ] CENTS tests, typecheck, and production build pass.
- [ ] Preview server restart is confirmed by bridge result/telemetry.
- [ ] Fresh, non-black screenshots are captured from the running preview.
- [ ] Refrigerator, shelving, and merchandise views are individually inspected.
- [ ] No obvious floating components, shelf intersections, door collisions, or misplaced products remain.
- [ ] Any remaining visual defects are documented and iterated before approval.

## 8. Important failure lessons

- A script that runs is not the same as a good model.
- Joining meshes into one object does not merge their topology.
- A GLB that exports is not necessarily visually correct in the target renderer.
- A screenshot upload that returns HTTP success may still contain an unusable black frame; inspect the actual pixels and compare captures for unexpected duplicates.
- The CENTS WebGL preview needs its drawing buffer preserved for canvas-based screenshots. The game branch has a preview-only `preserveDrawingBuffer` setting for ports `5173` and `4173`; production contexts should not pay this cost.
- Do not lower asset fidelity or remove visual features as the first response to performance or size problems. Measure the generated asset and optimize geometry, materials, and workload deliberately.

## 9. Repeating the workflow next time

For a new asset category, repeat sections 1–5, add a category-specific construction guide, then follow the release checklist. Keep source generators deterministic, parameterized, and easy to review. Prefer measured dimensions and constraints over arbitrary coordinates. Save the resulting asset commit SHA and game-loader URL in the project change record so future passes can reproduce the exact artifact.
