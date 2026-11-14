"""Confere as EMENDAS (fala corrida): silêncio que sobra em cada junção de takes e o texto em volta dela.
Uso: python3 -I emendas.py FINAL.mp4 work/segs_final.json [modelo_whisper]
     python3 -I emendas.py BRUTO.MOV work/segs_final.json small --bruto   (antes de renderizar: monta o áudio dos trechos)
  - mede o vão sem voz que atravessa cada emenda (soma do fim do take + começo do próximo)
  - marca ⚠ onde o vão passa de 0,18s (respiro audível) -> usar "tail": 0.04 e "lead": 0.02 no config
  - retranscreve ±1,5s em volta de cada emenda (pega palavra comida ou repetida)
"""
import json, subprocess, sys, numpy as np
v, segs = sys.argv[1], json.load(open(sys.argv[2]))
modelo = sys.argv[3] if len(sys.argv) > 3 and not sys.argv[3].startswith("--") else "small"
FPS = 30
raw = subprocess.run(["ffmpeg", "-v", "error", "-i", v, "-vn", "-ac", "1", "-ar", "16000", "-f", "s16le", "-"],
                     capture_output=True).stdout
au = np.frombuffer(raw, np.int16).astype(np.float32) / 32768
if "--bruto" in sys.argv:  # junta os trechos do bruto (mesma montagem do render: alinhada ao quadro)
    au = np.concatenate([au[int(round(a * 16000)):int(round(a * 16000)) + round((b - a) * FPS) * (16000 // FPS)]
                         for a, b in segs])
n = len(au) // 160
env = 20 * np.log10(np.sqrt((au[:n * 160].reshape(n, 160) ** 2).mean(axis=1)) + 1e-9)
thr = max(-48.0, float(np.percentile(env, 95)) - 28)
juncoes, t = [], 0.0
for a, b in segs[:-1]:
    t += round((b - a) * FPS) / FPS; juncoes.append(t)
from faster_whisper import WhisperModel
m = WhisperModel(modelo, device="cpu", compute_type="int8")
ruins = 0
for i, j in enumerate(juncoes):
    k = int(j * 100); l = r = k
    while l > 0 and env[l - 1] <= thr and k - l < 100: l -= 1
    while r < n and env[r] <= thr and r - k < 100: r += 1
    vao = (r - l) / 100
    a0 = max(0, j - 1.5); pedaco = au[int(a0 * 16000):int((j + 1.5) * 16000)]
    txt = " ".join(s.text.strip() for s in m.transcribe(pedaco, language="pt", beam_size=5)[0])
    flag = "⚠" if vao > 0.18 else " "
    ruins += vao > 0.18
    print(f"{flag} emenda {i:02d} em {j:6.2f}s  vão {vao:.2f}s  | {txt}")
print(f"{len(juncoes)} emendas, {ruins} com respiro (> 0,18s)")
