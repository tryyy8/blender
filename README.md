# Blender Asset Generator

A small, standalone repository for running headless Blender asset-generation scripts on GitHub Actions.

This repository contains generic procedural Blender tooling only. It is intentionally separate from the private CENTS game repository.

## Run the smoke test

1. Open the **Actions** tab.
2. Select **Blender Asset Pipeline Smoke Test**.
3. Choose **Run workflow**.
4. After it completes, download the `cents-blender-pipeline-smoke-test` artifact.

The workflow installs Blender on a GitHub-hosted Linux runner, generates a disposable two-storey commercial facade, exports it as a GLB, and uploads the result.

The smoke-test facade is only an export-pipeline check. It is not an approved final CENTS art style or production asset.

## Local command

```bash
blender --background --python tools/blender/pipeline_smoke_test.py -- --output /tmp/blender-pipeline-test.glb
```

## License and scope

The scripts are generic procedural tooling. Keep game source, private design documents, credentials, and unreleased CENTS content out of this repository.
