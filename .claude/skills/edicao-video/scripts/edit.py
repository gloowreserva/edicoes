"""Edição Gloow (estilos 1, 2 e 4): começa na fala, cortes em fala corrida (guiados pelas palavras, sem respiro entre takes), hook, legenda animada (opcional), zoom alternado (opcional), sobreposições em cartão, janela no topo ou tela cheia, selo de comentário.
Uso: python3 -I edit.py config.json
"""
import json, os, re, subprocess, sys
from PIL import Image, ImageDraw, ImageFilter

cfg = json.load(open(sys.argv[1]))
W, H, FPS = 1080, 1920, 30
work = cfg["work"]; os.makedirs(work, exist_ok=True)
src = cfg["video"]

def run(cmd):
    print(">>", " ".join(cmd)[:300], flush=True)
    subprocess.run(cmd, check=True)

# ---------- 1. fala corrida: segmentos a partir das palavras ----------
# Os cortes seguem as palavras da transcrição (não o silêncio): entre um take e outro sobra
# só uma folga mínima (lead/tail), então a emenda soa como fala contínua, sem respiro nem
# "olhada pra baixo". Pausas internas maiores que gap_max também são cortadas.
import numpy as np
SR = 48000
dur = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", src],
                           capture_output=True, text=True).stdout)
wav = f"{work}/audio_src.wav"
run(["ffmpeg", "-v", "error", "-y", "-i", src, "-vn", "-ac", "2", "-ar", str(SR), "-c:a", "pcm_s16le", wav])
import wave as _wave
with _wave.open(wav) as _wf:
    AUD = np.frombuffer(_wf.readframes(_wf.getnframes()), np.int16).reshape(-1, 2)
_mono = AUD.astype(np.float32).mean(axis=1) / 32768
HOP = SR // 100  # janelas de 10 ms
_n = len(_mono) // HOP
ENV = 20 * np.log10(np.sqrt((_mono[:_n * HOP].reshape(_n, HOP) ** 2).mean(axis=1)) + 1e-9)
THR = cfg.get("speech_db", max(-48.0, float(np.percentile(ENV, 95)) - 28))  # nível que conta como "voz"

def loud(t):
    i = int(t * 100)
    return 0 <= i < _n and ENV[i] > THR

removes = [tuple(x) for x in cfg.get("remove", [])]
def in_remove(t): return any(a <= t <= b for a, b in removes)
def remove_between(t0, t1): return any(a < t1 and b > t0 for a, b in removes)

gap_max = cfg.get("gap_max", 0.25)   # pausa máxima mantida dentro de uma frase
lead = cfg.get("lead", 0.03)         # folga antes da 1ª palavra do take
tail = cfg.get("tail", 0.06)         # folga depois da última palavra do take
words_all = [(w["start"], w["end"]) for seg in json.load(open(cfg["transcript"])) for w in seg["words"]]
words_all = [(a, b) for a, b in words_all if not in_remove((a + b) / 2)]
blocks = []
for a, b in words_all:
    if blocks and a - blocks[-1][1] <= gap_max and not remove_between(blocks[-1][1], a):
        blocks[-1][1] = max(blocks[-1][1], b)
    else:
        blocks.append([a, b])

segs = []
for i, (a, b) in enumerate(blocks):
    # ajusta a borda pelo áudio real (o Whisper costuma errar o fim/início da palavra por alguns ms)
    lo = max([0.0] + [rb for ra, rb in removes if rb <= a + 0.05] + ([blocks[i - 1][1]] if i else []))
    hi = min([dur] + [ra for ra, rb in removes if ra >= b - 0.05] + ([blocks[i + 1][0]] if i + 1 < len(blocks) else []))
    s0 = a
    while s0 - 0.01 > max(lo, a - 0.15) and loud(s0 - 0.01): s0 -= 0.01
    e0 = b
    while e0 + 0.01 < min(hi, b + 0.20) and loud(e0): e0 += 0.01
    s0, e0 = max(lo, s0 - lead), min(hi, e0 + tail)
    if segs and s0 - segs[-1][1] < 0.02: segs[-1] = (segs[-1][0], e0)
    else: segs.append((s0, e0))
