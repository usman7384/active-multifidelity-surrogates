import React from "react";
import { useCurrentFrame, useVideoConfig } from "remotion";
import { ease, enter } from "../anim";
import { CurvePanel, Headline, Kicker, Narration, Scene, Swatch } from "../components";
import { C, T } from "../theme";
import { clipFrames } from "../vo";

// Panel start frames follow the narration: each panel begins when its line does.
export const threeWaysStarts = (fps: number) => {
  const fine = 20;
  const cheap = fine + clipFrames("long_three_fine", fps, 195, 0.2);
  const mix = cheap + clipFrames("long_three_cheap", fps, 195, 0.2);
  return { fine, cheap, mix, end: mix + clipFrames("long_three_mix", fps, 230, 1.2) };
};

type V = "fine" | "cheap" | "mix";
const META: Record<V, { title: string; runs: string; color: string; verdict: string; why: string }> = {
  fine: {
    title: "Fine runs only",
    runs: "~110 runs",
    color: C.fine,
    verdict: "Accurate points, too few of them.",
    why: "Between the points the model guesses, and misses whole features.",
  },
  cheap: {
    title: "Cheap runs only",
    runs: "~1,700 runs",
    color: C.cheap,
    verdict: "Lots of points, all slightly off.",
    why: "The model learns the cheap answer precisely and becomes confidently wrong.",
  },
  mix: {
    title: "Mix of both",
    runs: "~1,160 cheap + 50 fine",
    color: C.mix,
    verdict: "Cheap runs draw the shape, fine runs fix the offset.",
    why: "A few accurate points teach the model how far off the cheap ones are.",
  },
};

const Panel: React.FC<{ v: V; from: number; x: number }> = ({ v, from, x }) => {
  const frame = useCurrentFrame();
  const m = META[v];
  const show = enter(frame, from);
  const progress = ease(frame, from + 20, 150);
  const verdict = enter(frame, from + 120);
  return (
    <div style={{ position: "absolute", left: x, top: 330, width: 540, ...show }}>
      <div style={{ fontSize: T.sub, fontWeight: 600, color: m.color, whiteSpace: "nowrap" }}>{m.title}</div>
      <div style={{ fontSize: T.tiny, color: C.muted, marginTop: 4 }}>{m.runs}</div>
      <div style={{ marginTop: 16, background: "#fff", borderRadius: 18, padding: 10, boxShadow: `0 1px 0 ${C.border}, 0 10px 30px rgba(11,11,11,0.05)` }}>
        <CurvePanel variant={v} width={520} height={270} progress={progress} />
      </div>
      <div style={{ marginTop: 22, ...verdict }}>
        <div style={{ fontSize: T.body, fontWeight: 600, lineHeight: 1.25 }}>{m.verdict}</div>
        <div style={{ fontSize: T.small, color: C.ink2, marginTop: 10, lineHeight: 1.35 }}>{m.why}</div>
      </div>
    </div>
  );
};

// Scene 4: the three strategies on a toy one-dimensional picture, built up one after another.
export const ThreeWays: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const starts = threeWaysStarts(fps);
  return (
    <Scene>
      <Narration k="long_three_fine" from={starts.fine} />
      <Narration k="long_three_cheap" from={starts.cheap} />
      <Narration k="long_three_mix" from={starts.mix} />
      <Kicker from={0}>Three ways to spend the hour</Kicker>
      <Headline from={6} size={76}>What the model learns from each kind of data</Headline>
      <Panel v="fine" from={starts.fine} x={120} />
      <Panel v="cheap" from={starts.cheap} x={120 + 590} />
      <Panel v="mix" from={starts.mix} x={120 + 1180} />
      <div style={{ position: "absolute", left: 120, bottom: 100, display: "flex", gap: 40, ...enter(frame, starts.fine + 110) }}>
        <div style={{ display: "flex", alignItems: "center", gap: 12, fontSize: T.small, color: C.ink2 }}>
          <svg width={36} height={6}><line x1={0} x2={36} y1={3} y2={3} stroke={C.truth} strokeWidth={2} strokeDasharray="6 6" /></svg>
          true answer
        </div>
        <div style={{ display: "flex", alignItems: "center", gap: 12, fontSize: T.small, color: C.ink2 }}>
          <div style={{ width: 36, height: 14, background: C.mixSoft, borderRadius: 3 }} />
          how unsure the model is
        </div>
        <Swatch color={C.fine} label="fine run" />
        <Swatch color={C.cheap} label="cheap run" />
      </div>
    </Scene>
  );
};
