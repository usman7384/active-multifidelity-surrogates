import React from "react";
import { Composition, Still } from "remotion";
import { Explainer, FPS, totalFrames } from "./Explainer";
import { Overview } from "./Overview";
import { Short, SHORT_FPS, shortTotal } from "./Short";

export const RemotionRoot: React.FC = () => {
  return (
    <>
      <Composition id="Explainer" component={Explainer} durationInFrames={totalFrames(FPS)} fps={FPS} width={1920} height={1080} />
      <Composition id="Short" component={Short} durationInFrames={shortTotal(SHORT_FPS)} fps={SHORT_FPS} width={1920} height={1080} />
      <Still id="Overview" component={Overview} width={1920} height={1540} />
    </>
  );
};
