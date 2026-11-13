# Third-party and upstream assessment

OG Tools does not bundle binaries, models, fonts, or code copied from third-party GitHub repositories. It invokes optional separately installed tools. Their licenses apply to the installed versions; consult their respective distributions before commercial use.

| Project | Reference | Use in OG Tools | License notes |
|---|---|---|---|
| Adobe Premiere UXP samples | https://github.com/AdobeDocs/uxp-premiere-pro-samples | API documentation and design patterns only | Adobe sample source may have proprietary license terms. No code copied. |
| FFmpeg | https://ffmpeg.org | External local executable | LGPL/GPL depending on build and linked libraries. Not redistributed. |
| Auto-Editor | https://github.com/WyattBlue/auto-editor | Optional Premiere XML process adapter | Upstream repo Unlicense; downstream binaries may differ. |
| faster-whisper | https://github.com/SYSTRAN/faster-whisper | Optional offline transcription import | Check project and model weight licenses. Not bundled. |
| rembg | https://github.com/danielgatis/rembg | Optional background matting import | MIT program; model licenses independent. |
| OpenCV | https://github.com/opencv/opencv | Optional local ROI tracking | Apache 2.0 in current versions. |
| yt-dlp | https://github.com/yt-dlp/yt-dlp | Optional authorized media downloads | Unlicense repository; distributed binaries may include copyleft components. |
| Auto Cut Agent | https://github.com/rashedislamrion/Auto-cut-agent-for-premierpro- | Engineering research | MIT, no code copied. |
| Open Silences | https://github.com/nicremo/open-silences | Engineering research | MIT, no code copied. |
| CapRocket | https://github.com/medhachim/CapRocket | Creative workflow research | License not assumed; no source copied. |

The OG Tools original code is personal-project source. Only use/download assets the user has rights to.

### v0.6 native keyframe module
`plugin/native/keyframes.js` is original code using the publicly documented Premiere UXP Action APIs. It is inspired by, but does not copy, Adobe's sample. Adobe APIs are used as references; the source code from Adobe sample is not redistributed.

Creator captions v0.7 design references only (no copied source): [nicolaigaina/ai-video-captions](https://github.com/nicolaigaina/ai-video-captions) (MIT) and [sebetancurch/auto-caption](https://github.com/sebetancurch/auto-caption) (MIT). Their libraries and design patterns were studied, not embedded.


## Creator text v0.9
The new 12 trend styles and 6 whole-clip keyframe curves are independently authored. No VOLT assets, template files, or code are embedded; public website previews are used only for studying feature categories.
