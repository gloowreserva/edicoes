"""Estilo 4 FALADO (UGC com fala: famílias A e B das referências da marca).
Uso: python3 -I estilo4f.py config.json

config:
  video, transcript (json do transcribe.py), work, output
  keep: [[ini, fim], ...]   trechos do BRUTO que ficam (a melhor tomada de cada frase), em ordem
  gap: 0.28                 pausa entre palavras acima disso é cortada (respiro)
  captions: "palavra"       1 palavra por vez, CAIXA ALTA branca com contorno (ref. 01/06/09)
            "destaque"      2-4 palavras, caixa alta, palavra-chave amarela (ref. 02)
            "nenhuma"
  cap_y: 1180               altura da legenda (px)
  replace: {"regex": "troca"}   correções da transcrição
  hook: {"text": "...", "dur": 3.0, "y": 560}   texto estilo TikTok clássico no início
  overlays: [{"at": seg_no_BRUTO, "dur": s, "file"|"files", "x", "y", "w"}]
  music, music_start, music_db: -24   (opcional, baixinha por baixo da voz)
"""
import json, os, re, subprocess, sys
from PIL import Image, ImageDraw, ImageFont, ImageFilter

cfg = json.load(open(sys.argv[1]))
W, H, FPS = 1080, 1920, 30
work = cfg["work"]; os.makedirs(work, exist_ok=True)
SK = os.path.dirname(os.path.abspath(__file__))
FONT = ImageFont.truetype("/usr/share/fonts/opentype/inter/Inter-SemiBold.otf", 50)
EMOJI = ImageFont.truetype("/usr/share/fonts/truetype/noto/NotoColorEmoji.ttf", 109)
TAG = ",setparams=color_primaries=bt709:color_trc=bt709:colorspace=bt709:range=tv"
ENC = ["-color_primaries", "bt709", "-color_trc", "bt709", "-colorspace", "bt709", "-color_range", "tv"]

def run(cmd):
    print(">>", " ".join(cmd)[:160], flush=True); subprocess.run(cmd, check=True)

# ---------- 1. trechos: tomadas escolhidas, cortando SÓ onde não há voz ----------
# O tempo das palavras do transcritor não é confiável pra cortar. Quem decide é o detector de voz
# (Silero VAD do faster-whisper), que ignora barulho de mão/roupa: corte nunca cai no meio de palavra.
words = [w for s in json.load(open(cfg["transcript"])) for w in s["words"]]
import numpy as np
from faster_whisper.vad import get_speech_timestamps, VadOptions
_raw = subprocess.run(["ffmpeg", "-v", "error", "-i", cfg["video"], "-vn", "-ac", "1", "-ar", "16000", "-f", "s16le", "-"],
                      capture_output=True).stdout
_au = np.frombuffer(_raw, np.int16).astype(np.float32) / 32768
_vo = VadOptions(threshold=cfg.get("vad_threshold", 0.45), min_silence_duration_ms=cfg.get("vad_silence_ms", 200),
                 speech_pad_ms=cfg.get("vad_pad_ms", 60), min_speech_duration_ms=150)
fala = [(t["start"] / 16000, t["end"] / 16000) for t in get_speech_timestamps(_au, _vo)]
json.dump(fala, open(f"{work}/fala.json", "w"))
def ajusta(a, b):  # borda marcada caindo no meio da fala: leva até o limite real da fala (no máx. 0,6s)
    for s, e in fala:
        if s < a < e and a - s <= 0.6: a = s
        if s < b < e and e - b <= 0.6: b = e
    return a, b
segs, exato = [], []
for k in cfg["keep"]:  # [ini, fim] ou [ini, fim, "x"] = borda exata (emenda entre duas palavras coladas)
    x_ = len(k) > 2 and k[2] == "x"
    a, b = (k[0], k[1]) if x_ else ajusta(k[0], k[1])
    pedacos = [(max(a, s), min(b, e)) for s, e in fala if e > a and s < b]
    if x_ and pedacos:  # borda exata manda: vale o ponto marcado, não o detector
        pedacos[0] = (a, pedacos[0][1]); pedacos[-1] = (pedacos[-1][0], b)
    for x, y in pedacos:  # junta pedaços separados por respiro curtíssimo
        if segs and segs[-1][1] >= a and x - segs[-1][1] < cfg.get("respiro_max", 0.12): segs[-1] = (segs[-1][0], y)
        elif y - x >= 0.3: segs.append((x, y)); exato.append((x_ and x == a, x_ and y == b))
    if x_ and segs: exato[-1] = (exato[-1][0], segs[-1][1] == b)
