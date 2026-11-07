"""Edição Gloow: corta respiros, zoom alternado nos cortes, hook, legenda animada, sobreposições.
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

# ---------- 1. silêncios -> segmentos mantidos ----------
out = subprocess.run(["ffmpeg", "-nostats", "-i", src, "-vn", "-af",
                      f"silencedetect=n={cfg.get('silence_db', -32)}dB:d={cfg.get('silence_min', 0.18)}",
                      "-f", "null", "-"], capture_output=True, text=True).stderr
dur = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", src],
                           capture_output=True, text=True).stdout)
starts = [float(x) for x in re.findall(r"silence_start: ([\d.]+)", out)]
ends = [float(x) for x in re.findall(r"silence_end: ([\d.]+)", out)]
pad = cfg.get("pad", 0.07)
sil = list(zip(starts, ends + [dur] * (len(starts) - len(ends)))) + [tuple(x) for x in cfg.get("remove", [])]
# regra: o vídeo sempre começa na primeira palavra falada
_first = min(w["start"] for seg in json.load(open(cfg["transcript"])) for w in seg["words"])
if _first > 0.15:
    sil.append((0.0, _first - 0.08 + pad))
sil.sort()
merged = []
for a, b in sil:
    if merged and a <= merged[-1][1]: merged[-1] = (merged[-1][0], max(merged[-1][1], b))
    else: merged.append((a, b))
sil = merged
segs, cur = [], 0.0
for s, e in sil:
    if s - cur > 0.05:
        segs.append((max(0, cur), min(dur, s + pad)))
    cur = e - pad
if dur - cur > 0.1:
    segs.append((cur, dur))
segs = [(a, b) for a, b in segs if b - a > 0.12]
print("segmentos:", [(round(a, 2), round(b, 2)) for a, b in segs])

def remap(t):
    acc = 0.0
    for a, b in segs:
        if t < a: return acc
        if t <= b: return acc + (t - a)
        acc += b - a
    return acc
total = sum(b - a for a, b in segs)

# ---------- 2. cortes + zoom alternado (trecho por trecho, pra não estourar memória) ----------
z = cfg.get("zoom", 1.10)
parts = []
for i, (a, b) in enumerate(segs):
    v = f"scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H}"
    if i % 2 == 1:
        zw, zh = int(W * z) // 2 * 2, int(H * z) // 2 * 2
        v += f",scale={zw}:{zh},crop={W}:{H}:{(zw-W)//2}:{int((zh-H)*0.35)}"
    v += f",fps={FPS},setsar=1"
    d = b - a
    part = f"{work}/part{i:03d}.mp4"
    run(["ffmpeg", "-v", "error", "-y", "-ss", f"{a:.3f}", "-i", src, "-t", f"{d:.3f}", "-vf", v,
         "-af", f"afade=t=in:d=0.015,afade=t=out:st={max(0,d-0.015):.3f}:d=0.015",
         "-map", "0:v:0", "-map", "0:a:0", "-c:v", "libx264", "-preset", "veryfast", "-crf", "16",
         "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-threads", "2", part])
    parts.append(part)
lst = f"{work}/parts.txt"
open(lst, "w").write("".join(f"file '{p}'\n" for p in parts))
cut = f"{work}/cut.mp4"
run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", lst, "-c", "copy", cut])
# duração real de cada trecho (ajusta o remap ao que foi codificado)
real = [float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", p],
        capture_output=True, text=True).stdout) for p in parts]

# ---------- 3. legendas (ASS) ----------
def ts(t):
    t = max(0, t); h = int(t // 3600); m = int(t % 3600 // 60); s = t % 60
    return f"{h}:{m:02d}:{s:05.2f}"

def clean(txt):
    for k, v in cfg.get("replace", {}).items():
        txt = re.sub(k, v, txt, flags=re.I)
    return txt

words = [{"w": w["word"], "s": w["start"], "e": w["end"]} for s in json.load(open(cfg["transcript"])) for w in s["words"]]
def kept(t): return any(a - 0.05 <= t <= b + 0.05 for a, b in segs)
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
Style: Sticker,Inter,70,&H00FFFFFF,&H00FFFFFF,&H00B469FF,&H00000000,-1,0,0,0,100,100,0,0,3,22,0,5,60,60,0,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text"""]
pop = r"{\fscx72\fscy72\t(0,90,\fscx108\fscy108)\t(90,170,\fscx100\fscy100)}"
for i, g in enumerate(groups):
    a = remap(g[0]["s"]); b = remap(groups[i + 1][0]["s"]) if i + 1 < len(groups) else remap(g[-1]["e"]) + 0.3
    txt = clean(" ".join(x["w"].strip() for x in g)).rstrip(".,!")
    ass.append(f"Dialogue: 1,{ts(a)},{ts(b)},Cap,,0,0,0,,{pop}{txt}")

hook = cfg["hook"]
ass.append(f"Dialogue: 2,{ts(0)},{ts(hook['dur'])},Hook,,0,0,0,,"
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
