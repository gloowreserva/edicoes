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

# ---------- 1. trechos: tomadas escolhidas, sem respiro ----------
words = [w for s in json.load(open(cfg["transcript"])) for w in s["words"]]
gap = cfg.get("gap", 0.28); pad = 0.07
segs = []
for a, b in cfg["keep"]:
    ws = [w for w in words if w["start"] >= a - 0.05 and w["end"] <= b + 0.05]
    if not ws: continue
    cur = [max(a, ws[0]["start"] - pad), ws[0]["end"]]
    for w in ws[1:]:
        if w["start"] - cur[1] > gap:
            segs.append((cur[0], min(cur[1] + pad, w["start"] - 0.02))); cur = [w["start"] - pad, w["end"]]
        else: cur[1] = w["end"]
    segs.append((cur[0], min(cur[1] + pad + 0.05, b)))
segs = [(round(a, 3), round(b, 3)) for a, b in segs if b - a > 0.1]

parts = []
for i, (a, b) in enumerate(segs):
    p = f"{work}/p{i:03d}.mp4"
    run(["ffmpeg", "-v", "error", "-y", "-ss", f"{a:.3f}", "-i", cfg["video"], "-t", f"{b - a:.3f}",
         "-vf", f"scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},fps={FPS},setsar=1{TAG}",
         "-af", f"afade=t=in:d=0.012,afade=t=out:st={max(0, b - a - 0.012):.3f}:d=0.012",
         "-c:v", "libx264", "-preset", "veryfast", "-crf", "15", *ENC, "-c:a", "pcm_s16le", "-ar", "48000", p.replace(".mp4", ".mov")])
    parts.append(p.replace(".mp4", ".mov"))
open(f"{work}/list.txt", "w").write("".join(f"file '{p}'\n" for p in parts))
cut = f"{work}/cut.mov"
run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", f"{work}/list.txt", "-c", "copy", cut])
real = [float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", p],
        capture_output=True, text=True).stdout) for p in parts]
total = sum(real)

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
        ass.append(f"Dialogue: 2,{ts(remap(sp['at']))},{ts(remap(sp['until']))},Pct,,0,0,0,," + r"{\pos(70," + str(cfg.get("split_h", 640) // 2) + r")}" + sp["label"])
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
        a, b = remap(sp["at"]), remap(sp["until"])
        inputs += ["-loop", "1", "-framerate", str(FPS), "-t", f"{total:.3f}", "-i", sp["file"]]
        fc.append(f"[{n}:v]scale={W}:{th}:force_original_aspect_ratio=increase,crop={W}:{th},setsar=1,format=rgba,"
                  f"scale=out_color_matrix=bt709:out_range=tv,format=yuv420p[top{i}];[top{i}][bot{i}]vstack[sp{i}]")
        fc.append(f"{last}[sp{i}]overlay=0:0:enable='between(t,{a:.3f},{b - 0.001:.3f})'[sv{i}]"); last = f"[sv{i}]"; n += 1
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
    fc.append(f"[0:a]loudnorm=I=-14:TP=-1.5:LRA=11[voz];[{n}:a]atrim=0:{total:.3f},asetpts=PTS-STARTPTS,"
              f"volume={cfg.get('music_db', -24)}dB,afade=t=out:st={total - 0.8:.3f}:d=0.8[mus];"
              f"[voz][mus]amix=inputs=2:duration=first:normalize=0[aout]")
else:
    fc.append("[0:a]loudnorm=I=-14:TP=-1.5:LRA=11[aout]")
run(["ffmpeg", "-v", "error", "-y", *inputs, "-filter_complex", ";".join(fc), "-map", "[vout]", "-map", "[aout]",
     "-c:v", "libx264", "-preset", "medium", "-crf", "19", "-pix_fmt", "yuv420p", *ENC, "-c:a", "aac", "-b:a", "192k",
     "-ar", "48000", "-movflags", "+faststart", "-t", f"{total:.3f}", cfg["output"]])
print(f"OK {cfg['output']}  {total:.1f}s, {len(segs)} trechos")
