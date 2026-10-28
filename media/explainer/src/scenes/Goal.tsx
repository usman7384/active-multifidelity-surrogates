import React from "react";
import { useCurrentFrame, useVideoConfig } from "remotion";
import { ease, enter, pop } from "../anim";
import { Headline, Kicker, Narration, Scene, Sub } from "../components";
import { C, T } from "../theme";

const Chip: React.FC<{ from: number; children: React.ReactNode }> = ({ from, children }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const p = pop(frame, fps, from);
  return (
    <div
      style={{
        padding: "16px 28px",
        borderRadius: 999,
        border: `2px solid ${C.grid}`,
        background: "#fff",
        fontSize: T.body,
        color: C.ink2,
        opacity: p,
        translate: `${(1 - p) * -30}px 0px`,
      }}
    >
      {children}
    </div>
  );
};

// Scene 2: what the model is for.
export const Goal: React.FC = () => {
  const frame = useCurrentFrame();
  const arrow = ease(frame, 70, 30);
  const box = pop(frame, 30, 85);
  const out = enter(frame, 110);
  return (
    <Scene>
      <Narration k="long_goal" />
      <Kicker from={0}>The goal</Kicker>
      <Headline from={6}>A model that predicts the test for any setting.</Headline>
      <Sub from={22} style={{ marginTop: 18 }}>
        Each simulation is one data point. The model fills in everything between them, and says how sure it is.
      </Sub>
      <div style={{ display: "flex", alignItems: "center", gap: 36, marginTop: 90 }}>
        <div style={{ display: "flex", flexDirection: "column", gap: 18 }}>
          <Chip from={40}>ring size</Chip>
          <Chip from={48}>wall thickness</Chip>
          <Chip from={56}>friction</Chip>
          <Chip from={64}>material</Chip>
        </div>
        <svg width={140} height={40} style={{ opacity: arrow }}>
          <line x1={0} y1={20} x2={120 * arrow} y2={20} stroke={C.ink2} strokeWidth={3} />
          <polygon points="120,10 140,20 120,30" fill={C.ink2} opacity={arrow} />
        </svg>
        <div
          style={{
            padding: "40px 48px",
            borderRadius: 24,
            background: C.mix,
            color: "#fff",
            fontSize: T.sub,
            fontWeight: 600,
            opacity: box,
            scale: String(0.9 + 0.1 * box),
          }}
        >
          surrogate model
        </div>
        <svg width={140} height={40} style={{ opacity: out.opacity }}>
          <line x1={0} y1={20} x2={120} y2={20} stroke={C.ink2} strokeWidth={3} />
          <polygon points="120,10 140,20 120,30" fill={C.ink2} />
        </svg>
        <div style={{ ...out }}>
          <div style={{ fontSize: T.sub, fontWeight: 600 }}>how much the ring widens</div>
          <div style={{ fontSize: T.body, color: C.ink2, marginTop: 10 }}>
            plus an honest <span style={{ color: C.mix, fontWeight: 600 }}>± how sure</span>
          </div>
        </div>
      </div>
    </Scene>
  );
};
