# Explainer video and overview diagram

A [Remotion](https://www.remotion.dev) project that renders two things from the study's numbers:

- `Explainer`: a 71-second animated explainer for a non-technical audience (1920 x 1080, 30 fps), rendered to
  [`../explainer.mp4`](../explainer.mp4).
- `Overview`: the one-page result diagram (1920 x 1300), rendered to [`../result_overview.png`](../result_overview.png).

Every number shown is in `src/data.ts` with the result file it comes from. The toy curves in the "three ways"
scene (`src/curves.ts`) illustrate the mechanism; they are not data.

Design rules followed: Remotion's agent skills (`remotion-dev/skills`: frame-driven `interpolate`/`spring`,
no CSS transitions, safe areas, 84px+ headlines at 1080p) and the dataviz palette method (three categorical
colours validated for colour-vision deficiency, thin marks, direct labels, recessive axes).

```bash
npm i
npx remotion studio                                  # preview and scrub
npx remotion render Explainer ../explainer.mp4 --codec h264 --crf 18
npx remotion still Overview ../result_overview.png
```

On a machine without a Remotion-downloaded browser, add `--browser-executable` pointing at an installed Chrome.
