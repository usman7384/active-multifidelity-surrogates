import React from "react";
import { linearTiming, TransitionSeries } from "@remotion/transitions";
import { fade } from "@remotion/transitions/fade";
import { useCurrentFrame, useVideoConfig } from "remotion";
import { ease, enter } from "./anim";
import { Bar, CurvePanel, Headline, Kicker, MeshCard, Narration, Scene, Stat, Sub } from "./components";
import { CONFIRM, FINAL, IVR_FLOOR } from "./data";
import { PickCard } from "./scenes/Picking";
import { C, T } from "./theme";
import { clipFrames } from "./vo";

// The 30-second cut for LinkedIn and the README: the choice, the three ways, the result, how runs were chosen.

const FPS = 30;
const FADE = 10;
export const shortScenes = (fps: number) => ({
  s1: clipFrames("short_s1", fps, 200),
  s2: clipFrames("short_s2", fps, 300),
  s3: clipFrames("short_s3", fps, 260),
  s4: clipFrames("short_s4", fps, 170),
});
export const shortTotal = (fps: number) => Object.values(shortScenes(fps)).reduce((a, b) => a + b, 0) - 3 * FADE;

const S1: React.FC = () => {
  const frame = useCurrentFrame();
  return (
    <Scene>
      <Narration k="short_s1" />
      <Headline from={0} size={84}>Accurate simulations are slow. Cheap ones are slightly off.</Headline>
      <Sub from={14} style={{ marginTop: 16 }}>You have one hour of computer time. Which runs do you buy?</Sub>
      <div style={{ display: "flex", gap: 60, marginTop: 56 }}>
        <MeshCard kind="fine" from={40} />
        <MeshCard kind="cheap" from={56} />
      </div>
      <div style={{ position: "absolute", right: 120, bottom: 100, fontSize: T.small, color: C.muted, ...enter(frame, 90) }}>
        ring compression test · forming simulation
      </div>
    </Scene>
  );
};

const META = {
  fine: { title: "Accurate only", verdict: "Too few points. Misses features.", color: C.fine },
  cheap: { title: "Cheap only", verdict: "Precisely wrong, and sure of it.", color: C.cheap },
  mix: { title: "Mixed", verdict: "Cheap draws the shape, accurate fixes the offset.", color: C.mix },
} as const;

const S2: React.FC = () => {
  const frame = useCurrentFrame();
  const starts = { fine: 10, cheap: 95, mix: 180 } as const;
  return (
    <Scene>
      <Narration k="short_s2" />
      <Kicker from={0}>Three ways to spend the hour</Kicker>
      <Headline from={4} size={70}>What the model learns from each</Headline>
      {(["fine", "cheap", "mix"] as const).map((v, i) => {
        const from = starts[v];
        const m = META[v];
        return (
          <div key={v} style={{ position: "absolute", left: 120 + i * 590, top: 300, width: 540, ...enter(frame, from) }}>
            <div style={{ fontSize: T.sub, fontWeight: 600, color: m.color }}>{m.title}</div>
            <div style={{ marginTop: 16, background: "#fff", borderRadius: 18, padding: 10, boxShadow: `0 1px 0 ${C.border}, 0 10px 30px rgba(11,11,11,0.05)` }}>
              <CurvePanel variant={v} width={520} height={290} progress={ease(frame, from + 10, 110)} />
            </div>
            <div style={{ fontSize: T.body, fontWeight: 600, marginTop: 22, lineHeight: 1.3, ...enter(frame, from + 70) }}>{m.verdict}</div>
          </div>
        );
      })}
      <div style={{ position: "absolute", left: 120, bottom: 100, fontSize: T.small, color: C.muted, ...enter(frame, 40) }}>
        dashed: true answer · band: how unsure the model is
      </div>
    </Scene>
  );
};