# alinha tudo ao quadro, pra áudio e vídeo terem exatamente a mesma duração
segs = [(round(a * FPS) / FPS, round(b * FPS) / FPS) for a, b in segs]
segs = [(a, b) for a, b in segs if b - a >= 3 / FPS]
print("segmentos:", [(round(a, 2), round(b, 2)) for a, b in segs])

def remap(t):
    acc = 0.0
    for a, b in segs:
        if t < a: return acc
        if t <= b: return acc + (t - a)
        acc += b - a
    return acc
total = sum(b - a for a, b in segs)

# ---------- 2. cortes + zoom alternado (vídeo trecho por trecho; áudio montado de uma vez) ----------
z = cfg.get("zoom", 1.10)
# estilo 4: "zoom_at" = trechos [ini, fim] (tempo do original) com zoom só nas falas importantes.
# Os trechos de vídeo são divididos nas bordas desses intervalos (o áudio não muda).
zoom_at = [tuple(x) for x in cfg.get("zoom_at", [])]
vsegs = []
for a, b in segs:
    cuts = sorted({a, b, *[t for r in zoom_at for t in r if a < t < b]})
    cuts = [round(t * FPS) / FPS for t in cuts]
    for x, y in zip(cuts, cuts[1:]):
        if y - x >= 1 / FPS: vsegs.append((x, y, any(r0 <= (x + y) / 2 <= r1 for r0, r1 in zoom_at)))
if not zoom_at: vsegs = [(a, b, i % 2 == 1) for i, (a, b) in enumerate(segs)]
parts = []
for i, (a, b, zoomed) in enumerate(vsegs):
    v = f"scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H}"
    if zoomed and z > 1.001:
        zw, zh = int(W * z) // 2 * 2, int(H * z) // 2 * 2
        v += f",scale={zw}:{zh},crop={W}:{H}:{(zw-W)//2}:{int((zh-H)*0.35)}"
    v += f",fps={FPS},setsar=1"
    nf = round((b - a) * FPS)
    part = f"{work}/part{i:03d}.mp4"
    run(["ffmpeg", "-v", "error", "-y", "-ss", f"{a:.4f}", "-i", src, "-vf", v, "-frames:v", str(nf), "-an",
         "-c:v", "libx264", "-preset", "veryfast", "-crf", "16", "-pix_fmt", "yuv420p", "-threads", "2", part])
    parts.append(part)