# folga de 0,1s antes/depois (o começo de palavra suave escapa do detector), sem invadir o vizinho nem as bordas exatas
segs = [(a if ea else max(a - 0.06, segs[i - 1][1] if i and segs[i - 1][1] <= a else 0), b if eb else b)
        for i, ((a, b), (ea, eb)) in enumerate(zip(segs, exato))]
segs = [(round(a, 3), round(b, 3)) for a, b in segs]
# garante que nenhuma borda (não exata) caia com voz: recua o início / avança o fim até o silêncio (máx. 0,25s)
def _db(t0, t1):
    x = _au[max(0, int(t0 * 16000)):int(t1 * 16000)]
    return 20 * np.log10(np.sqrt(np.mean(x ** 2)) + 1e-9) if len(x) else -99
_lim = np.percentile([_db(t, t + 0.05) for t in np.arange(0, len(_au) / 16000 - 0.05, 0.05)], 90) - 16
if cfg.get("apara_olhar", True):
    # presença: apara as pontas do trecho onde ele já desviou o olhar (pro roteiro/pacote) — no máx. 0,35s
    import cv2
    _fd = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")
    _cap = cv2.VideoCapture(cfg["video"])
    def de_frente(t):
        _cap.set(cv2.CAP_PROP_POS_MSEC, t * 1000); ok, fr = _cap.read()
        if not ok: return True
        g = cv2.cvtColor(cv2.resize(fr, (270, 480)), cv2.COLOR_BGR2GRAY)
        return len(_fd.detectMultiScale(g, 1.08, 10, minSize=(60, 60))) > 0
    novos, nex = [], []
    for (a, b), (ea, eb) in zip(segs, exato):
        t = b
        while not eb and t > b - 0.35 and not de_frente(t - 0.02) and _db(t - 0.16, t - 0.04) <= _lim: t -= 0.04
        b2 = t if t < b else b
        t = a
        while not ea and t < a + 0.25 and not de_frente(t + 0.02) and _db(t + 0.04, t + 0.16) <= _lim: t += 0.04
        if b2 - t >= 0.3: novos.append((round(t, 3), round(b2, 3))); nex.append((ea, eb))
    segs, exato = novos, nex
exato_final = exato
_s2 = []
for i, ((a, b), (ea, eb)) in enumerate(zip(segs, exato_final)):
    lo = _s2[-1][1] if _s2 else 0
    if not ea:
        n = 0
        while _db(a - 0.02, a) > _lim - 25 and n < 15 and a - 0.02 > lo: a -= 0.02; n += 1
        a = max(lo, a - 0.04)  # uns 40ms de silêncio antes da primeira sílaba
    if not eb:
        n = 0
        while _db(b, b + 0.02) > _lim - 25 and n < 15: b += 0.02; n += 1
    _s2.append((round(a, 3), round(b, 3)))
segs = _s2
json.dump(segs, open(f"{work}/segs.json", "w"))
if cfg.get("dry"):  # só calcula os cortes (pra conferir), sem renderizar
    print("segs:", [(round(a, 2), round(b, 2)) for a, b in segs]); sys.exit(0)

