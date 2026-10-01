# Vendored MediaPipe

- Package: `@mediapipe/tasks-vision` **1.0.1** (npm), Apache-2.0, © Google LLC.
  - `vision_bundle.mjs` — the ES module (its `sourceMappingURL` comment was stripped; the map is not vendored).
  - `wasm/vision_wasm_internal.{js,wasm}` — the SIMD build. The `nosimd` build is **not** vendored:
    every current browser (Safari ≥ 16.4, Chrome, Firefox) supports wasm SIMD. If an old device
    fails to load, add `vision_wasm_nosimd_internal.{js,wasm}` from the same package version.
- Models (`../../models/`), from `storage.googleapis.com/mediapipe-models/pose_landmarker/…/float16/latest/`:
  - `pose_landmarker_lite.task` — live camera default (fast).
  - `pose_landmarker_full.task` — video analysis and the "Tarkka" live option.
  Model card: https://storage.googleapis.com/mediapipe-assets/Model%20Card%20BlazePose%20GHUM%203D.pdf

License text: https://www.apache.org/licenses/LICENSE-2.0

To update: download the npm tarball
(`https://registry.npmjs.org/@mediapipe/tasks-vision/-/tasks-vision-<ver>.tgz`), copy the files
above, strip the source-map comment, and re-run the app's manual checks (the `PoseLandmarker`
API and the result's `close()` have changed between versions before).