lst = f"{work}/parts.txt"
open(lst, "w").write("".join(f"file '{p}'\n" for p in parts))
cutv = f"{work}/cut_v.mp4"
run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", lst, "-c", "copy", cutv])
# áudio: junta as amostras exatas de cada trecho, com micro-fade de 4 ms em cada emenda (sem estalo, sem vão)
FADE = int(SR * 0.004)
pieces = []
for a, b in segs:
    i0 = int(round(a * SR)); n = int(round((b - a) * FPS)) * (SR // FPS)
    p = AUD[i0:i0 + n].astype(np.float32)
    if len(p) < n: p = np.vstack([p, np.zeros((n - len(p), 2), np.float32)])
    ramp = np.linspace(0, 1, FADE, dtype=np.float32)[:, None]
    p[:FADE] *= ramp; p[-FADE:] *= ramp[::-1]
    pieces.append(p)
cuta = f"{work}/cut_a.wav"
with _wave.open(cuta, "wb") as _wo:
    _wo.setnchannels(2); _wo.setsampwidth(2); _wo.setframerate(SR)
    _wo.writeframes(np.clip(np.vstack(pieces), -32768, 32767).astype(np.int16).tobytes())
cut = f"{work}/cut.mp4"
run(["ffmpeg", "-v", "error", "-y", "-i", cutv, "-i", cuta, "-map", "0:v", "-map", "1:a", "-c:v", "copy",
     "-c:a", "aac", "-b:a", "192k", "-shortest", cut])

# ---------- 3. legendas (ASS) ----------
def ts(t):
    t = max(0, t); h = int(t // 3600); m = int(t % 3600 // 60); s = t % 60
    return f"{h}:{m:02d}:{s:05.2f}"

def clean(txt):
    for k, v in cfg.get("replace", {}).items():
        txt = re.sub(k, v, txt, flags=re.I)
    return txt

words = [{"w": w["word"], "s": w["start"], "e": w["end"]} for s in json.load(open(cfg["transcript"])) for w in s["words"]]
def kept(t): return any(a - 0.02 <= t <= b + 0.02 for a, b in segs)
words = [w for w in words if kept((w["s"] + w["e"]) / 2)]
groups, g = [], []
for w in words:
    g.append(w)
    txt = " ".join(x["w"].strip() for x in g)
    if len(g) >= 3 or len(txt) >= 14 or re.search(r"[.,?!]$", w["w"].strip()):
        groups.append(g); g = []
if g: groups.append(g)

ass = [f"""[Script Info]
ScriptType: v4.00+
PlayResX: {W}
PlayResY: {H}
WrapStyle: 0

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Cap,Inter,80,&H00FFFFFF,&H00FFFFFF,&H00000000,&H64000000,-1,0,0,0,100,100,0,0,1,6,2,2,60,60,560,1
Style: Hook,Inter SemiBold,68,&H00FFFFFF,&H00FFFFFF,&H00000000,&H78000000,-1,0,0,0,100,100,0,0,1,5,2,8,90,90,300,1
Style: HookBox,Inter,64,&H00000000,&H00000000,&H00FFFFFF,&H00FFFFFF,-1,0,0,0,100,100,0,0,3,18,0,8,110,110,300,1
Style: Sticker,Inter,70,&H00FFFFFF,&H00FFFFFF,&H00B469FF,&H00000000,-1,0,0,0,100,100,0,0,3,22,0,5,60,60,0,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text"""]
pop = r"{\fscx72\fscy72\t(0,90,\fscx108\fscy108)\t(90,170,\fscx100\fscy100)}"
for i, g in enumerate(groups if cfg.get("captions", True) else []):
    a = remap(g[0]["s"]); b = remap(groups[i + 1][0]["s"]) if i + 1 < len(groups) else remap(g[-1]["e"]) + 0.3
    txt = clean(" ".join(x["w"].strip() for x in g)).rstrip(".,!")
    ass.append(f"Dialogue: 1,{ts(a)},{ts(b)},Cap,,0,0,0,,{pop}{txt}")

hook = cfg["hook"]
ass.append(f"Dialogue: 2,{ts(0)},{ts(hook['dur'])},{'HookBox' if hook.get('style') == 'box' else 'Hook'},,0,0,0,,"
           r"{\fad(120,200)\fscx85\fscy85\t(0,180,\fscx103\fscy103)\t(180,280,\fscx100\fscy100)}" + hook["text"].replace("\n", r"\N"))
for st in cfg.get("stickers", []):
    a, b = remap(st["start"]), remap(st["end"])
    ass.append(f"Dialogue: 3,{ts(a)},{ts(b)},Sticker,,0,0,0,,"
               r"{\pos(540," + str(st.get("y", 760)) + r")\fad(80,150)\fscx40\fscy40\frz-6\t(0,160,\fscx112\fscy112\frz3)\t(160,260,\fscx100\fscy100\frz-2)}"
               + st["text"].replace("\n", r"\N"))
assf = f"{work}/legendas.ass"
open(assf, "w").write("\n".join(ass) + "\n")

# ---------- 4. cards (imagens) ----------
def make_card(path, out, maxw, maxh, tilt):
    im = Image.open(path).convert("RGB")
    im.thumbnail((maxw, maxh), Image.LANCZOS)
    w, h = im.size; r = 34; bd = 8
    card = Image.new("RGBA", (w + 2 * bd, h + 2 * bd), (0, 0, 0, 0))
    m = Image.new("L", card.size, 0); ImageDraw.Draw(m).rounded_rectangle([0, 0, *card.size], r + bd, fill=255)
    card.paste((255, 255, 255, 255), (0, 0), m)
    m2 = Image.new("L", im.size, 0); ImageDraw.Draw(m2).rounded_rectangle([0, 0, *im.size], r, fill=255)
    card.paste(im, (bd, bd), m2)
    sh = 40
    canvas = Image.new("RGBA", (card.width + 2 * sh, card.height + 2 * sh), (0, 0, 0, 0))
    shadow = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    shadow.paste((0, 0, 0, 140), (sh, sh + 14), card.split()[3])
    canvas = Image.alpha_composite(canvas, shadow.filter(ImageFilter.GaussianBlur(18)))
    canvas.alpha_composite(card, (sh, sh))
    canvas = canvas.rotate(tilt, Image.BICUBIC, expand=True)
    canvas.save(out)
    return canvas.size

inputs, fc, last = ["-i", cut], [], "[0:v]"
idx = 1
for k, ov in enumerate(cfg.get("overlays", [])):
    a, b = remap(ov["start"]), remap(ov["end"]); d = b - a
    tag = f"[o{k}]"
    if ov["type"] == "card":
        png = f"{work}/card{k}.png"
        cw, ch = make_card(ov["file"], png, ov.get("maxw", 640), ov.get("maxh", 1150), ov.get("tilt", -3))
        inputs += ["-loop", "1", "-framerate", str(FPS), "-t", f"{d:.3f}", "-i", png]
        fc.append(f"[{idx}:v]format=rgba,fade=in:st=0:d=0.18:alpha=1,fade=out:st={d-0.2:.3f}:d=0.2:alpha=1,"
                  f"setpts=PTS-STARTPTS+{a:.3f}/TB{tag}")
        y0 = ov.get("y", 170)
        p = f"clip((t-{a:.3f})/0.32,0,1)"
        yexpr = f"{y0}+160*(1-(1+2.70158*pow({p}-1,3)+1.70158*pow({p}-1,2)))"
        fc.append(f"{last}{tag}overlay=x=(W-w)/2:y='{yexpr}':eval=frame:eof_action=pass[b{k}]")
    elif ov["type"] == "pip":  # estilo 2: janela no topo, perto da cabeça
        pw, ph = ov.get("size", [600, 600]); py = ov.get("y", 230); bd, r, sh = 8, 30, 36
        cx, cy, cw, chh = ov.get("crop", [0, 0, 1, 1])
        frame = Image.new("RGBA", (pw + 2 * (bd + sh), ph + 2 * (bd + sh)), (0, 0, 0, 0))
        m = Image.new("L", (pw + 2 * bd, ph + 2 * bd), 0)
        ImageDraw.Draw(m).rounded_rectangle([0, 0, pw + 2 * bd - 1, ph + 2 * bd - 1], r + bd, fill=255)
        shadow = Image.new("RGBA", frame.size, (0, 0, 0, 0)); shadow.paste((0, 0, 0, 150), (sh, sh + 12), m)
        frame = Image.alpha_composite(frame, shadow.filter(ImageFilter.GaussianBlur(16)))
        frame.paste((255, 255, 255, 255), (sh, sh), m)
        mask = Image.new("L", (pw, ph), 0); ImageDraw.Draw(mask).rounded_rectangle([0, 0, pw - 1, ph - 1], r, fill=255)
        maskf = f"{work}/pipmask{k}.png"; mask.save(maskf)
        if ov["file"].lower().endswith((".mp4", ".mov")):
            inputs += ["-ss", str(ov.get("from", 0)), "-t", f"{d:.3f}", "-i", ov["file"]]
            src_v = f"[{idx}:v]crop=iw*{cw}:ih*{chh}:iw*{cx}:ih*{cy},scale={pw}:{ph}:force_original_aspect_ratio=increase,crop={pw}:{ph},fps={FPS},format=rgba"
        else:
            im = Image.open(ov["file"]).convert("RGB"); W0, H0 = im.size
            im = im.crop((int(W0 * cx), int(H0 * cy), int(W0 * (cx + cw)), int(H0 * (cy + chh))))
            sc = max(pw / im.width, ph / im.height)
            im = im.resize((max(pw, round(im.width * sc)), max(ph, round(im.height * sc))), Image.LANCZOS)
            l, t = (im.width - pw) // 2, 0 if ov.get("align_top", True) else (im.height - ph) // 2
            imf = f"{work}/pipimg{k}.png"; im.crop((l, t, l + pw, t + ph)).save(imf)
            inputs += ["-loop", "1", "-framerate", str(FPS), "-t", f"{d:.3f}", "-i", imf]
            src_v = f"[{idx}:v]format=rgba"
        idx += 1
        framef = f"{work}/pipframe{k}.png"; frame.save(framef)
        inputs += ["-loop", "1", "-framerate", str(FPS), "-t", f"{d:.3f}", "-i", maskf]; mi = idx; idx += 1
        inputs += ["-loop", "1", "-framerate", str(FPS), "-t", f"{d:.3f}", "-i", framef]; fi = idx
        fade = f"fade=in:st=0:d=0.2:alpha=1,fade=out:st={d-0.2:.3f}:d=0.2:alpha=1,setpts=PTS-STARTPTS+{a:.3f}/TB"
        fc.append(f"{src_v}[pv{k}];[{mi}:v]format=gray[pm{k}];[pv{k}][pm{k}]alphamerge,{fade}[pc{k}]")
        fc.append(f"[{fi}:v]format=rgba,{fade}[pf{k}]")
        p = f"clip((t-{a:.3f})/0.3,0,1)"
        yo = f"(-50*(1-(1+2.70158*pow({p}-1,3)+1.70158*pow({p}-1,2))))"
        px = ov.get("x"); fx = "(W-w)/2" if px is None else str(px - bd - sh); vx = "(W-w)/2" if px is None else str(px)
        fc.append(f"{last}[pf{k}]overlay=x={fx}:y='{py - bd - sh}+{yo}':eval=frame:eof_action=pass[pb{k}]")
        fc.append(f"[pb{k}][pc{k}]overlay=x={vx}:y='{py}+{yo}':eval=frame:eof_action=pass[b{k}]")
    else:  # vídeo em tela cheia
        inputs += ["-ss", str(ov.get("from", 0)), "-t", f"{d:.3f}", "-i", ov["file"]]
        fc.append(f"[{idx}:v]scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},fps={FPS},"
                  f"format=rgba,fade=in:st=0:d=0.15:alpha=1,fade=out:st={d-0.15:.3f}:d=0.15:alpha=1,"
                  f"setpts=PTS-STARTPTS+{a:.3f}/TB{tag}")
        fc.append(f"{last}{tag}overlay=0:0:eof_action=pass[b{k}]")
    last = f"[b{k}]"; idx += 1
fc.append(f"{last}ass={assf}[vout]")
final = cfg["output"]
run(["ffmpeg", "-v", "error", "-y", *inputs, "-filter_complex", ";".join(fc), "-map", "[vout]", "-map", "0:a",
     "-c:v", "libx264", "-preset", "medium", "-crf", "20", "-pix_fmt", "yuv420p", "-c:a", "copy",
     "-movflags", "+faststart", "-t", f"{total:.3f}", final])
print(f"OK {final}  duração {total:.1f}s (original {dur:.1f}s)")