# "segura imagem": {"v0": t} / {"v1": t} — o áudio fica inteiro, mas a imagem segura o 1º/último quadro
# com ele de frente (esconde o giro de cabeça de 0,2–0,3s no começo/fim da fala sem cortar palavra)
congela = list(cfg.get("segura_imagem", []))
GRADE = "," + cfg["grade"] if cfg.get("grade") else ",eq=gamma=0.8:contrast=1.12:brightness=-0.05:saturation=1.15"
if cfg.get("grade") == "nenhum": GRADE = ""
# segura imagem AUTOMÁTICO: em todo começo/fim de trecho, se ele já está virando o rosto, a imagem segura
# o quadro firme mais próximo (máx. 0,5s) e o áudio segue inteiro
if cfg.get("segura_auto", True):
    import cv2
    _fd2 = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")
    _cp = cv2.VideoCapture(cfg["video"])
    def _rosto(t):
        _cp.set(cv2.CAP_PROP_POS_MSEC, t * 1000); ok, fr = _cp.read()
        if not ok: return None
        g = cv2.cvtColor(cv2.resize(fr, (270, 480)), cv2.COLOR_BGR2GRAY)
        f = _fd2.detectMultiScale(g, 1.08, 8, minSize=(60, 60))
        return max(f, key=lambda r: r[2]) if len(f) else None
    for a, b in segs:
        meio = [r for r in (_rosto(a + (b - a) * k / 6) for k in range(1, 6)) if r is not None]
        if not meio: continue
        mx = np.median([r[0] + r[2] / 2 for r in meio]); my = np.median([r[1] + r[3] / 2 for r in meio])
        mw = np.median([r[2] for r in meio])
        def firme(t):
            r = _rosto(t)
            return r is not None and abs(r[0] + r[2] / 2 - mx) < 0.22 * mw and abs(r[1] + r[3] / 2 - my) < 0.22 * mw \
                and abs(r[2] - mw) < 0.15 * mw
        if b - a > 1.2:
            if not any("v1" in c and abs(c["v1"] - b) < 0.6 for c in congela):
                t = b - 0.03
                while t > b - 0.3 and not firme(t): t -= 1 / 15
                if t < b - 0.05 and firme(t): congela.append({"v1": round(t, 3)})
            if not any("v0" in c and abs(c["v0"] - a) < 0.6 for c in congela):
                t = a + 0.03
                while t < a + 0.3 and not firme(t): t += 1 / 15
                if t > a + 0.05 and firme(t): congela.append({"v0": round(t, 3)})
    json.dump(congela, open(f"{work}/segura.json", "w"))
parts = []
for i, (a, b) in enumerate(segs):
    p = f"{work}/p{i:03d}.mp4"
    vs = next((c["v0"] - a for c in congela if "v0" in c and a <= c["v0"] < min(b, a + 0.6)), 0)
    ve = next((b - c["v1"] for c in congela if "v1" in c and max(a, b - 0.6) < c["v1"] <= b), 0)
    hold = ""
    if vs > 0 or ve > 0:
        hold = (f"trim=start={vs:.3f}:end={b - a - ve:.3f},setpts=PTS-STARTPTS,"
                f"tpad=start_duration={vs:.3f}:start_mode=clone:stop_duration={ve:.3f}:stop_mode=clone,")
    run(["ffmpeg", "-v", "error", "-y", "-ss", f"{a:.3f}", "-i", cfg["video"], "-t", f"{b - a:.3f}",
         "-vf", f"{hold}scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},fps={FPS},setsar=1{TAG}{GRADE}",
         "-af", f"afade=t=in:d=0.012,afade=t=out:st={max(0, b - a - 0.012):.3f}:d=0.012",
         "-c:v", "libx264", "-preset", "veryfast", "-crf", "15", *ENC, "-c:a", "pcm_s16le", "-ar", "48000", p.replace(".mp4", ".mov")])
    parts.append(p.replace(".mp4", ".mov"))
open(f"{work}/list.txt", "w").write("".join(f"file '{p}'\n" for p in parts))
cut = f"{work}/cut.mov"
run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", f"{work}/list.txt", "-c", "copy", cut])
real = [float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", p],
        capture_output=True, text=True).stdout) for p in parts]
total = sum(real)

def remap_fim(t):  # fim de um bloco: vai até o fim do trecho onde ele cai (sem sobrar quadro solto)
    acc = 0.0
    for (a, b), d in zip(segs, real):
        if t < a: return acc
        if t <= b + 0.3: return acc + d
        acc += d
    return acc

def remap(t):
    acc = 0.0
    for (a, b), d in zip(segs, real):
        if t < a: return acc
        if t <= b: return acc + min(t - a, d)
        acc += d
    return acc

