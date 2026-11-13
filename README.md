# OG Tools v0.8 — Windows Setup Engineering Kit

**This is not a production-certified Premiere plugin or finished VOLT replacement.**

Use `INSTALL_OG_TOOLS.cmd` for one-click Windows setup. The script attempts to provision local Python, FFmpeg, Faster-Whisper, a background autostart engine and a UXP panel via the manual External plugin folder. No need to run the old `START_OG_TOOLS_WINDOWS.bat` manually after a successful install, but **the manual UXP folder may not be accepted by Premiere 2026**. This was not executed on Windows.

For a self-contained portable engine *without Python at the user's end*, push this repository to GitHub and run `Build Portable Windows Engine` workflow. The CI script uses PyInstaller, bundles FFmpeg and checks the local engine's health. **Not yet run on Github; no EXE is included in this source ZIP.** The workflow emits an artifact ZIP if it passes.

The current editor functions from v0.7 remain intact. For more details on actual processing, limitations and dependencies, see `RELEASE_NOTES_v0.7.md` and `RELEASE_NOTES_v0.8.md`.

**Known limitations**: Adobe official `.ccx` still needs UXP Developer Tool packaging and Premiere host verification; editable timeline Text/Keyframes only mock tested; Arabic Whisper real recording inference not yet verified; silence cut and speed ramp generate new media rather than editing timeline natively; 21 tools not complete.

# OG Tools Personal — Engineering Build v0.7 (Premiere Pro 2026)

**NEW:** See [RELEASE_NOTES_v0.7.md](RELEASE_NOTES_v0.7.md) for Creator Captions (Arabic word timing + 8 effects), 8 native Creator Zoom keyframe presets, 5 rendered speed-ramp curves and silence cut from selected trimmed clips. **50 tests passed** outside Premiere (33 Python + 17 JavaScript); Premiere host integration remains unverified.

**Important:** This repository is a working local media-processing engine plus a UXP panel prototype. It is **not** a finished 21-tool Premiere extension, not an Adobe-signed `.ccx` installer, and not a VOLT template clone.

## What is actually implemented

The 21 original slots in the panel reflect the VOLT-style workflow categories, but the implementation levels differ. **16 local-capability legacy modules** (when their local dependencies are installed), **4 optional external open-source adapters**, and **1 not implemented**. All directly generated assets use new original designs. Tested on Linux + FFmpeg locally, *not* inside Premiere Pro/Windows.

| Module | Status | What is produced | Premiere limitation |
|---|---|---|---|
| 1. AI captions | Optional faster-whisper | Arabic/English SRT | Not inserted onto timeline automatically; native Premiere transcription not called |
| 2. 30 animated text motions | Local engine | ProRes 4444 MOV alpha | Raster video; not editable MOGRT text/keyframes |
| 3. 3D Text | 2.5D implementation | Simulated extrusion PNG | Not real native 3D layer |
| 4. Text on Path | Partial implementation | Curved PNG, RTL per shaped word | Not fully editable text path; advanced Arabic shaping differs |
| 5. Draw on Video | Local engine | 5 types of ProRes drawing overlays | Import as clip |
| 6. Motion Graphics Templates | Local engine | 12 original title styles PNG / animated via module 2 | No MOGRT assets included |
| 7. Animated Carousel | Local engine | Panning MP4 from 2–20 images | Does not create editable native slide sequence |
| 8. Icon Library | Local engine | 22 original SVG icons | Import into graphics editor; direct SVG import into Premiere may not work |
| 9. Web asset search | **Not implemented** | — | No scraping/search API |
| 10. Downloader | Optional yt-dlp | Downloaded authorized media | Download only media with necessary rights |
| 11. Remove Background | Optional rembg | Transparent image PNG | Still-image backgrounds only, not native Object Mask/video rotoscoping |
| 12. Sound FX | Local engine | 12 deterministic WAV FX | Basic synthesized sounds, not AI sound generation |
| 13. Silence Remover | Local engine, optional auto-editor XML | New shorter MP4/WAV, detection JSON, or Premiere XML with optional tool | **Does not ripple-delete the active Premiere timeline** |
| 14. Podcast Tools | Local engine | Voice chain WAV | Preprocessed copy |
| 15. Audio Enhancement | Local engine | Four FFmpeg WAV processing profiles | Not Adobe Enhance Speech API |
| 16. Transitions | Local engine | 16 FFmpeg transitions between 2 videos | Video-only export; original audio omitted intentionally |
| 17. Easing Curves | Local engine | 6 easing CSV curves | Not Premiere native keyframes |
| 18. Speed Ramp | Local engine | 3-segment rendered MP4/WAV | Not Premiere native speed keyframes |
| 19. Motion Tracking | Optional OpenCV | ROI motion CSV | No timeline tracking/effects in Premiere |
| 20. Social Guides | Local engine | 5 overlay PNG templates | Import overlay manually |
| 21. Project Organizer | Local engine | Non-destructive folder copy plan, optional copies | Does not manipulate bins inside Premiere |

### Source projects investigated / integrated as external adapters

We did not download, vendor or copy code from these GitHub repositories into this ZIP; the environment could browse documentation but could not clone repositories. We reused their public API/command patterns and call optional installed programs as separate processes. Third-party licenses and model weights remain external.

