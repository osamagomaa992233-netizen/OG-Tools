# OG Tools v0.7 — Creator Editing Workflows (Engineering Release)

**Build date:** 2026-11-13. **Target:** Windows + Premiere Pro 2026 UXP. This is a source engineering build, NOT a verified one-click Premiere installer and NOT a complete replacement for VOLT.

## New in this build

### 1. Creator Captions — Arabic and English

- Reads audio from a selected trimmed source clip through Premiere's documented UXP selection / source-file APIs, if Premiere supplies those objects as expected.
- The optional locally installed `faster-whisper` produces speech-to-text **word timestamps**. Requires an initial model download; **actual model inference was not tested in this build environment**.
- Original ASS styles: `kinetic-pop`, `clean-focus`, `editorial-accent`, `word-flash`, `micro-bounce`, `mono-underline`, `hook-punch`, `quiet-lower`.
- Four color palettes, customizable installed font family, up to five words per phrase, Arabic/English script selection.
- Exports `.srt` (sequence-aligned when selected via panel), `.ass` (timed styling), `.words.json` (word-by-word data), and optional burned-in preview `.mp4`.
- **Native caption limitations:** SRT can be imported into Premiere as captions by the editor, but the ASS motion effects do **not** become native editable Premiere text keyframes. Clip selection is one source clip, not an entire mixed/assembled track.

### 2. Creator Zoom — direct UXP keyframe presets and offline video alternatives

- Eight **new** native motion presets: `creator-punch-in`, `creator-punch-out`, `creator-snap-zoom`, `creator-reaction`, `creator-jumpcut`, `creator-slow-push`, `creator-breathe`, `creator-focus-pull`.
- Uses the same UXP keyframing transaction engine as v0.6; sets editable Scale (and optionally Position) keyframes of one selected clip. Refuses to overwrite any existing keyframes. **Mock Premiere API tested, real Premiere not available.**
- Four quick-action buttons in panel; additionally, six FFmpeg video-output creator zoom variants, retaining audio.

### 3. Creator Speed Ramp — local media output

- Five original speed curves: `whip`, `impact`, `smooth`, `hyper`, `reverse-feel`.
- Samples eased speed curves over 3–48 segments (9 default), preserves audio tempo as well as the existing FFmpeg pipeline supports; writes MP4 and JSON speed profile.
- Not native Premiere Time Remapping keyframes. Small seams may occur between independently encoded segments; test with actual footage prior to delivery.

### 4. Silence Cut — selected clip safety

- Uses selected clip's source in/out and timeline offset so source media outside the trim is **not** analyzed for the selected-clip workflow.
- Outputs a shortened media copy or a non-destructive JSON keep/cut plan and original/sequence time ranges.
- No automatic ripple delete of other linked timeline elements. Optional `auto-editor` XML path is available only for the source-wide flow.

## Engineering verification

- **33 Python unit/integration tests passed** on Linux (actual FFmpeg media exports, Arabic ASS subtitles and captioned-video preview, zoom, sampled speed ramp and audio, silence segment render, localhost engine).
- **17 JavaScript Node tests passed** (mock Premiere API selection/keyframes and safety rejection cases).
- `plugin/main.js`, `plugin/native/keyframes.js`, `plugin/native/selection.js`, and `plugin/native/ui.js` pass JavaScript syntax checks. `plugin/manifest.json` parses.
- **Not tested:** actual Arabic recording Whisper inference (optional package/model absent), Windows install, UXP panel running under Premiere, native keyframe application inside real Premiere, GitHub Actions execution, `.ccx` Adobe-signed packaging.

## Install/developer usage

1. Install Python 3.11+ and FFmpeg (add to PATH).
2. Run `START_OG_TOOLS_WINDOWS.bat`; for voice captions run `OPTIONAL_AI_SETUP_WINDOWS.bat` once. First run downloads a model when used.
3. In Premiere Pro 2026, enable developer mode; load `plugin/manifest.json` via Adobe UXP Developer Tool.
4. Select one clip and press `Use selected Premiere audio/video clip as source`, then choose `Creator Captions`, `Silence Remover`, `Creator Zoom Render`, or `Creator Velocity Ramp`.
5. For actual **editable Zoom keyframes**, instead select one video or graphic clip and use `Creator Zoom — Quick Actions` or `Native Keyframe Studio`.
6. Import generated files into the Project bin with the panel's `Import output` button. Verify timing and safety before working on production sequences.

No original media is intentionally overwritten by default outputs; a manually supplied output destination may replace an existing generated asset. Back up your Premiere projects before editing.

## Upstream inspiration and dependencies

- Adobe Premiere UXP examples: https://github.com/AdobeDocs/uxp-premiere-pro-samples
- faster-whisper (MIT): https://github.com/SYSTRAN/faster-whisper
- Local animated caption examples (MIT, design reference only; no upstream source copied): https://github.com/nicolaigaina/ai-video-captions and https://github.com/sebetancurch/auto-caption
- auto-editor (Unlicense): https://github.com/WyattBlue/auto-editor
- FFmpeg: https://ffmpeg.org/legal.html (build-dependent LGPL/GPL licensing).

All additions to OG Tools in this build were authored here; no proprietary VOLT templates or binaries were used.
