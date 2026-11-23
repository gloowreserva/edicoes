"""Retranscreve um trecho e substitui as palavras desse intervalo na transcrição (corrige trechos que o Whisper pulou ou com tempo errado).
Uso: python3 -I retrecho.py transcricao.json audio.wav INICIO FIM
"""
import sys, json, wave, numpy as np
from faster_whisper import WhisperModel
js, wav, a, b = sys.argv[1], sys.argv[2], float(sys.argv[3]), float(sys.argv[4])
wf = wave.open(wav); sr = wf.getframerate(); wf.setpos(int(a * sr))
au = np.frombuffer(wf.readframes(int((b - a) * sr)), np.int16).astype(np.float32) / 32768
m = WhisperModel("medium", device="cpu", compute_type="int8")
segs, _ = m.transcribe(au, language="pt", word_timestamps=True, condition_on_previous_text=False,
                       initial_prompt="Transcreva literalmente, com repetições, gaguejos e hesitações: é, é, eu, eu.")
new = [{"start": s.start + a, "end": s.end + a, "text": s.text,
        "words": [{"start": w.start + a, "end": w.end + a, "word": w.word} for w in s.words]} for s in segs]
old = json.load(open(js))
keep = []
for s in old:
    ws = [w for w in s["words"] if not (a <= (w["start"] + w["end"]) / 2 <= b)]
    if ws: keep.append({**s, "words": ws, "start": ws[0]["start"], "end": ws[-1]["end"]})
out = sorted(keep + new, key=lambda s: s["start"])
json.dump(out, open(js, "w"), ensure_ascii=False)
for s in new: print(f"[{s['start']:.2f}-{s['end']:.2f}] {s['text']}")
