import React from "react";
import { useCurrentFrame } from "remotion";
import { ease, enter } from "../anim";
import { COST } from "../data";
import { Headline, Kicker, Scene, Sub } from "../components";
import { C, T } from "../theme";

// A one-hour bar filled with runs of one kind.
const Fill: React.FC<{ kind: "fine" | "cheap"; from: number; width: number }> = ({ kind, from, width }) => {
  const frame = useCurrentFrame();
  const p = ease(frame, from, 70);
  const cost = kind === "fine" ? COST.fine : COST.cheap;
  const n = Math.floor(COST.budget / cost);
  const shown = Math.floor(n * p);
  const color = kind === "fine" ? C.fine : C.cheap;
  const H = 64;
  const cell = (width / n);
  return (
    <div style={{ opacity: ease(frame, from - 10, 16) }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "baseline", marginBottom: 14 }}>
        <div style={{ fontSize: T.sub, fontWeight: 600 }}>{kind === "fine" ? "Fine runs only" : "Cheap runs only"}</div>
        <div style={{ fontSize: T.sub, fontWeight: 600, color }}>
          {shown.toLocaleString("en-US")} runs
        </div>
      </div>
      <div style={{ position: "relative", width, height: H, background: C.plane, borderRadius: 10, overflow: "hidden", border: `1px solid ${C.grid}` }}>
        {kind === "fine"
          ? Array.from({ length: shown }, (_, i) => (
              <div key={i} style={{ position: "absolute", left: i * cell + 1, top: 6, width: cell - 2, height: H - 12, background: color, borderRadius: 3 }} />
            ))
          : <div style={{ position: "absolute", left: 0, top: 0, width: width * p, height: H, background: `repeating-linear-gradient(90deg, ${color} 0 1.4px, transparent 1.4px 2px)` }} />}
      </div>
    </div>
  );
};

// Scene 3: the budget.
export const Budget: React.FC = () => {
  const frame = useCurrentFrame();
  return (
    <Scene>
      <Kicker from={0}>The constraint</Kicker>
      <Headline from={6}>One hour of computer time buys very different amounts of data.</Headline>
      <div style={{ display: "flex", flexDirection: "column", gap: 54, marginTop: 80 }}>
        <Fill kind="fine" from={40} width={1680} />
        <Fill kind="cheap" from={95} width={1680} />
      </div>
      <div style={{ marginTop: 22, fontSize: T.tiny, color: C.muted, ...enter(frame, 150) }}>
        one block = one run · each bar is 3,600 CPU seconds
      </div>
      <Sub from={165} style={{ marginTop: "auto", fontSize: T.body }}>
        <span style={{ color: C.fine, fontWeight: 600 }}>~100 accurate points</span>
        <span style={{ color: C.muted }}> &nbsp;or&nbsp; </span>
        <span style={{ color: C.cheap, fontWeight: 600 }}>~1,800 slightly-off points</span>. Neither is what you want.
      </Sub>
    </Scene>
  );
};
