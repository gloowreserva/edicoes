"""Estilo 4 — cortes de mentoria (gravação horizontal do Meet -> vertical 1080x1920).
Uso: python3 -I mentoria.py config.json

config:
  video, work, output, transcript (tempos do vídeo ORIGINAL)
  ranges: [[ini, fim], ...] na ordem em que entram no corte (o 1º pode ser o cold open)
  layout: arquivo json com uma letra por segundo: M = câmera cheia, S = tela compartilhada (ver classifica_layout.py)
  remove, replace, gap_max, lead, tail: como no edit.py
  hook {text, dur}, stickers [{start, end, text}]
  punch: [[ini, fim], ...] trechos com punch-in (zoom 15%)
  highlight: palavras que ficam amarelas na legenda (senão escolhe a mais forte do bloco)
  music, music_start, music_gain_db (padrão -25)
  screen_mode: "blur" (padrão: tela desfocada + orador grande no centro) ou "show" (tela visível + orador no canto)
  screen_crop: [x, y, w, h] em px do quadro original, área da tela compartilhada (padrão [0, 130, 1440, 820])
  thumb_face: [x, y, lado] recorte quadrado do rosto na miniatura (padrão [1560, 408, 228])
  thumb: [x, y, w, h] da miniatura do orador durante a tela compartilhada (padrão [1440, 405, 480, 270])
"""
import json, os, re, subprocess, sys, wave
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

cfg = json.load(open(sys.argv[1]))
W, H, FPS, SR = 1080, 1920, 30, 48000
work = cfg["work"]; os.makedirs(work, exist_ok=True)
src = cfg["video"]
LAY = json.load(open(cfg["layout"])) if cfg.get("layout") else ""

def run(cmd):
    print(">>", " ".join(cmd)[:240], flush=True)
    subprocess.run(cmd, check=True)

def lay(t):
    i = int(t)
    return LAY[i] if 0 <= i < len(LAY) else "M"

# ---------- áudio do trecho (só a janela usada, não a mentoria inteira) ----------
lo_all = min(a for a, b in cfg["ranges"]) - 1; hi_all = max(b for a, b in cfg["ranges"]) + 1
lo_all = max(0.0, lo_all)
wav = f"{work}/audio_src.wav"
run(["ffmpeg", "-v", "error", "-y", "-ss", f"{lo_all:.3f}", "-to", f"{hi_all:.3f}", "-i", src, "-vn", "-ac", "2",
     "-ar", str(SR), "-c:a", "pcm_s16le", wav])
with wave.open(wav) as wf:
    AUD = np.frombuffer(wf.readframes(wf.getnframes()), np.int16).reshape(-1, 2)
mono = AUD.astype(np.float32).mean(axis=1) / 32768
HOP = SR // 100; nH = len(mono) // HOP
ENV = 20 * np.log10(np.sqrt((mono[:nH * HOP].reshape(nH, HOP) ** 2).mean(axis=1)) + 1e-9)
THR = cfg.get("speech_db", max(-48.0, float(np.percentile(ENV, 95)) - 28))
def loud(t):
    i = int((t - lo_all) * 100)
    return 0 <= i < nH and ENV[i] > THR

# ---------- fala corrida dentro de cada range ----------
removes = [tuple(x) for x in cfg.get("remove", [])]
def in_remove(t): return any(a <= t <= b for a, b in removes)
def remove_between(t0, t1): return any(a < t1 and b > t0 for a, b in removes)
gap_max, lead, tail = cfg.get("gap_max", 0.25), cfg.get("lead", 0.03), cfg.get("tail", 0.06)
TR = [w for s in json.load(open(cfg["transcript"])) for w in s["words"]]

