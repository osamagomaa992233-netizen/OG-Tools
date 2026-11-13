# OG Tools v0.8 — Windows packaging work, not a finished extension

- Added one-click Windows setup from source (`INSTALL_OG_TOOLS.cmd`). It automates a Python virtual environment, Faster-Whisper, Pillow, FFmpeg download when missing, copying UXP panel and configuring autostart. **Not tested on Windows.**
- Added GitHub Actions **Windows portable build** that freezes the local engine into an `.exe`, bundles FFmpeg, and runs a localhost HTTP health smoke test before uploading a release ZIP. **Workflow not run yet.** This ZIP contains workflow/source, **not** the Windows binary.
- The setup uses an **unofficial External UXP folder fallback**, which may require developer mode and is not a verified substitute for Adobe's supported `.ccx` workflow. See Adobe documentation for verified distribution; only UXP Developer Tool can currently produce a validated CCX package with our toolchain.
- Local caption recognition requires the first Whisper model download. Native Premiere timeline effects remain untested.
- No completed new motion features are claimed in this build. Earlier v0.7 rendering / native mocked-keyframe capabilities are retained.

## Reality check

This is not yet the final ready-to-use Premiere plugin. Users should not be instructed to run it as though all 21 features are complete. Never claim UXP integration passed without actual Premiere host testing.
