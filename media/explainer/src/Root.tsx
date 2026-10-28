import React from "react";
import { Composition, Still } from "remotion";
import { Explainer, TOTAL } from "./Explainer";
import { Overview } from "./Overview";

export const RemotionRoot: React.FC = () => {
  return (
    <>
      <Composition id="Explainer" component={Explainer} durationInFrames={TOTAL} fps={30} width={1920} height={1080} />
      <Still id="Overview" component={Overview} width={1920} height={1300} />
    </>
  );
};