segs = []  # em ordem de saída
for ra, rb in cfg["ranges"]:
    ws = [(w["start"], w["end"]) for w in TR if ra <= (w["start"] + w["end"]) / 2 <= rb]
    ws = [(a, b) for a, b in ws if not in_remove((a + b) / 2)]
    blocks = []
    for a, b in ws:
        if blocks and a - blocks[-1][1] <= gap_max and not remove_between(blocks[-1][1], a):
            blocks[-1][1] = max(blocks[-1][1], b)
        else:
            blocks.append([a, b])
    rs = []
    for i, (a, b) in enumerate(blocks):
        lo = max([ra - 0.05] + [y for x, y in removes if y <= a + 0.05] + ([blocks[i - 1][1]] if i else []))
        hi = min([rb + 0.05] + [x for x, y in removes if x >= b - 0.05] + ([blocks[i + 1][0]] if i + 1 < len(blocks) else []))
        s0 = a
        while s0 - 0.01 > max(lo, a - 0.15) and loud(s0 - 0.01): s0 -= 0.01
        e0 = b
        while e0 + 0.01 < min(hi, b + 0.20) and loud(e0): e0 += 0.01
        s0, e0 = max(lo, s0 - lead), min(hi, e0 + tail)
        if rs and s0 - rs[-1][1] < 0.02: rs[-1] = (rs[-1][0], e0)
        else: rs.append((s0, e0))
    segs += rs
segs = [(round(a * FPS) / FPS, round(b * FPS) / FPS) for a, b in segs]
segs = [(a, b) for a, b in segs if b - a >= 3 / FPS]

# divide cada segmento onde o layout muda (câmera <-> tela)
parts = []
for a, b in segs:
    cuts = [a] + [float(s) for s in range(int(a) + 1, int(b) + 1) if lay(s) != lay(s - 1) and a < s < b] + [b]
    for x, y in zip(cuts, cuts[1:]):
        x, y = round(x * FPS) / FPS, round(y * FPS) / FPS
        if y - x >= 1 / FPS: parts.append((x, y, lay((x + y) / 2)))
# junta pedaços minúsculos ao vizinho (evita piscar de layout)
fixed = []
for p in parts:
    if fixed and p[1] - p[0] < 0.7 and fixed[-1][1] == p[0]:
        fixed[-1] = (fixed[-1][0], p[1], fixed[-1][2])
    else:
        fixed.append(p)
parts = fixed
print("partes:", [(round(a, 2), round(b, 2), l) for a, b, l in parts])

# tempo de saída de cada instante do original (o mesmo instante pode aparecer 2x por causa do cold open:
# devolve a 1ª ocorrência a partir de 'after')
def remap_all(t):
    acc, out = 0.0, []
    for a, b, _ in parts:
        if a - 0.02 <= t <= b + 0.02: out.append(acc + min(max(t - a, 0), b - a))
        acc += b - a
    return out
total = sum(b - a for a, b, _ in parts)

# ---------- rosto do orador (câmera cheia) ----------
import cv2
CASC = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")
def face_x(a, b):
    xs = []
    for t in np.linspace(a + 0.1, max(a + 0.1, b - 0.1), 4):
        r = subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{t:.2f}", "-i", src, "-frames:v", "1", "-vf", "scale=960:540",
                            "-f", "rawvideo", "-pix_fmt", "gray", "-"], capture_output=True).stdout
        if len(r) < 960 * 540: continue
        g = np.frombuffer(r, np.uint8).reshape(540, 960)
        f = CASC.detectMultiScale(g, 1.1, 5, minSize=(60, 60))
        if len(f):
            x, y, w, h = max(f, key=lambda q: q[2] * q[3]); xs.append((x + w / 2) * 2)
    return float(np.median(xs)) if xs else cfg.get("face_x", 840)

punch = [tuple(x) for x in cfg.get("punch", [])]
SC = cfg.get("screen_crop", [0, 130, 1440, 820])
TH = cfg.get("thumb", [1440, 405, 480, 270])

