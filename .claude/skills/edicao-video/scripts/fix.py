# retranscreve trechos com o modelo medium e substitui as palavras desses trechos no json
import sys, json, wave, numpy as np
from faster_whisper import WhisperModel
js, wav = sys.argv[1], sys.argv[2]; rngs = [tuple(map(float, r.split("-"))) for r in sys.argv[3:]]
m = WhisperModel("medium", device="cpu", compute_type="int8")
wf = wave.open(wav); sr = wf.getframerate()
data = json.load(open(js))
for a, b in rngs:
    wf.setpos(int(a * sr)); au = np.frombuffer(wf.readframes(int((b - a) * sr)), np.int16).astype(np.float32) / 32768
    segs, _ = m.transcribe(au, language="pt", word_timestamps=True, condition_on_previous_text=False,
        initial_prompt="Transcreva literalmente, com repetições, gaguejos e hesitações: é, é, eu, eu.")
    new = [{"start": w.start + a, "end": w.end + a, "word": w.word} for s in segs for w in s.words]
    for s in data: s["words"] = [w for w in s["words"] if not (a <= w["start"] < b)]
    data.append({"start": a, "end": b, "text": "", "words": new})
    print(f"--- {a}-{b}:", " ".join(f"{w['word'].strip()}[{w['start']:.2f}]" for w in new), flush=True)
for s in data: s["words"].sort(key=lambda w: w["start"])
data.sort(key=lambda s: s["start"])
json.dump(data, open(js, "w"), ensure_ascii=False)
