# Build Skill

Run `powershell -ExecutionPolicy Bypass -File tools/build.ps1`. It checks the required Harness layout and Python entry-point compilation. Record any failure in `MISTAKES.md`.

V1.1: `tools/build.ps1` checks actual Python source syntax. Target projects must configure their business build command in `.harness/config.json`. See `docs/V1.1.md`.
