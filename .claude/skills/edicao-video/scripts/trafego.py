"""Estilo de edição 4 (tráfego): não mexe no vídeo; melhora a qualidade e coloca
CTA + uma sobreposição perto do fim.

uso: python3 -I trafego.py VIDEO SOBREPOSICAO SAIDA "TEXTO DO CTA" [ANTES_DO_FIM=6] [DURACAO=5] [opções]
  --sem-qualidade : não refaz a melhora de qualidade (vídeo já passou pelo cta_video.py)
  --seta          : seta para baixo pulando, abaixo da sobreposição (botão "Saiba mais" do anúncio)
  --y N --maxh N --maxw N : posição/tamanho do cartão da sobreposição (padrão 1110, 470, 600)
"""
import json, os, subprocess, sys, tempfile
from PIL import Image, ImageDraw, ImageFilter

argv = sys.argv[1:]
def opt(nome, padrao):
    if nome in argv:
        i = argv.index(nome); v = argv[i + 1]; del argv[i:i + 2]; return int(v)
    return padrao
def flag(nome):
    if nome in argv: argv.remove(nome); return True
    return False
qualidade, seta = not flag("--sem-qualidade"), flag("--seta")
Y, MAXH, MAXW = opt("--y", 1110), opt("--maxh", 470), opt("--maxw", 600)
video, sob, saida, texto = argv[:4]
antes = float(argv[4]) if len(argv) > 4 else 6.0
dura = float(argv[5]) if len(argv) > 5 else 5.0

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
extra_in, extra_fc, fim_card = [], "", Y - sh + card.height - sh
if seta:  # seta branca com contorno preto, pulando para baixo
    S = 150; ar = Image.new("RGBA", (S + 40, S + 60), (0, 0, 0, 0)); dr = ImageDraw.Draw(ar)
    pts = [(20 + S * .32, 20), (20 + S * .68, 20), (20 + S * .68, 20 + S * .5), (20 + S * .95, 20 + S * .5),
           (20 + S / 2, 20 + S), (20 + S * .05, 20 + S * .5), (20 + S * .32, 20 + S * .5)]
    dr.polygon(pts, fill=(255, 255, 255, 255), outline=(0, 0, 0, 255), width=9)
    sombra = Image.new("RGBA", ar.size, (0, 0, 0, 0)); sombra.paste((0, 0, 0, 120), (0, 8), ar.split()[3])
    ar = Image.alpha_composite(sombra.filter(ImageFilter.GaussianBlur(8)), ar)
    arpng = f"{work}/seta.png"; ar.save(arpng)
    extra_in = ["-loop", "1", "-framerate", "30", "-t", f"{d:.3f}", "-i", arpng]
    ys = fim_card + 10
    extra_fc = (f";[2:v]format=rgba,fade=in:st=0:d=0.2:alpha=1,fade=out:st={d - 0.2:.3f}:d=0.2:alpha=1,"
                f"setpts=PTS-STARTPTS+{a:.3f}/TB[s];[c][s]overlay=x=(W-w)/2:y='{ys}+22*abs(sin(2*PI*1.4*(t-{a:.3f})))':eval=frame:eof_action=pass[c2]")
# qualidade: limpeza leve de ruído, 1080x1920, nitidez e um toque de contraste/cor
q = "hqdn3d=1.5:1.5:3:3,scale=1080:1920:flags=lanczos,cas=0.6,eq=contrast=1.04:saturation=1.08," if qualidade else ""
fc = (f"[0:v]{q}setsar=1[v];"
      f"[1:v]format=rgba,fade=in:st=0:d=0.2:alpha=1,fade=out:st={d - 0.2:.3f}:d=0.2:alpha=1,"
      f"setpts=PTS-STARTPTS+{a:.3f}/TB[o];"
      f"[v][o]overlay=x=(W-w)/2:y={Y - sh}:eof_action=pass[c]" + extra_fc +
      f";[{'c2' if seta else 'c'}]ass={ass},format=yuv420p[out]")
subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", video,
                "-loop", "1", "-framerate", "30", "-t", f"{d:.3f}", "-i", png, *extra_in,
                "-filter_complex", fc, "-map", "[out]", "-map", "0:a?",
                "-c:v", "libx264", "-preset", "slow", "-crf", "16" if qualidade else "17", "-c:a", "copy",
                "-movflags", "+faststart", saida], check=True)
print(f"OK {saida} ({total:.1f}s; CTA {a:.1f}s–{b:.1f}s)")