# ---------- 2. legenda (ASS) ----------
def clean(t):
    for k, v in cfg.get("replace", {}).items(): t = re.sub(k, v, t, flags=re.I)
    return t
def kept(t): return any(a <= t <= b for a, b in segs)
fix = cfg.get("word_fix", {})  # {"tempo": "nova"} ou {"tempo|palavra": "nova"}; "" apaga
def fixw(w):
    for k, v in fix.items():
        t, _, orig = k.partition("|")
        if abs(w["start"] - float(t)) < 0.04 and (not orig or orig.lower() == w["word"].strip(" .,!?").lower()): return v
    return clean(w["word"].strip())
if cfg.get("recaption", True):
    # legenda tirada do vídeo JÁ CORTADO (modelo medium): tempo exato de cada palavra no vídeo final
    import wave, numpy as np
    from faster_whisper import WhisperModel
    wav = f"{work}/cut.wav"
    run(["ffmpeg", "-v", "error", "-y", "-i", cut, "-vn", "-ac", "1", "-ar", "16000", wav])
    wf = wave.open(wav); au = np.frombuffer(wf.readframes(wf.getnframes()), np.int16).astype(np.float32) / 32768
    m = WhisperModel(cfg.get("caption_model", "medium"), device="cpu", compute_type="int8")
    sg, _ = m.transcribe(au, language="pt", word_timestamps=True, condition_on_previous_text=False)
    kw = [dict(w=clean(w.word.strip()), s=w.start, e=w.end) for x in sg for w in x.words]
    for de, para in cfg.get("phrase_fix", []):  # ex.: ["a cara", "acorda"] (erro de transcrição em 2+ palavras)
        toks = de.lower().split(); i = 0
        while i <= len(kw) - len(toks):
            if [re.sub(r"[^\w]", "", x["w"].lower()) for x in kw[i:i + len(toks)]] == toks:
                kw[i:i + len(toks)] = [dict(w=para, s=kw[i]["s"], e=kw[i + len(toks) - 1]["e"])]
            i += 1
    # o transcritor da legenda às vezes pula palavra: completa com a transcrição do bruto onde ficou buraco
    for w in words:
        c = (w["start"] + w["end"]) / 2
        if not kept(c): continue
        t = remap(w["start"]); d = min(w["end"] - w["start"], 0.6)
        prev = [x for x in kw if x["s"] <= t]; nxt = [x for x in kw if x["s"] > t]
        livre = (not prev or prev[-1]["e"] <= t + 0.05) and (not nxt or nxt[0]["s"] >= t + 0.25)
        txt = clean(w["word"].strip())
        perto = " ".join(x["w"].lower() for x in kw if abs(x["s"] - t) < 1.5)
        if livre and re.sub(r"\W", "", txt) and re.sub(r"\W", "", txt.lower()) not in perto:
            kw.append(dict(w=txt, s=t, e=min(t + d, nxt[0]["s"] if nxt else t + d))); kw.sort(key=lambda x: x["s"])
    json.dump(kw, open(f"{work}/legenda_palavras.json", "w"), ensure_ascii=False)
else:
    kw = [dict(w=fixw(w), s=remap(w["start"]), e=remap(w["end"])) for w in words if kept((w["start"] + w["end"]) / 2)]
kw = [w for w in kw if re.sub(r"\W", "", w["w"])]
def ts(t):
    t = max(0, t); return f"{int(t // 3600)}:{int(t % 3600 // 60):02d}:{t % 60:05.2f}"
