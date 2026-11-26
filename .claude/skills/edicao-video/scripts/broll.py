"""Estilo de edição 3: vídeo B-roll (sem fala) com texto na tela e música, do primeiro ao último quadro.
Uso: python3 -I broll.py VIDEO MUSICA SAIDA "TEXTO" [inicio_musica_em_segundos] ["CTA_FINAL"] [cor: rosa|verde|azul|amarelo|roxo|vermelho]
- CTA_FINAL (opcional, ex.: "GRUPO GRÁTIS\nNA BIO"): no último ~1,2 s o texto sai e entra um selo grande e chamativo
  (rosa com amarelo, entrada com "pop" e leve tremida), no meio da tela.
- O texto aparece inteiro no primeiro quadro e fica até o fim (sem fade).
- A música começa no volume cheio no primeiro quadro (use inicio_musica para pular silêncio/introdução).
"""
import os, subprocess, sys

video, musica, saida, texto = sys.argv[1:5]
inicio = float(sys.argv[5]) if len(sys.argv) > 5 else 0.0
cta = sys.argv[6] if len(sys.argv) > 6 else ""
# 7º argumento: cor do selo final (variar entre versões pra não parecer vídeo repetido)
CORES = {  # (texto, caixa) em &HBBGGRR
    "rosa": ("&H0000F0FF", "&H00B414FF"),     # amarelo na caixa rosa
    "verde": ("&H00000000", "&H0039FF14"),    # preto na caixa verde-limão
    "azul": ("&H00FFFFFF", "&H00FF6A00"),     # branco na caixa azul
    "amarelo": ("&H00000000", "&H0000E1FF"),  # preto na caixa amarela
    "roxo": ("&H00FFFFFF", "&H00D4228B"),     # branco na caixa roxa
    "vermelho": ("&H00FFFFFF", "&H002020E6"), # branco na caixa vermelha
}
cor_txt, cor_box = CORES.get(sys.argv[7] if len(sys.argv) > 7 else "rosa", CORES["rosa"])
dur = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", video],
                           capture_output=True, text=True).stdout)
# brutos de iPhone são HDR (HLG): conversão de verdade pra BT.709, senão a pele fica pálida
_trc = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=color_transfer",
                       "-of", "csv=p=0", video], capture_output=True, text=True).stdout.strip().strip(",")
HDR = ("zscale=t=linear:npl=203:tin=arib-std-b67:pin=bt2020:min=bt2020nc,format=gbrpf32le,zscale=p=bt709,"
       "tonemap=hable:desat=0,zscale=t=bt709:m=bt709:r=tv,format=yuv420p,eq=brightness=0.05:contrast=1.05,"
       if _trc in ("arib-std-b67", "smpte2084") else "")
ass = os.path.splitext(saida)[0] + ".ass"
txt = texto.replace("\n", r"\N")
def ts(t):
    return f"{int(t // 3600)}:{int(t % 3600 // 60):02d}:{t % 60:05.2f}"
fim_txt = max(0.5, dur - 1.2) if cta else 32400
cta_ev = ""
if cta:
    c = cta.replace("\n", r"\N")
    cta_ev = (f"Dialogue: 1,{ts(fim_txt)},{ts(dur + 1)},CTA,,0,0,0,,"
              r"{\fscx40\fscy40\frz-8\t(0,140,\fscx118\fscy118\frz4)\t(140,260,\fscx100\fscy100\frz-3)\t(260,600,\frz2)\t(600,900,\frz-2)}" + c + "\n")
open(ass, "w").write(f"""[Script Info]
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920
WrapStyle: 0

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: CTA,Inter,96,{cor_txt},{cor_txt},{cor_box},&H00000000,-1,0,0,0,100,100,0,0,3,34,0,5,80,80,0,1
Style: B,Inter SemiBold,50,&H00FFFFFF,&H00FFFFFF,&H00000000,&H78000000,-1,0,0,0,100,100,0,0,1,4.5,2,8,90,150,300,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
Dialogue: 0,0:00:00.00,{ts(fim_txt)},B,,0,0,0,,{txt}
{cta_ev}""")
subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", video, "-ss", str(inicio), "-i", musica,
                "-vf", f"{HDR}scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,fps=30,ass={ass}",
                "-map", "0:v", "-map", "1:a", "-af", f"loudnorm=I=-14:TP=-1.5,afade=t=out:st={max(0, dur - 0.1):.2f}:d=0.1",
                "-t", f"{dur:.3f}", "-c:v", "libx264", "-preset", "medium", "-crf", "20", "-pix_fmt", "yuv420p",
                "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", saida], check=True)
print(f"OK {saida} ({dur:.1f}s)")