# moldura arredondada da miniatura do orador (layout de tela)
TW = 400
tm = Image.new("L", (TW, TW), 0); ImageDraw.Draw(tm).rounded_rectangle([0, 0, TW - 1, TW - 1], 40, fill=255)
tm.save(f"{work}/thumbmask.png")
fr = Image.new("RGBA", (TW + 100, TW + 100), (0, 0, 0, 0))
sh = Image.new("RGBA", fr.size, (0, 0, 0, 0)); sh.paste((0, 0, 0, 170), (50, 62), tm)
fr = Image.alpha_composite(fr, sh.filter(ImageFilter.GaussianBlur(18)))
m8 = Image.new("L", (TW + 12, TW + 12), 0); ImageDraw.Draw(m8).rounded_rectangle([0, 0, TW + 11, TW + 11], 46, fill=255)
fr.paste((255, 255, 255, 255), (44, 44), m8)
fr.save(f"{work}/thumbframe.png")
BWm = 820
bm = Image.new("L", (BWm, BWm), 0); ImageDraw.Draw(bm).rounded_rectangle([0, 0, BWm - 1, BWm - 1], 60, fill=255); bm.save(f"{work}/bigmask.png")
bf = Image.new("RGBA", (BWm + 112, BWm + 112), (0, 0, 0, 0))
bs = Image.new("RGBA", bf.size, (0, 0, 0, 0)); bs.paste((0, 0, 0, 180), (56, 70), bm)
bf = Image.alpha_composite(bf, bs.filter(ImageFilter.GaussianBlur(22)))
b8 = Image.new("L", (BWm + 16, BWm + 16), 0); ImageDraw.Draw(b8).rounded_rectangle([0, 0, BWm + 15, BWm + 15], 68, fill=255)
bf.paste((255, 255, 255, 255), (48, 48), b8); bf.save(f"{work}/bigframe.png")

files = []
for i, (a, b, l) in enumerate(parts):
    nf = round((b - a) * FPS)
    out = f"{work}/part{i:03d}_{a:.2f}_{b:.2f}_{l}.mp4"
    files.append(out)
    if os.path.exists(out) and os.path.getsize(out) > 0: continue  # reaproveita parte já renderizada
    mid = (a + b) / 2
    z = 1.15 if any(x <= mid <= y for x, y in punch) else 1.0
    if l == "S" and cfg.get("screen_mode", "blur") == "show":
        # tela visível (só quando não expõe perfil/dados de aluno) + orador em janela no canto
        x, y, w, h = SC; sh_ = int(W * h / w) // 2 * 2
        tx, ty, tw, thh = TH; fw = min(tw, thh); fxc = tx + tw / 2
        fc = (f"[0:v]split=3[a][b][c];"
              f"[a]crop={w}:{h}:{x}:{y},scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},boxblur=30:3,eq=brightness=-0.25[bg];"
              f"[b]crop={w}:{h}:{x}:{y},scale={W}:{sh_}[sc];"
              f"[c]crop={fw}:{fw}:{int(fxc - fw / 2)}:{ty},scale={TW}:{TW}:flags=lanczos,unsharp=5:5:0.8[th];"
              f"movie={work}/thumbmask.png,format=gray,scale={TW}:{TW}[tm];[th][tm]alphamerge[thr];"
              f"movie={work}/thumbframe.png[tf];"
              f"[bg][sc]overlay=0:{560}[v1];[v1][tf]overlay={W - TW - 60 - 50}:{560 + sh_ - 140 - 50}[v2];"
              f"[v2][thr]overlay={W - TW - 60 + 6}:{560 + sh_ - 140 + 6},fps={FPS},setsar=1[v]")
        run(["ffmpeg", "-v", "error", "-y", "-ss", f"{a:.4f}", "-i", src, "-filter_complex", fc, "-map", "[v]",
             "-frames:v", str(nf), "-an", "-c:v", "libx264", "-preset", "veryfast", "-crf", "17", "-pix_fmt", "yuv420p",
             "-threads", "3", out])
    elif l == "S":
        # padrão: tela desfocada ao fundo (protege perfis de alunos) + orador grande no centro
        x, y, w, h = SC
        fx, fy, fw = cfg.get("thumb_face", [1560, 408, 228])
        BW, BY = 820, 560  # janela abaixo do hook
        fc = (f"[0:v]split=2[a][c];"
              f"[a]crop={w}:{h}:{x}:{y},scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},boxblur=40:4,eq=brightness=-0.35:saturation=0.6[bg];"
              f"[c]crop={fw}:{fw}:{fx}:{fy},scale={BW}:{BW}:flags=lanczos,unsharp=7:7:1.0,eq=contrast=1.05[th];"
              f"movie={work}/bigmask.png,format=gray[tm];[th][tm]alphamerge[thr];movie={work}/bigframe.png[tf];"
              f"[bg][tf]overlay={(W - BW) // 2 - 56}:{BY - 56}[v2];[v2][thr]overlay={(W - BW) // 2}:{BY},fps={FPS},setsar=1[v]")
        run(["ffmpeg", "-v", "error", "-y", "-ss", f"{a:.4f}", "-i", src, "-filter_complex", fc, "-map", "[v]",
             "-frames:v", str(nf), "-an", "-c:v", "libx264", "-preset", "veryfast", "-crf", "17", "-pix_fmt", "yuv420p",
             "-threads", "3", out])
    else:
        cx = face_x(a, b)
        cw = int(1080 * 9 / 16 / z) // 2 * 2; chh = int(1080 / z) // 2 * 2
        x0 = int(min(max(cx - cw / 2, 0), 1920 - cw))
        y0 = int(min(max(0, (1080 - chh) * 0.25), 1080 - chh))
        v = f"crop={cw}:{chh}:{x0}:{y0},scale={W}:{H}:flags=lanczos,unsharp=5:5:0.6,fps={FPS},setsar=1"
        run(["ffmpeg", "-v", "error", "-y", "-ss", f"{a:.4f}", "-i", src, "-vf", v, "-frames:v", str(nf), "-an",
             "-c:v", "libx264", "-preset", "veryfast", "-crf", "17", "-pix_fmt", "yuv420p", "-threads", "3", out])