cy = cfg.get("cap_y", 1180)
ass = [f"""[Script Info]
ScriptType: v4.00+
PlayResX: {W}
PlayResY: {H}
WrapStyle: 0

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Palavra,Inter Black,92,&H00FFFFFF,&H00FFFFFF,&H00000000,&H64000000,-1,0,0,0,100,100,1,0,1,5,3,5,60,60,0,1
Style: Chave,Inter Black,84,&H005AFF3C,&H005AFF3C,&H00103A10,&H64000000,-1,0,0,0,100,100,0,0,1,7,3,5,60,60,0,1
Style: Pct,Inter Black,120,&H00FFFFFF,&H00FFFFFF,&H00000000,&H64000000,-1,0,0,0,100,100,0,0,1,6,3,4,60,60,0,1
Style: Destaque,Inter ExtraBold,74,&H00FFFFFF,&H00FFFFFF,&H00000000,&H64000000,-1,0,0,0,88,100,0,0,1,5,2,5,60,60,0,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text"""]
mode = cfg.get("captions", "palavra")
pos = r"{\pos(540," + str(cy) + ")"
STOP = set("o a os as um uma de da do das dos e é que pra para no na nos nas em com se te eu você vai ele ela isso esse essa por mais muito já".split())
if mode == "palavra":
    for i, w in enumerate(kw):
        e = kw[i + 1]["s"] if i + 1 < len(kw) and kw[i + 1]["s"] - w["e"] < 0.6 else w["e"] + 0.25
        t = w["w"].strip(".,!?;:").upper()
        ass.append(f"Dialogue: 1,{ts(w['s'])},{ts(e)},Palavra,,0,0,0,,{pos}" + r"\fscx90\fscy90\t(0,70,\fscx100\fscy100)}" + t)
elif mode == "destaque":
    groups, g = [], []
    for w in kw:
        g.append(w)
        if len(g) >= 3 or len(" ".join(x["w"] for x in g)) > 16 or re.search(r"[.,?!]$", w["w"]): groups.append(g); g = []
    if g: groups.append(g)
    for i, g in enumerate(groups):
        e = groups[i + 1][0]["s"] if i + 1 < len(groups) and groups[i + 1][0]["s"] - g[-1]["e"] < 0.6 else g[-1]["e"] + 0.25
        ws = [x["w"].strip(".,!?;:").upper() for x in g]
        cand = [j for j, x in enumerate(ws) if x.lower() not in STOP and len(x) > 3]
        k = max(cand, key=lambda j: len(ws[j])) if cand else -1
        txt = " ".join(r"{\c&H00D7FF&}" + x + r"{\c&HFFFFFF&}" if j == k else x for j, x in enumerate(ws))
        ass.append(f"Dialogue: 1,{ts(g[0]['s'])},{ts(e)},Destaque,,0,0,0,,{pos}" + r"\fscx92\fscy92\t(0,80,\fscx100\fscy100)}" + txt)
for k in cfg.get("keywords", []):  # palavras-chave soltas (ref. 08)
    a = remap(k["at"]); e = a + k.get("dur", 1.4)
    ass.append(f"Dialogue: 2,{ts(a)},{ts(e)},Chave,,0,0,0,," + r"{\pos(540," + str(k.get("y", 1150)) + r")\fscx40\fscy40\t(0,120,\fscx110\fscy110)\t(120,200,\fscx100\fscy100)}" + k["text"].replace("\n", r"\N"))
