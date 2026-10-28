// Narration clips (public/vo/*.wav, made by voiceover/make_voiceover.py) and their lengths, used to size scenes.
import durations from "../voiceover/durations.json";

const D = durations as Record<string, number>;

export const hasClip = (key: string) => key in D;

// Frames a scene needs to fit its narration plus a breath, never less than `minFrames`.
export const clipFrames = (key: string, fps: number, minFrames: number, tailSeconds = 0.6) =>
  Math.max(minFrames, Math.ceil(((D[key] ?? 0) + tailSeconds) * fps));
