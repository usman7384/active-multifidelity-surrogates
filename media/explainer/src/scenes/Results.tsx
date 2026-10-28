import React from "react";
import { useCurrentFrame } from "remotion";
import { enter } from "../anim";
import { FINAL } from "../data";
import { Bar, Headline, Kicker, Narration, Scene, Sub } from "../components";
import { C, T } from "../theme";

// Scene 5: the measured result on the real solver, eight trials each, one CPU hour.
export const Results: React.FC = () => {
  const frame = useCurrentFrame();
  const W = 1680;
  const pct = (v: number) => `${Math.round(v * 100)}%`;
  const err = (v: number) => v.toFixed(2);
  return (
    <Scene>
      <Narration k="long_results" />
      <Kicker from={0}>Measured on the real simulator · 8 trials each · 1 CPU hour</Kicker>
      <Headline from={6} size={76}>Prediction error on 100 unseen fine-mesh tests</Headline>
      <Sub from={14} size={T.small} color={C.muted} style={{ marginTop: 10 }}>
        lower is better · root-mean-square error in points of inner-diameter change
      </Sub>
      <div style={{ marginTop: 22 }}>
        <Bar label={FINAL.fine.label} note={FINAL.fine.runs} value={FINAL.fine.rmse} max={0.56} color={C.fine} from={30} format={err} width={W} />
        <Bar label={FINAL.cheap.label} note={FINAL.cheap.runs} value={FINAL.cheap.rmse} max={0.56} color={C.cheap} from={44} format={err} width={W} />
        <Bar label={FINAL.mix.label} note={FINAL.mix.runs} value={FINAL.mix.rmse} max={0.56} color={C.mix} from={58} format={err} width={W} emphasis />
      </div>

      <div style={{ marginTop: 24, ...enter(frame, 150) }}>
        <div style={{ fontSize: T.sub, fontWeight: 600 }}>When the model says "95% sure", how often is it right?</div>
        <div style={{ fontSize: T.small, color: C.muted, marginTop: 6 }}>target: 95% · the line</div>
      </div>
      <div style={{ marginTop: 14 }}>
        <Bar label={FINAL.fine.label} value={FINAL.fine.coverage} max={1} color={C.fine} from={170} format={pct} width={W} target={0.95} />
        <Bar label={FINAL.cheap.label} value={FINAL.cheap.coverage} max={1} color={C.cheap} from={184} format={pct} width={W} target={0.95} />
        <Bar label={FINAL.mix.label} value={FINAL.mix.coverage} max={1} color={C.mix} from={198} format={pct} width={W} target={0.95} emphasis />
      </div>
      <div style={{ position: "absolute", left: 120, bottom: 76, fontSize: T.body, color: C.ink2, ...enter(frame, 290) }}>
        Cheap runs alone are wrong <span style={{ color: C.cheap, fontWeight: 600 }}>a third of the time</span> when they claim to be sure.
        The mix is <span style={{ color: C.mix, fontWeight: 600 }}>both more accurate and more honest</span>.
      </div>
    </Scene>
  );
};
