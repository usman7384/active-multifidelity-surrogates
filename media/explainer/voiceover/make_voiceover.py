"""Synthesise the narration with Kokoro (open-weights TTS, Apache-2.0) and record each clip's length.

    python voiceover/make_voiceover.py            # all lines in lines.json
    python voiceover/make_voiceover.py long hook  # one line

Writes public/vo/<set>_<key>.wav (24 kHz mono) and voiceover/durations.json ({"<set>_<key>": seconds}), which the
compositions read to size their scenes. Needs: pip install kokoro soundfile (a one-off model download of ~330 MB).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import soundfile as sf

HERE = Path(__file__).resolve().parent
OUT = HERE.parent / "public" / "vo"
LINES = json.loads((HERE / "lines.json").read_text(encoding="utf-8"))
DUR_FILE = HERE / "durations.json"


def main(only_set: str | None = None, only_key: str | None = None) -> None:
    from kokoro import KPipeline

    pipe = KPipeline(lang_code="a", repo_id="hexgrad/Kokoro-82M")
    OUT.mkdir(parents=True, exist_ok=True)
    durations = json.loads(DUR_FILE.read_text()) if DUR_FILE.exists() else {}
    for set_name, lines in LINES.items():
        if set_name == "voice" or (only_set and set_name != only_set):
            continue
        for key, text in lines.items():
            if only_key and key != only_key:
                continue
            if text.startswith("PLACEHOLDER"):
                continue
            audio = np.concatenate([a for _, _, a in pipe(text, voice=LINES["voice"], speed=1.0)])
            audio = np.concatenate([np.zeros(int(0.15 * 24000)), audio, np.zeros(int(0.25 * 24000))])
            name = f"{set_name}_{key}"
            sf.write(OUT / f"{name}.wav", audio, 24000)
            durations[name] = round(len(audio) / 24000, 3)
            print(f"{name}: {durations[name]} s")
    DUR_FILE.write_text(json.dumps(durations, indent=1), encoding="utf-8")


if __name__ == "__main__":
    main(*(sys.argv[1:3] or [None, None]))
