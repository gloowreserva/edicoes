"""Confere a 'presença' de cada trecho que vai entrar no vídeo: rosto bem de frente pra câmera e parado no lugar.
Marca quadros (8/s) sem rosto frontal rígido ou com a cabeça saindo da posição (balançou, virou, abaixou).
Uso: python3 -I checa_presenca.py BRUTO work/segs.json  -> lista de instantes suspeitos (tempo no bruto)
"""
import cv2, json, sys, numpy as np
v, segs = sys.argv[1], json.load(open(sys.argv[2]))
fd = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")
cap = cv2.VideoCapture(v); fps = cap.get(cv2.CAP_PROP_FPS)
ruins = []
for i, (a, b) in enumerate(segs):
    t = a; caixas = []
    while t < b:
        cap.set(cv2.CAP_PROP_POS_MSEC, t * 1000); ok, fr = cap.read()
        if not ok: break
        g = cv2.cvtColor(cv2.resize(fr, (270, 480)), cv2.COLOR_BGR2GRAY)
        f = fd.detectMultiScale(g, 1.08, 10, minSize=(60, 60))
        caixas.append((t, max(f, key=lambda r: r[2]) if len(f) else None)); t += 0.125
    ok_ = [c for _, c in caixas if c is not None]
    if not ok_: ruins.append((i, a, b, "sem rosto frontal no trecho todo")); continue
    mx, my = np.median([c[0] + c[2] / 2 for c in ok_]), np.median([c[1] + c[3] / 2 for c in ok_])
    mw = np.median([c[2] for c in ok_])
    for t, c in caixas:
        if c is None: ruins.append((i, a, b, f"{t:.2f}s sem rosto de frente"))
        elif abs(c[0] + c[2] / 2 - mx) > 0.35 * mw or abs(c[1] + c[3] / 2 - my) > 0.35 * mw:
            ruins.append((i, a, b, f"{t:.2f}s cabeça fora da posição"))
for r in ruins: print(f"  trecho {r[0]} ({r[1]:.2f}-{r[2]:.2f}): {r[3]}")
print(f"{len(segs)} trechos, {len(ruins)} quadros suspeitos")
