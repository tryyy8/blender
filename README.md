A small, standalone repository for running headless Blender asset-generation scripts on GitHub Actions.

This repository contains generic procedural Blender tooling only. It is intentionally separate from the private CENTS game repository.

## Run the smoke test

1. Open the **Actions** tab.
2. Select **Blender Asset Pipeline Smoke Test**.
3. Choose **Run workflow**.
4. After it completes, download the `cents-blender-pipeline-smoke-test` artifact.

The workflow installs Blender on a GitHub-hosted Linux runner, generates a disposable two-storey commercial facade, exports it as a GLB, and uploads the result.

The smoke-test facade is only an export-pipeline check. It is not an approved final CENTS art style or production asset.

For normal assistant-operated CENTS development, use the private CENTS Dev Bridge queue. Its Android/Termux controller accepts bounded jobs and publishes results back to GitHub. If the phone-side bridge is unavailable, the assistant can trigger the public-runner fallback by updating `.github/cents-validation/request.json`; no one needs to open Actions or select a branch manually. The manual `workflow_dispatch` option remains available as a human fallback.

## Private CENTS validation (public runner)

The **CENTS Private Repo Validation** workflow is triggered either by a push to `.github/cents-validation/request.json` on `main`, or manually through `workflow_dispatch`. The request file contains only a request ID and an allowlisted private branch name (`cents-game-prototype` or `cents-dev-bridge`). The workflow validates that branch, checks out the selected private `tryyy8/CENTS` branch into the temporary GitHub Actions runner, and runs tests, TypeScript type-checking, and the Vite production build for the game branch, or bridge regression tests for the bridge branch. The assistant can create/update the request file to trigger a run and inspect the resulting workflow run and logs.

No CENTS source is committed to this repository, no build output is published, and the private checkout is removed with the temporary runner.

### One-time setup

Create a fine-grained personal access token in GitHub with access to **only** `tryyy8/CENTS` and **Contents: Read-only** permission. Add that token under **Settings → Secrets and variables → Actions** in this `tryyy8/blender` repository, using the exact secret name:

`CENTS_READ_TOKEN`

Do not paste the token into source files, workflow YAML, or chat. The workflow uses it only to read the private CENTS repository.

## CENTS material identity study

The material pipeline includes a controlled comparison asset with six identical UV-sphere samples: stone, lime plaster, timber, brushed metal, concrete, and asphalt. Each family has separate deterministic pattern logic and exports packed base-colour, roughness, and tangent-normal maps. The reusable implementations live in `tools/blender/cents_materials.py` and are used by both the comparison study and the District 01 commercial-building generator.

Generate the comparison asset locally:

```bash
blender --background --python tools/blender/cents_material_identity_study.py -- --output /tmp/cents-material-study.glb --size 384
```

The exported GLB is self-contained. A successful export validates the map/export path, not final visual approval; the materials still require comparison in the actual PlayCanvas scene under common lighting.

Generate the reusable modular retail-store asset study locally:

```bash
blender --background --python tools/blender/retail_store_kit.py -- --output /tmp/retail-store-kit.glb --texture-size 256
```

The kit keeps the shell, perimeter shelving, gondolas, chillers, checkout, stockroom, product displays, and lighting as separate modules, joining geometry by material within each module. It is generic pipeline tooling; game-specific branding and design stay in the private CENTS repository.

## Local command

```bash
blender --background --python tools/blender/pipeline_smoke_test.py -- --output /tmp/blender-pipeline-test.glb
```

## License and scope

The scripts are generic procedural tooling. Keep game source, private design documents, credentials, and unreleased CENTS content out of this repository.


### Assistant-triggered fallback request

To trigger validation without manually using the Actions interface, create or update this public request file on `main`:

```json
{
  "request_id": "unique-request-id",
  "cents_branch": "cents-game-prototype"
}
```

Only the two allowlisted private branches are accepted. The request file contains no token, CENTS source, build output, or private project data. The runner checks out the private source temporarily, runs the selected checks, and does not upload the source or build artifacts. Updating the request ID creates a new push event and a new validation run.
