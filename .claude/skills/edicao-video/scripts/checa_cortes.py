"""Confere cada corte do estilo 4 falado: voz exatamente no ponto do corte = palavra cortada.
Uso: python3 -I checa_cortes.py BRUTO.wav work/segs.json transcricao.json
"""
import json, sys, wave, numpy as np
wf = wave.open(sys.argv[1]); sr = wf.getframerate()
a = np.frombuffer(wf.readframes(wf.getnframes()), np.int16).astype(np.float32) / 32768
segs = json.load(open(sys.argv[2]))
words = [w for s in json.load(open(sys.argv[3])) for w in s["words"]]
def db(t0, t1):
    x = a[max(0, int(t0 * sr)):int(t1 * sr)]
    return 20 * np.log10(np.sqrt(np.mean(x ** 2)) + 1e-9) if len(x) else -99
voz = np.percentile([db(t, t + 0.05) for t in np.arange(0, len(a) / sr - 0.05, 0.05)], 90)
lim = voz - 14
ruins = 0
for i, (s, e) in enumerate(segs):
    for nome, t0, t1, t in (("início", s, s + 0.04, s), ("fim", e - 0.04, e, e)):
        if db(t0, t1) > lim:
            perto = min(words, key=lambda w: min(abs(w["start"] - t), abs(w["end"] - t)))
            print(f"  ⚠ corte {i} {nome} em {t:.2f}s com voz ({db(t0, t1):.0f} dB) — perto de '{perto['word'].strip()}'")
            ruins += 1
print(f"{len(segs)} trechos, {ruins} cortes com voz no ponto (limite {lim:.0f} dB)")
