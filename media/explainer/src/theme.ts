// Visual system for the explainer and the overview still. Light surface, one UI sans, three series colours.
// The three categorical colours were validated with the dataviz palette checker (CVD dE 9.2, normal dE 27.6);
// aqua sits below 3:1 on the surface, so every aqua mark carries a direct label.
import { loadFont } from "@remotion/google-fonts/Inter";

export const { fontFamily } = loadFont("normal", {
  weights: ["400", "500", "600", "700"],
  subsets: ["latin"],
});

export const C = {
  surface: "#fcfcfb",
  plane: "#f9f9f7",
  ink: "#0b0b0b",
  ink2: "#52514e",
  muted: "#898781",
  grid: "#e1e0d9",
  axis: "#c3c2b7",
  border: "rgba(11,11,11,0.10)",
  // series: the three ways of spending the budget
  mix: "#2a78d6",
  cheap: "#eb6834",
  fine: "#1baf7a",
  mixSoft: "#cde2fb",
  cheapSoft: "#fbdccf",
  fineSoft: "#c9efe0",
  truth: "#52514e",
  good: "#006300",
};

export const FONT = `${fontFamily}, "Segoe UI", system-ui, sans-serif`;

// 1920 x 1080 canvas: the safe area and the type scale (video-layout rules, scaled from 1080 wide).
export const SAFE_X = 120;
export const SAFE_Y = 110;
export const T = {
  headline: 92,
  sub: 46,
  body: 34,
  small: 28,
  tiny: 24,
};