* [AdobeDocs UXP Premiere Samples](https://github.com/AdobeDocs/uxp-premiere-pro-samples) — reference for official Premiere UXP host/project APIs (some individual source files have **Adobe proprietary terms**, so **none are copied**).
* [WyattBlue/auto-editor](https://github.com/WyattBlue/auto-editor) — **Unlicense**; optional Premiere XML export integration for silence editing.
* [SYSTRAN/faster-whisper](https://github.com/SYSTRAN/faster-whisper) — optional offline speech transcription. Whisper models download on first use and carry their own licenses.
* [danielgatis/rembg](https://github.com/danielgatis/rembg) — MIT program; individual model weights can have different commercial restrictions, so the UI adapter only enables selected common models.
* [yt-dlp/yt-dlp](https://github.com/yt-dlp/yt-dlp) — optional downloader; repository Unlicense; installed executables can carry combined third-party licenses.
* [opencv/opencv](https://github.com/opencv/opencv) — optional optical-flow/tracking input; Apache 2.0 in current releases.
* [rashedislamrion/Auto-cut-agent-for-premierpro-](https://github.com/rashedislamrion/Auto-cut-agent-for-premierpro-) — design research for UXP split and synchronisation; **not copied, not embedded, not claimed compatible**.
* [nicremo/open-silences](https://github.com/nicremo/open-silences) — MIT; workflow and rollback research; CEP/macOS, not embedded.

### Local system requirements

- Windows 10/11, Premiere Pro 2026, Adobe UXP Developer Tool (for a development plugin).
- Python 3.11+ with Pillow.
- FFmpeg and FFprobe installed and on PATH for media rendering.
- For optional features: `faster-whisper`, `rembg[cpu]`, `opencv-python`, `yt-dlp`, `auto-editor`.
- Initial model downloads require connectivity; they are not included.
- No forced paid API, login, telemetry or Adobe access token. Local Python bridge listens **only** on `127.0.0.1:8734`.

### How to run this engineering build (not a final user-installable plugin)

1. Unzip. On Windows, launch `START_OG_TOOLS_WINDOWS.bat` to create the Python venv and run the local engine. **FFmpeg must be installed separately if not already on PATH.**
2. In Premiere Pro 2026 enable **Settings → Plugins → Developer Mode**, restart Premiere.
3. In **UXP Developer Tool**, choose **Add Plugin** then select `plugin/manifest.json` and **Load**.
4. Open Premiere **Window → UXP Plugins → OG Tools**. The panel calls the localhost engine and can generate media.
5. Choose a source from Browse, run the transform, and optionally click **Import output to Premiere**. The import code uses Adobe `Project.importFiles()`, but has **not** been verified in Premiere here.
6. `OPTIONAL_AI_SETUP_WINDOWS.bat` installs optional packages when desired. These tools may be large.

You can run the media engine without Premiere:

```bash
python -m pip install -r requirements-core.txt
python -m engine.server
python -m engine.cli title-motion --text "مرحبا بالعالم" --motion slide-up --style editorial
python -m engine.cli sfx
python -m unittest discover -s tests -v
```

Outputs created with empty `--output` go to `~/Videos/OG Tools` for source-less features; source-aware output defaults next to the source with an `.og-...` suffix.

## Test evidence (2026-11-12)

- 25 Python unit/integration tests passed on the available Linux execution environment.
- Tests actually generated and probed MP4 cut output, speed ramps with audio, denoised WAV, transitions, Arabic/English ProRes 4444 alpha MOV, slideshow, drawing overlay, WAV SFX, SVG icons, social PNG, and a localhost HTTP job.
- `node --check plugin/main.js` and `json` manifest validation passed. A Chromium/Playwright live visual preview was attempted but blocked by sandbox browser policy, so it is NOT counted as passing.
- Headless browser and UXP panel UI were not validated; the localhost API was validated via HTTP requests.
- The `.github/workflows/test.yml` runs these tests on GitHub Actions Ubuntu and Windows after you upload the repository. **It has not run on GitHub**, and the environment here could not run Windows or Premiere Pro.
- No assertion of fully functioning Premiere timeline edits, Adobe import, or Windows installation can be made without an actual integration test.

## Important operational limits

- The engine never overwrites its source media. Timeline changes are *not* made directly; optional XML import creates a separate sequence when supported by auto-editor.
- Silence detection is level-based and can remove quiet syllables if tuned too aggressively. Review the rendered media before deleting any original.
- Transition MP4 is video-only; do not assume audio is preserved in that output.
- The optional background remover only handles photos. Object Mask controls are not available through this prototype.
- The path/3D text outputs approximate those effects visually, but are not native editable Premiere layers.
- Fast CLI tests do not prove Premiere plugin compatibility.

## GitHub roadmap

The included `.github/workflows/test.yml` can be activated by pushing this entire folder to a GitHub repository. That will validate Python/FFmpeg on Windows without touching the user's Premiere environment. For the next production milestone, add host-native testing on a licensed Premiere 2026 instance and a signed install package `.ccx`.

This project was authored as a private personal project. No VOLT source files, templates, paid assets or brand marks are embedded.

## v0.6 — Native editable keyframe animations (experimental Premiere integration)

The panel now includes **Native Keyframe Studio**: 24 original motion presets applied as *actual UXP ComponentParam keyframe actions* to a selected editable Graphic/MOGRT/clip in Premiere's sequence. Unlike the previous ProRes title renderer, this does not render or rasterize the selected title, and it does not modify its text content. The text remains editable **if it was editable before**.

Keyframed properties are dynamically discovered in the selected clip's component chain and can be manually mapped if auto-detection fails (e.g. localized labels). Supports Position, Scale, Opacity, Rotation. Cubic easing is sampled into 9/13/21 keyframes per property. The tool refuses to overwrite existing keyframes and refuses to apply partial presets with missing required properties.

Run mocked Adobe UXP transaction tests: `node --test tests/test_native_keyframes.js`.
These tests cannot establish Premiere runtime compatibility; no Premiere host was available for integration testing. Not yet production-certified. This project remains an engineering build.
