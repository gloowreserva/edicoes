"""Estilo 4C (UGC sem fala): monta cenas escolhidas do bruto, texto estilo TikTok "clássico"
(caixa branca arredondada por linha, letra preta, com emoji) e música do início ao fim.
Uso: python3 -I estilo4c.py config.json

config: {"video", "work", "output", "music", "music_start", "grade": true,
         "shots": [{"from": s, "to": s, "text": "...", "y": centro_vertical_px}]}
Cenas seguidas com o mesmo texto mantêm o texto parado (sem piscar).
"""
import json, os, subprocess, sys
from PIL import Image, ImageDraw, ImageFont

cfg = json.load(open(sys.argv[1]))
W, H, FPS = 1080, 1920, 30
work = cfg["work"]; os.makedirs(work, exist_ok=True)
FONT = ImageFont.truetype("/usr/share/fonts/opentype/inter/Inter-SemiBold.otf", cfg.get("font_size", 50))
EMOJI = ImageFont.truetype("/usr/share/fonts/truetype/noto/NotoColorEmoji.ttf", 109)

def run(cmd):
    print(">>", " ".join(cmd)[:200], flush=True); subprocess.run(cmd, check=True)

def is_emoji(ch):
    o = ord(ch)
    return o >= 0x1F000 or 0x2600 <= o <= 0x27BF or o in (0xFE0F, 0x200D)

def runs(line):  # quebra a linha em trechos texto/emoji
    out = []
    for ch in line:
        e = is_emoji(ch)
        if out and out[-1][0] == e: out[-1][1] += ch
        else: out.append([e, ch])
    return out

def emoji_img(seq, size):
    seq = seq.replace("️", "")
    if not seq.strip(): return None
    im = Image.new("RGBA", (160 * len(seq), 160), (0, 0, 0, 0))
    ImageDraw.Draw(im).text((0, 0), seq, font=EMOJI, embedded_color=True)
    im = im.crop(im.getbbox())
    return im.resize((round(im.width * size / im.height), size), Image.LANCZOS)