const S3: React.FC = () => {
  const frame = useCurrentFrame();
  return (
    <Scene>
      <Narration k="short_s3" />
      <Kicker from={0}>Measured on 100 unseen tests · 20 random trials</Kicker>
      <Headline from={4} size={76}>The mix, for the same hour of compute:</Headline>
      <div style={{ display: "flex", gap: 30, marginTop: 56 }}>
        <Stat from={30} value={`${Math.round(CONFIRM.relGain * 100)}% less`} label="prediction error than cheap runs alone" color={C.mix} width={540} />
        <Stat from={48} value={`${Math.round(FINAL.mix.coverage * 100)}% vs ${Math.round(FINAL.cheap.coverage * 100)}%`} label={`right when it says "95% sure" (mix vs cheap only)`} color={C.mix} width={540} />
        <Stat from={66} value={`${CONFIRM.wins} of 12`} label="pre-registered trials won: test written down before running" width={540} />
      </div>
      <div style={{ marginTop: 44, fontSize: T.small, color: C.muted, ...enter(frame, 90) }}>
        prediction error on 100 unseen tests after 1 CPU hour · lower is better · 8 trials
      </div>
      <div style={{ marginTop: 6 }}>
        <Bar label="Accurate only" value={FINAL.fine.rmse} max={0.56} color={C.fine} from={100} format={(v) => v.toFixed(2)} width={1680} />
        <Bar label="Cheap only" value={FINAL.cheap.rmse} max={0.56} color={C.cheap} from={112} format={(v) => v.toFixed(2)} width={1680} />
        <Bar label="Mixed" value={FINAL.mix.rmse} max={0.56} color={C.mix} from={124} format={(v) => v.toFixed(2)} width={1680} emphasis />
      </div>
      <div style={{ marginTop: "auto", fontSize: T.sub, color: C.ink2, ...enter(frame, 170) }}>
        Same compute. <span style={{ color: C.mix, fontWeight: 600 }}>Less error.</span> Honest about its uncertainty.
      </div>
    </Scene>
  );
};

const S4: React.FC = () => {
  const frame = useCurrentFrame();
  const pending = IVR_FLOOR.verdict === null;
  return (
    <Scene>
      <Narration k="short_s4" />
      <Kicker from={0}>And how were the runs chosen?</Kicker>
      <div style={{ display: "flex", gap: 40, marginTop: 30 }}>
        <PickCard kind="lhs" from={10} width={820} />
        <PickCard kind="ivr" from={40} width={820} />
      </div>
      <div style={{ marginTop: "auto", ...enter(frame, 90) }}>
        <div style={{ fontSize: T.sub, fontWeight: 600, color: pending ? C.muted : C.ink }}>
          {pending ? "IVR result: pending the pre-registered run" : IVR_FLOOR.verdict}
        </div>
        <div style={{ fontSize: T.small, color: C.muted, marginTop: 14 }}>github.com/usman7384/active-multifidelity-surrogates</div>
      </div>
    </Scene>
  );
};

export const Short: React.FC = () => {
  const { fps } = useVideoConfig();
  const s = shortScenes(fps);
  return (
    <TransitionSeries>
      <TransitionSeries.Sequence durationInFrames={s.s1}><S1 /></TransitionSeries.Sequence>
      <TransitionSeries.Transition presentation={fade()} timing={linearTiming({ durationInFrames: FADE })} />
      <TransitionSeries.Sequence durationInFrames={s.s2}><S2 /></TransitionSeries.Sequence>
      <TransitionSeries.Transition presentation={fade()} timing={linearTiming({ durationInFrames: FADE })} />
      <TransitionSeries.Sequence durationInFrames={s.s3}><S3 /></TransitionSeries.Sequence>
      <TransitionSeries.Transition presentation={fade()} timing={linearTiming({ durationInFrames: FADE })} />
      <TransitionSeries.Sequence durationInFrames={s.s4}><S4 /></TransitionSeries.Sequence>
    </TransitionSeries>
  );
};

export const SHORT_FPS = FPS;
