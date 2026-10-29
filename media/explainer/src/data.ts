// Every number shown in the video, with where it comes from in the repository.

// README main table: results/final/summary.md, seeds 1-8, final scores at about 1.05-1.10 CPU hours.
export const FINAL = {
  fine: { label: "Fine runs only", runs: "~125 fine runs", rmse: 0.484, coverage: 0.9 },
  cheap: { label: "Cheap runs only", runs: "~1,700 cheap runs", rmse: 0.257, coverage: 0.68 },
  mix: { label: "Mix of both", runs: "~1,160 cheap + 50 fine", rmse: 0.205, coverage: 0.91 },
};

// Pre-registered confirmation: results/confirm/confirm.md, seeds 9-20, scores at 1.0 CPU hour.
export const CONFIRM = {
  seeds: [9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20],
  cheap: [0.212, 0.216, 0.254, 0.27, 0.261, 0.255, 0.252, 0.224, 0.237, 0.295, 0.234, 0.301],
  mix: [0.172, 0.126, 0.112, 0.162, 0.11, 0.29, 0.161, 0.149, 0.195, 0.25, 0.147, 0.26],
  meanCheap: 0.251,
  meanMix: 0.178,
  coverageCheap: 0.67,
  coverageMix: 0.94,
  wins: 11,
  relGain: 0.295,
  p: 0.0005,
};

// Solver cost per run, CPU seconds (README, "The fidelity pair").
export const COST = { fine: 34, cheap: 2, budget: 3600 };

// Pre-registration part 2: mf_ivr with a 40% fine-run floor against mf_lhs, seeds 9-20 (results/confirm_ivr).
// `verdict` stays null until that run has finished; the scenes then show "result pending".
export const IVR_FLOOR: { verdict: string | null; detail: string | null } = {
  verdict: "Letting the model choose did not help: IVR lost to the even spread in 10 of 12 pre-registered trials.",
  detail: "Mean error 0.23 against 0.18 for the same hour (Wilcoxon p = 0.99). It still beat cheap runs alone on calibration in 12 of 12. The simple design stays the default.",
};
