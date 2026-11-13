"""Estilo de edição 4 (tráfego): não mexe no vídeo; melhora a qualidade e coloca
CTA + uma sobreposição perto do fim.

uso: python3 -I trafego.py VIDEO SOBREPOSICAO SAIDA "TEXTO DO CTA" [ANTES_DO_FIM=6] [DURACAO=5]
"""
import json, os, subprocess, sys, tempfile
from PIL import Image, ImageDraw, ImageFilter

video, sob, saida, texto = sys.argv[1:5]
antes = float(sys.argv[5]) if len(sys.argv) > 5 else 6.0
dura = float(sys.argv[6]) if len(sys.argv) > 6 else 5.0

info = json.loads(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                                  "-of", "json", video], capture_output=True, text=True, check=True).stdout)
total = float(info["format"]["duration"])
a = max(0.0, total - antes); b = min(total, a + dura)
work = tempfile.mkdtemp()

# ---- CTA: texto em cima da cabeça, centralizado, dentro da área segura ----
def ts(t): return f"{int(t // 3600)}:{int(t % 3600 // 60):02d}:{t % 60:05.2f}"
linhas = texto.replace("\\n", r"\N")
ass = f"{work}/cta.ass"
open(ass, "w").write(f"""[Script Info]
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920
WrapStyle: 0

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: CTA,Inter SemiBold,58,&H00FFFFFF,&H00FFFFFF,&H00000000,&H78000000,-1,0,0,0,100,100,0,0,1,5,2,8,100,100,250,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
Dialogue: 0,{ts(a)},{ts(b)},CTA,,0,0,0,,{{\\fad(150,150)}}{linhas}
""")

# ---- sobreposição: cartão com borda branca, canto arredondado e sombra ----
MAXW, MAXH, Y = 600, 470, 1110
im = Image.open(sob).convert("RGB"); im.thumbnail((MAXW, MAXH), Image.LANCZOS)
w, h = im.size; r, bd, sh = 30, 8, 36
card = Image.new("RGBA", (w + 2 * (bd + sh), h + 2 * (bd + sh)), (0, 0, 0, 0))
m = Image.new("L", (w + 2 * bd, h + 2 * bd), 0)
ImageDraw.Draw(m).rounded_rectangle([0, 0, w + 2 * bd - 1, h + 2 * bd - 1], r + bd, fill=255)
shadow = Image.new("RGBA", card.size, (0, 0, 0, 0)); shadow.paste((0, 0, 0, 150), (sh, sh + 12), m)
card = Image.alpha_composite(card, shadow.filter(ImageFilter.GaussianBlur(16)))
card.paste((255, 255, 255, 255), (sh, sh), m)
mi = Image.new("L", (w, h), 0); ImageDraw.Draw(mi).rounded_rectangle([0, 0, w - 1, h - 1], r, fill=255)
card.paste(im, (sh + bd, sh + bd), mi)
png = f"{work}/sob.png"; card.save(png)

d = b - a
# qualidade: limpeza leve de ruído, 1080x1920, nitidez e um toque de contraste/cor
fc = (f"[0:v]hqdn3d=1.5:1.5:3:3,scale=1080:1920:flags=lanczos,cas=0.6,"
      f"eq=contrast=1.04:saturation=1.08,setsar=1[v];"
      f"[1:v]format=rgba,fade=in:st=0:d=0.2:alpha=1,fade=out:st={d - 0.2:.3f}:d=0.2:alpha=1,"
      f"setpts=PTS-STARTPTS+{a:.3f}/TB[o];"
      f"[v][o]overlay=x=(W-w)/2:y={Y - sh}:eof_action=pass,ass={ass},format=yuv420p[out]")
subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", video,
                "-loop", "1", "-framerate", "30", "-t", f"{d:.3f}", "-i", png,
                "-filter_complex", fc, "-map", "[out]", "-map", "0:a?",
                "-c:v", "libx264", "-preset", "slow", "-crf", "16", "-c:a", "copy",
                "-movflags", "+faststart", saida], check=True)
print(f"OK {saida} ({total:.1f}s; CTA {a:.1f}s–{b:.1f}s)")