def line_img(line):
    fs = FONT.size; parts = []
    for e, s in runs(line):
        if e:
            em = emoji_img(s, int(fs * 0.95))
            if em: parts.append(("img", em))
        else:
            parts.append(("txt", s))
    asc, desc = FONT.getmetrics(); h = asc + desc
    width = sum(FONT.getlength(p[1]) if p[0] == "txt" else p[1].width + 4 for p in parts)
    padx, pady = 22, 10
    im = Image.new("RGBA", (int(width) + 2 * padx, h + 2 * pady), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle([0, 0, im.width - 1, im.height - 1], 16, fill=(255, 255, 255, 255))
    x = padx
    for kind, p in parts:
        if kind == "txt":
            d.text((x, pady), p, font=FONT, fill=(0, 0, 0, 255)); x += FONT.getlength(p)
        else:
            im.alpha_composite(p, (int(x) + 2, pady + (h - p.height) // 2 + 2)); x += p.width + 4
    return im

def text_png(text, yc, out):
    lines = [line_img(l) for l in text.split("\n")]
    canvas = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    gap = -2  # caixas encostadas, como no TikTok
    total = sum(l.height for l in lines) + gap * (len(lines) - 1)
    y = yc - total // 2
    for l in lines:
        canvas.alpha_composite(l, ((W - l.width) // 2, y)); y += l.height + gap
    canvas.save(out)

# 1. cortes
grade = ",eq=contrast=1.04:saturation=1.12" if cfg.get("grade", True) else ""
parts = []
for i, s in enumerate(cfg["shots"]):
    p = f"{work}/shot{i:02d}.mp4"
    run(["ffmpeg", "-v", "error", "-y", "-ss", str(s["from"]), "-i", cfg["video"], "-t", f"{s['to'] - s['from']:.3f}",
         "-vf", f"scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},fps={FPS},setsar=1{grade}",
         "-an", "-c:v", "libx264", "-preset", "veryfast", "-crf", "15", p])
    parts.append(p)
open(f"{work}/list.txt", "w").write("".join(f"file '{p}'\n" for p in parts))
cut = f"{work}/cut.mp4"
run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", f"{work}/list.txt", "-c", "copy", cut])
durs = [float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", p],
        capture_output=True, text=True).stdout) for p in parts]
total = sum(durs)

# 2. blocos de texto (junta cenas seguidas com o mesmo texto)
blocks, t = [], 0.0
for s, d in zip(cfg["shots"], durs):
    if blocks and blocks[-1]["text"] == s["text"] and blocks[-1]["y"] == s.get("y", 1080): blocks[-1]["end"] = t + d
    else: blocks.append({"text": s["text"], "y": s.get("y", 1080), "start": t, "end": t + d})
    t += d
inputs, fc, last = ["-i", cut], [], "[0:v]"
for k, b in enumerate(blocks):
    png = f"{work}/txt{k:02d}.png"; text_png(b["text"], b["y"], png)
    inputs += ["-loop", "1", "-framerate", str(FPS), "-i", png]
    en = f"between(t,{b['start']:.3f},{b['end'] - 0.001:.3f})"
    fc.append(f"{last}[{k + 1}:v]overlay=0:0:enable='{en}':shortest=1[v{k}]"); last = f"[v{k}]"

# 3. sobreposições: imagem em cartão (borda branca, canto arredondado, sombra) no topo, ao lado da cabeça.
#    {"shot": i, "files": [img, ...], "x", "y", "w", "from": seg_na_cena, "dur": seg}. Várias imagens = sequência.
def card(path, w, out):
    import pillow_heif; pillow_heif.register_heif_opener()
    im = Image.open(path).convert("RGB"); im = im.resize((w, round(im.height * w / im.width)), Image.LANCZOS)
    bd, r, sh = 7, 20, 30
    c = Image.new("RGBA", (im.width + 2 * (bd + sh), im.height + 2 * (bd + sh)), (0, 0, 0, 0))
    m = Image.new("L", (im.width + 2 * bd, im.height + 2 * bd), 0)
    ImageDraw.Draw(m).rounded_rectangle([0, 0, m.width - 1, m.height - 1], r + bd, fill=255)
    from PIL import ImageFilter
    shadow = Image.new("RGBA", c.size, (0, 0, 0, 0)); shadow.paste((0, 0, 0, 120), (sh, sh + 10), m)
    c = Image.alpha_composite(c, shadow.filter(ImageFilter.GaussianBlur(14)))
    c.paste((255, 255, 255, 255), (sh, sh), m)
    mi_ = Image.new("L", im.size, 0); ImageDraw.Draw(mi_).rounded_rectangle([0, 0, im.width - 1, im.height - 1], r, fill=255)
    c.paste(im, (sh + bd, sh + bd), mi_)
    c.save(out); return sh + bd

starts = [sum(durs[:i]) for i in range(len(durs))]
n = len(blocks) + 1
for k, ov in enumerate(cfg.get("overlays", [])):
    a = starts[ov["shot"]] + ov.get("from", 0.0)
    b = min(a + ov.get("dur", durs[ov["shot"]] - ov.get("from", 0.0)), total)
    files = ov.get("files") or [ov["file"]]; step = (b - a) / len(files)
    for j, f in enumerate(files):
        png = f"{work}/ov{k:02d}_{j}.png"; off = card(f, ov.get("w", 420), png)
        s, e = a + j * step, a + (j + 1) * step
        inputs += ["-loop", "1", "-framerate", str(FPS), "-t", f"{total:.3f}", "-i", png]
        fi = "" if j else f",fade=in:st={s:.3f}:d=0.15:alpha=1"
        fc.append(f"[{n}:v]format=rgba{fi}[ovi{k}_{j}]")
        fc.append(f"{last}[ovi{k}_{j}]overlay={ov['x'] - off}:{ov['y'] - off}:enable='between(t,{s:.3f},{e - 0.001:.3f})'[vo{k}_{j}]")
        last = f"[vo{k}_{j}]"; n += 1

# 4. música do primeiro ao último segundo
mi = n
inputs += ["-ss", str(cfg.get("music_start", 0)), "-i", cfg["music"]]
fc.append(f"[{mi}:a]atrim=0:{total:.3f},asetpts=PTS-STARTPTS,afade=t=out:st={total - 0.6:.3f}:d=0.6,"
          f"loudnorm=I=-14:TP=-1.5:LRA=11[aout]")
run(["ffmpeg", "-v", "error", "-y", *inputs, "-filter_complex", ";".join(fc), "-map", last, "-map", "[aout]",
     "-c:v", "libx264", "-preset", "medium", "-crf", "19", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k",
     "-ar", "48000", "-movflags", "+faststart", "-t", f"{total:.3f}", cfg["output"]])
print(f"OK {cfg['output']}  {total:.1f}s, {len(cfg['shots'])} cenas, {len(blocks)} textos")
