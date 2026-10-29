"""Synthesise the narration and record each clip's length.

    python voiceover/make_voiceover.py            # all lines in lines.json
    python voiceover/make_voiceover.py long hook  # one line

Two free backends, chosen by the "voice" field in lines.json:
  - a Kokoro voice such as "am_michael" (open weights, Apache-2.0, runs locally; pip install kokoro soundfile)
  - a Microsoft neural voice such as "en-US-AndrewMultilingualNeural" (edge-tts; the text is synthesised on
    Microsoft's servers; pip install edge-tts soundfile)
"rate" slows or speeds the reading (1.0 = normal).

Writes public/vo/<set>_<key>.wav (24 kHz mono) and voiceover/durations.json ({"<set>_<key>": seconds}), which the
compositions read to size their scenes.
"""
from __future__ import annotations

import asyncio
import io
import json
import sys
from pathlib import Path

import numpy as np
import soundfile as sf

HERE = Path(__file__).resolve().parent
OUT = HERE.parent / "public" / "vo"
LINES = json.loads((HERE / "lines.json").read_text(encoding="utf-8"))
DUR_FILE = HERE / "durations.json"
SR = 24000


def _kokoro(voice: str, rate: float):
    from kokoro import KPipeline

    pipe = KPipeline(lang_code="b" if voice.startswith("b") else "a", repo_id="hexgrad/Kokoro-82M")
    return lambda text: np.concatenate([a for _, _, a in pipe(text, voice=voice, speed=rate)])


def _edge(voice: str, rate: float):
    import edge_tts
    import av  # bundled with kokoro's dependencies; decodes the mp3 that edge-tts returns

    async def speak(text: str) -> bytes:
        buf = b""
        async for chunk in edge_tts.Communicate(text, voice, rate=f"{round((rate - 1) * 100):+d}%").stream():
            if chunk["type"] == "audio":
                buf += chunk["data"]
        return buf

    def synth(text: str):
        for attempt in range(4):                       # the service occasionally returns no audio; retry
            try:
                data = asyncio.run(speak(text))
                break
            except edge_tts.exceptions.NoAudioReceived:
                if attempt == 3:
                    raise
        with av.open(io.BytesIO(data)) as c:
            res = av.AudioResampler(format="flt", layout="mono", rate=SR)
            frames = [f.to_ndarray()[0] for fr in c.decode(audio=0) for f in res.resample(fr)]
        return np.concatenate(frames)

    return synth


def main(only_set: str | None = None, only_key: str | None = None) -> None:
    voice, rate = LINES["voice"], float(LINES.get("rate", 1.0))
    synth = (_edge if voice.startswith("en-") else _kokoro)(voice, rate)
    OUT.mkdir(parents=True, exist_ok=True)
    durations = json.loads(DUR_FILE.read_text()) if DUR_FILE.exists() else {}
    for set_name, lines in LINES.items():
        if not isinstance(lines, dict) or (only_set and set_name != only_set):
            continue
        for key, text in lines.items():
            if only_key and key != only_key:
                continue
            audio = synth(text).astype(np.float32)
            audio = np.concatenate([np.zeros(int(0.15 * SR), np.float32), audio, np.zeros(int(0.3 * SR), np.float32)])
            name = f"{set_name}_{key}"
            sf.write(OUT / f"{name}.wav", audio, SR)
            durations[name] = round(len(audio) / SR, 3)
            print(f"{name}: {durations[name]} s")
    DUR_FILE.write_text(json.dumps(durations, indent=1), encoding="utf-8")


if __name__ == "__main__":
    main(*(sys.argv[1:3] or [None, None]))
