import React from "react";
import { useCurrentFrame } from "remotion";
import { enter } from "../anim";
import { Kicker, Narration, Scene } from "../components";
import { C, T } from "../theme";

const Line: React.FC<{ from: number; children: React.ReactNode }> = ({ from, children }) => {
  const frame = useCurrentFrame();
  return (
    <div style={{ fontSize: 84, fontWeight: 600, letterSpacing: -2, lineHeight: 1.15, ...enter(frame, from, 26) }}>{children}</div>
  );
};

// Scene 7: the takeaway for someone who has to decide.
export const Takeaway: React.FC = () => {
  const frame = useCurrentFrame();
  return (
    <Scene>
      <Narration k="long_takeaway" />
      <Kicker from={0}>What it means</Kicker>
      <div style={{ display: "flex", flexDirection: "column", gap: 26, marginTop: 20 }}>
        <Line from={8}>Same hour of compute.</Line>
        <Line from={30}>
          About <span style={{ color: C.mix }}>30% less error</span>.
        </Line>
        <Line from={52}>Honest about what it doesn't know.</Line>
      </div>
      <div style={{ marginTop: "auto", display: "flex", justifyContent: "space-between", alignItems: "flex-end", ...enter(frame, 95) }}>
        <div style={{ fontSize: T.body, color: C.ink2, lineHeight: 1.4, maxWidth: 1100 }}>
          The recipe: many cheap simulations for the shape, a few expensive ones to correct them, and a model that
          combines the two. Next: letting the model pick its own runs (promising, not yet consistent).
        </div>
        <div style={{ fontSize: T.small, color: C.muted, textAlign: "right" }}>
          active-multifidelity-surrogates
          <br />
          ring compression test · 20 trials
        </div>
      </div>
    </Scene>
  );
};
