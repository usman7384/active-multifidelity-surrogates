# Explainer video and overview diagram

A [Remotion](https://www.remotion.dev) project that renders two things from the study's numbers:

- `Short`: the 34-second narrated cut for LinkedIn and the README (1920 x 1080, 30 fps), rendered to
  [`../explainer_short.mp4`](../explainer_short.mp4) and, at half size and 15 fps, [`../explainer_short.gif`](../explainer_short.gif).
- `Explainer`: the 100-second narrated version, rendered to [`../explainer.mp4`](../explainer.mp4).
- `Overview`: the one-page result diagram (1920 x 1540), rendered to [`../result_overview.png`](../result_overview.png).

Narration: `voiceover/lines.json` is the script; `voiceover/make_voiceover.py` synthesises it with
[Kokoro](https://github.com/hexgrad/kokoro) (open-weights, Apache-2.0, runs locally) into `public/vo/` and records
each clip's length in `voiceover/durations.json`, which sizes the scenes.

Every number shown is in `src/data.ts` with the result file it comes from. The toy curves in the "three ways"
scene (`src/curves.ts`) illustrate the mechanism; they are not data.

Design rules followed: Remotion's agent skills (`remotion-dev/skills`: frame-driven `interpolate`/`spring`,
no CSS transitions, safe areas, 84px+ headlines at 1080p) and the dataviz palette method (three categorical
colours validated for colour-vision deficiency, thin marks, direct labels, recessive axes).

```bash
npm i
npx remotion studio                                  # preview and scrub
python voiceover/make_voiceover.py                 # once, after editing lines.json (pip install kokoro soundfile)
npx remotion render Short ../explainer_short.mp4 --codec h264 --crf 18
npx remotion render Short ../explainer_short.gif --codec gif --scale 0.5 --every-nth-frame 2
npx remotion render Explainer ../explainer.mp4 --codec h264 --crf 18
npx remotion still Overview ../result_overview.png
```

On a machine without a Remotion-downloaded browser, add `--browser-executable` pointing at an installed Chrome.
