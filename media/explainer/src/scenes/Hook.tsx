import React from "react";
import { useCurrentFrame } from "remotion";
import { enter } from "../anim";
import { Headline, MeshCard, Scene, Sub } from "../components";
import { C, T } from "../theme";

// Scene 1: the choice. Two simulators of the same ring test, one hour of computer time.
export const Hook: React.FC = () => {
  const frame = useCurrentFrame();
  return (
    <Scene>
      <Headline from={0}>Two ways to simulate the same test.</Headline>
      <Sub from={14} style={{ marginTop: 18 }}>
        One is accurate but slow. One is fast but slightly off. You have one hour of computer time.
      </Sub>
      <div style={{ display: "flex", gap: 60, marginTop: 70 }}>
        <MeshCard kind="fine" from={40} />
        <MeshCard kind="cheap" from={58} />
      </div>
      <div style={{ marginTop: "auto", fontSize: T.sub, fontWeight: 600, color: C.ink, ...enter(frame, 105) }}>
        Which runs should you buy?
      </div>
    </Scene>
  );
};
