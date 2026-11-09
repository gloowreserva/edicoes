import sys, json, wave, numpy as np
from faster_whisper import WhisperModel
m = WhisperModel(sys.argv[3], device="cpu", compute_type="int8")
wf = wave.open(sys.argv[1]); audio = np.frombuffer(wf.readframes(wf.getnframes()), np.int16).astype(np.float32)/32768
segs, info = m.transcribe(audio, language="pt", word_timestamps=True, vad_filter=False, condition_on_previous_text=False,
                          initial_prompt="Transcreva literalmente, com repetições, gaguejos e hesitações: é, é, eu, eu.")
out = []
for s in segs:
    print(f"[{s.start:6.2f}-{s.end:6.2f}] {s.text}", flush=True)
    out.append({"start": s.start, "end": s.end, "text": s.text, "words": [{"start": w.start, "end": w.end, "word": w.word} for w in s.words]})
json.dump(out, open(sys.argv[2], "w"), ensure_ascii=False)
