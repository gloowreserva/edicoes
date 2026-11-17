"""Transcreve só os trechos escolhidos (modelo melhor), com tempos no vídeo ORIGINAL.
Uso: python3 -I transcribe_ranges.py audio16k.wav saida.json modelo INI-FIM [INI-FIM ...]"""
import sys, json, wave, numpy as np
from faster_whisper import WhisperModel
wavp, out, model = sys.argv[1:4]
m = WhisperModel(model, device="cpu", compute_type="int8")
wf = wave.open(wavp); sr = wf.getframerate()
res = []
for r in sys.argv[4:]:
    a, b = map(float, r.split("-")); a0 = max(0, a - 1.0); b0 = b + 1.0
    wf.setpos(int(a0 * sr)); x = np.frombuffer(wf.readframes(int((b0 - a0) * sr)), np.int16).astype(np.float32) / 32768
    segs, _ = m.transcribe(x, language="pt", word_timestamps=True, vad_filter=False, condition_on_previous_text=False,
                           initial_prompt="Transcreva literalmente, com repetições: é, é, eu, eu. TikTok, Samuca, Nulle, app rosa.")
    for s in segs:
        ws = [{"start": w.start + a0, "end": w.end + a0, "word": w.word} for w in s.words]
        ws = [w for w in ws if a - 0.3 <= (w["start"] + w["end"]) / 2 <= b + 0.3]
        if ws:
            res.append({"start": ws[0]["start"], "end": ws[-1]["end"], "text": "".join(w["word"] for w in ws), "words": ws})
            print(f"[{ws[0]['start']:7.2f}-{ws[-1]['end']:7.2f}]{''.join(w['word'] for w in ws)}", flush=True)
json.dump(res, open(out, "w"), ensure_ascii=False)