for sp in cfg.get("split", []):  # rótulo grande (ex.: 30%) na parte de cima
    if sp.get("label"):
        ass.append(f"Dialogue: 2,{ts(remap(sp['at']))},{ts(remap_fim(sp['until']))},Pct,,0,0,0,," + r"{\pos(70," + str(cfg.get("split_h", 640) // 2) + r")}" + sp["label"])
assf = f"{work}/leg.ass"; open(assf, "w").write("\n".join(ass) + "\n")

# ---------- 3. hook (caixa branca estilo TikTok) e cartões ----------
sys.argv = [sys.argv[0]]  # reaproveita as funções de desenho do 4C sem rodar o 4C
src = open(os.path.join(SK, "estilo4c.py")).read()
ns = {}
exec(src.split("# 1. cortes")[0].replace("cfg = json.load(open(sys.argv[1]))", "cfg = {'work': '" + work + "'}"), ns)
card_src = src[src.index("def card("):src.index("starts = [")]
exec(card_src, ns)
text_png, card = ns["text_png"], ns["card"]

inputs, fc, last, n = ["-i", cut], [], "[0:v]", 1
sps = cfg.get("split", [])
if sps:
    th = cfg.get("split_h", 640); bh = H - th
    fc.append(f"[0:v]split=2[base][sb];[sb]crop={W}:{bh}:0:{int((H - bh) * 0.3)},split={len(sps)}" + "".join(f"[bot{i}]" for i in range(len(sps))))
    last = "[base]"
    for i, sp in enumerate(sps):
        a, b = remap(sp["at"]), remap_fim(sp["until"])
        inputs += ["-loop", "1", "-framerate", str(FPS), "-t", f"{total:.3f}", "-i", sp["file"]]
        cy = "ih-oh" if sp.get("crop_y") == "base" else "(ih-oh)/2"
        fc.append(f"[{n}:v]scale={W}:{th}:force_original_aspect_ratio=increase,crop={W}:{th}:(iw-ow)/2:{cy},setsar=1,format=rgba,"
                  f"scale=out_color_matrix=bt709:out_range=tv,format=yuv420p[top{i}];[top{i}][bot{i}]vstack[sp{i}]")
        fc.append(f"{last}[sp{i}]overlay=0:0:enable='between(t,{a - 0.034:.3f},{b + 0.034:.3f})'[sv{i}]"); last = f"[sv{i}]"; n += 1
if cfg.get("hook"):
    hk = cfg["hook"]; png = f"{work}/hook.png"; text_png(hk["text"], hk.get("y", 560), png)
    inputs += ["-loop", "1", "-framerate", str(FPS), "-t", f"{total:.3f}", "-i", png]
    fc.append(f"[{n}:v]scale=out_color_matrix=bt709:out_range=tv,format=yuva420p[hk]")
    fc.append(f"{last}[hk]overlay=0:0:enable='between(t,0,{hk.get('dur', 3.0):.3f})'[vh]"); last = "[vh]"; n += 1
for k, ov in enumerate(cfg.get("overlays", [])):
    a = remap(ov["at"]); b = min(a + ov.get("dur", 2.5), total)
    files = ov.get("files") or [ov["file"]]; step = (b - a) / len(files)
    for j, f in enumerate(files):
        png = f"{work}/ov{k:02d}_{j}.png"; off = card(f, ov.get("w", 420), png)
        s, e = a + j * step, a + (j + 1) * step
        inputs += ["-loop", "1", "-framerate", str(FPS), "-t", f"{total:.3f}", "-i", png]
        fi = "" if j else f",fade=in:st={s:.3f}:d=0.15:alpha=1"
        fc.append(f"[{n}:v]format=rgba{fi},scale=out_color_matrix=bt709:out_range=tv,format=yuva420p[o{k}_{j}]")
        fc.append(f"{last}[o{k}_{j}]overlay={ov['x'] - off}:{ov['y'] - off}:enable='between(t,{s:.3f},{e - 0.001:.3f})'[v{k}_{j}]")
        last = f"[v{k}_{j}]"; n += 1
fc.append(f"{last}ass={assf}[vout]")

# ---------- 4. áudio: voz normalizada (+ música baixinha opcional) ----------
if cfg.get("music"):
    inputs += ["-ss", str(cfg.get("music_start", 0)), "-i", cfg["music"]]
    fc.append(f"[0:a]loudnorm=I=-14:TP=-1.5:LRA=11,aresample=48000[voz];[{n}:a]aresample=48000,atrim=0:{total:.3f},asetpts=PTS-STARTPTS,"
              f"volume={cfg.get('music_db', -24)}dB,afade=t=out:st={total - 0.8:.3f}:d=0.8[mus];"
              f"[voz][mus]amix=inputs=2:duration=first:normalize=0[aout]")
else:
    fc.append("[0:a]loudnorm=I=-14:TP=-1.5:LRA=11,aresample=48000[aout]")
run(["ffmpeg", "-v", "error", "-y", *inputs, "-filter_complex", ";".join(fc), "-map", "[vout]", "-map", "[aout]",
     "-c:v", "libx264", "-preset", "medium", "-crf", "19", "-pix_fmt", "yuv420p", *ENC, "-c:a", "aac", "-b:a", "192k",
     "-ar", "48000", "-movflags", "+faststart", "-t", f"{total:.3f}", cfg["output"]])
print(f"OK {cfg['output']}  {total:.1f}s, {len(segs)} trechos")
