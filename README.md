A small, standalone repository for running headless Blender asset-generation scripts on GitHub Actions.

This repository contains generic procedural Blender tooling only. It is intentionally separate from the private CENTS game repository.

## Run the smoke test

1. Open the **Actions** tab.
2. Select **Blender Asset Pipeline Smoke Test**.
3. Choose **Run workflow**.
4. After it completes, download the `cents-blender-pipeline-smoke-test` artifact.

The workflow installs Blender on a GitHub-hosted Linux runner, generates a disposable two-storey commercial facade, exports it as a GLB, and uploads the result.

The smoke-test facade is only an export-pipeline check. It is not an approved final CENTS art style or production asset.

## Private CENTS validation (public runner)

The **CENTS Private Repo Validation** workflow runs manually from this public repository and checks out the selected branch of the private `tryyy8/CENTS` repository into the temporary GitHub Actions runner. It runs tests, TypeScript type-checking, and the Vite production build for `cents-game-prototype`, or the bridge regression tests for `cents-dev-bridge`.

No CENTS source is committed to this repository, no build output is published, and the private checkout is removed with the temporary runner.

### One-time setup

Create a fine-grained personal access token in GitHub with access to **only** `tryyy8/CENTS` and **Contents: Read-only** permission. Add that token under **Settings → Secrets and variables → Actions** in this `tryyy8/blender` repository, using the exact secret name:

`CENTS_READ_TOKEN`

Do not paste the token into source files, workflow YAML, or chat. The workflow uses it only to read the private CENTS repository.

## Local command

```bash
blender --background --python tools/blender/pipeline_smoke_test.py -- --output /tmp/blender-pipeline-test.glb
```

## License and scope

The scripts are generic procedural tooling. Keep game source, private design documents, credentials, and unreleased CENTS content out of this repository.