open(f"{work}/parts.txt", "w").write("".join(f"file '{p}'\n" for p in files))
cutv = f"{work}/cut_v.mp4"
run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", f"{work}/parts.txt", "-c", "copy", cutv])

FADE = int(SR * 0.004); pieces = []
for a, b, _ in parts:
    i0 = int(round((a - lo_all) * SR)); n = int(round((b - a) * FPS)) * (SR // FPS)
    p = AUD[i0:i0 + n].astype(np.float32)
    if len(p) < n: p = np.vstack([p, np.zeros((n - len(p), 2), np.float32)])
    ramp = np.linspace(0, 1, FADE, dtype=np.float32)[:, None]
    p[:FADE] *= ramp; p[-FADE:] *= ramp[::-1]; pieces.append(p)
cuta = f"{work}/cut_a.wav"
with wave.open(cuta, "wb") as wo:
    wo.setnchannels(2); wo.setsampwidth(2); wo.setframerate(SR)
    wo.writeframes(np.clip(np.vstack(pieces), -32768, 32767).astype(np.int16).tobytes())

# ---------- legenda CAIXA ALTA com palavra-chave amarela ----------
def ts(t):
    t = max(0, t); return f"{int(t // 3600)}:{int(t % 3600 // 60):02d}:{t % 60:05.2f}"
def clean(txt):
    for k, v in cfg.get("replace", {}).items(): txt = re.sub(k, v, txt, flags=re.I)
    return txt
HL = [h.lower() for h in cfg.get("highlight", [])]
STOP = set("que pra para com uma umas uns por mais muito você vocês isso esse essa aqui então porque quando onde tipo assim gente galera ainda está estão tava também sobre depois antes cara mano como".split())

ow = []  # palavras no tempo de saída
acc = 0.0
for a, b, _ in parts:
    for w in TR:
        m = (w["start"] + w["end"]) / 2
        if a - 0.01 <= m <= b + 0.01:
            ow.append({"w": w["word"].strip(), "s": acc + max(0, w["start"] - a), "e": acc + min(b - a, w["end"] - a)})
    acc += b - a
groups, g = [], []
for w in ow:
    g.append(w); txt = " ".join(x["w"] for x in g)
    if len(g) >= 4 or len(txt) >= 18 or re.search(r"[.,?!]$", w["w"]):
        groups.append(g); g = []
if g: groups.append(g)

def pick(words):
    toks = [re.sub(r"[^\wÀ-ú$%]", "", x).lower() for x in words]
    for i, t in enumerate(toks):
        if any(h == t or (len(h) > 3 and h in t) for h in HL): return i
    for i, t in enumerate(toks):
        if re.search(r"\d", t): return i
    cand = [(len(t), i) for i, t in enumerate(toks) if len(t) >= 5 and t not in STOP]
    return max(cand)[1] if cand else None

def layout_at_out(t):
    acc = 0.0
    for a, b, l in parts:
        if t < acc + (b - a): return l
        acc += b - a
    return parts[-1][2]

ass = [f"""[Script Info]
ScriptType: v4.00+
PlayResX: {W}
PlayResY: {H}
WrapStyle: 0

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Cap,Inter ExtraBold,76,&H00FFFFFF,&H00FFFFFF,&H00000000,&H96000000,-1,0,0,0,100,100,0,0,1,7,3,5,70,70,0,1
Style: Hook,Inter SemiBold,68,&H00FFFFFF,&H00FFFFFF,&H00000000,&H78000000,-1,0,0,0,100,100,0,0,1,5,2,8,90,150,300,1
Style: Sticker,Inter,70,&H00FFFFFF,&H00FFFFFF,&H00B469FF,&H00000000,-1,0,0,0,100,100,0,0,3,22,0,5,60,60,0,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text"""]
pop = r"{\fscx80\fscy80\t(0,80,\fscx106\fscy106)\t(80,150,\fscx100\fscy100)}"
hook = cfg["hook"]
for i, g in enumerate(groups):
    a = g[0]["s"]; b = groups[i + 1][0]["s"] if i + 1 < len(groups) else min(total, g[-1]["e"] + 0.3)
    ws = [clean(x["w"]).rstrip(".,!;:").upper() for x in g]
    ws = [x for x in ws if x]
    for j in range(len(ws) - 1, 0, -1):  # "MEIO -DIA" -> "MEIO-DIA"
        if ws[j].startswith("-"): ws[j - 1] += ws.pop(j)
    if not ws: continue
    k = pick(ws)
    txt = " ".join((r"{\c&H0000D4FF&}" + x + r"{\c&H00FFFFFF&}") if j == k else x for j, x in enumerate(ws))
    y = 1500 if layout_at_out(a) == "S" else 1230
    ass.append(f"Dialogue: 1,{ts(a)},{ts(b)},Cap,,0,0,0,,{{\\pos(540,{y})}}{pop}{txt}")
ass.append(f"Dialogue: 2,{ts(0)},{ts(hook['dur'])},Hook,,0,0,0,,"
           r"{\fad(100,200)\fscx85\fscy85\t(0,180,\fscx103\fscy103)\t(180,280,\fscx100\fscy100)}" + hook["text"].replace("\n", r"\N"))
for st in cfg.get("stickers", []):
    occ = remap_all(st["start"])
    if not occ: continue
    a = occ[-1]; b = a + (st["end"] - st["start"])
    ass.append(f"Dialogue: 3,{ts(a)},{ts(b)},Sticker,,0,0,0,,"
               r"{\pos(540," + str(st.get("y", 900)) + r")\fad(80,150)\fscx40\fscy40\frz-6\t(0,160,\fscx112\fscy112\frz3)\t(160,260,\fscx100\fscy100\frz-2)}"
               + st["text"].replace("\n", r"\N"))
assf = f"{work}/legendas.ass"; open(assf, "w").write("\n".join(ass) + "\n")

# ---------- mix: voz normalizada + trilha baixa ----------
inputs = ["-i", cutv, "-i", cuta]
af = f"[1:a]apad=pad_dur=5,highpass=f=80,loudnorm=I=-14:TP=-1.5:LRA=9,atrim=0:{total:.3f},asetpts=PTS-STARTPTS[voz]"  # apad: o loudnorm come o fim sem folga
if cfg.get("music"):
    inputs += ["-ss", str(cfg.get("music_start", 0)), "-stream_loop", "-1", "-i", cfg["music"]]
    gdb = cfg.get("music_gain_db", -25)
    af += (f";[2:a]atrim=0:{total:.3f},asetpts=PTS-STARTPTS,aresample={SR},volume={gdb}dB,"
           f"afade=t=in:d=0.4,afade=t=out:st={max(0, total - 1.2):.3f}:d=1.2[mus];"
           f"[voz][mus]amix=inputs=2:duration=first:normalize=0,alimiter=limit=0.89[aout]")
else:
    af += ";[voz]anull[aout]"
final = cfg["output"]
run(["ffmpeg", "-v", "error", "-y", *inputs, "-filter_complex", f"[0:v]ass={assf}[vout];{af}",
     "-map", "[vout]", "-map", "[aout]", "-c:v", "libx264", "-preset", "medium", "-crf", "19", "-pix_fmt", "yuv420p",
     "-c:a", "aac", "-b:a", "192k", "-ar", str(SR), "-movflags", "+faststart", "-t", f"{total:.3f}", final])
print(f"OK {final}  duração {total:.1f}s")
