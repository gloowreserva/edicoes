import sys, wave, numpy as np
from faster_whisper import WhisperModel
wav, a, b = sys.argv[1], float(sys.argv[2]), float(sys.argv[3])
wf = wave.open(wav); sr = wf.getframerate(); wf.setpos(int(a * sr))
au = np.frombuffer(wf.readframes(int((b - a) * sr)), np.int16).astype(np.float32) / 32768
m = WhisperModel("medium", device="cpu", compute_type="int8")
segs, _ = m.transcribe(au, language="pt", word_timestamps=True, condition_on_previous_text=False,
                       initial_prompt="Transcreva literalmente, com repetições, gaguejos e hesitações: é, é, eu, eu.")
for s in segs: print(" ".join(f"{w.word.strip()}[{w.start + a:.2f}]" for w in s.words))
