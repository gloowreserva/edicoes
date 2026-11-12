"""Estilo de edição 3: vídeo B-roll (sem fala) com texto na tela e música, do primeiro ao último quadro.
Uso: python3 -I broll.py VIDEO MUSICA SAIDA "TEXTO" [inicio_musica_em_segundos]
- O texto aparece inteiro no primeiro quadro e fica até o fim (sem fade).
- A música começa no volume cheio no primeiro quadro (use inicio_musica para pular silêncio/introdução).
"""
import os, subprocess, sys

video, musica, saida, texto = sys.argv[1:5]
inicio = float(sys.argv[5]) if len(sys.argv) > 5 else 0.0
dur = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", video],
                           capture_output=True, text=True).stdout)
ass = os.path.splitext(saida)[0] + ".ass"
txt = texto.replace("\n", r"\N")
open(ass, "w").write(f"""[Script Info]
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920
WrapStyle: 0

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: B,Inter SemiBold,50,&H00FFFFFF,&H00FFFFFF,&H00000000,&H78000000,-1,0,0,0,100,100,0,0,1,4.5,2,5,100,100,0,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
Dialogue: 0,0:00:00.00,9:00:00.00,B,,0,0,0,,{txt}
""")
subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", video, "-ss", str(inicio), "-i", musica,
                "-vf", f"scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,fps=30,ass={ass}",
                "-map", "0:v", "-map", "1:a", "-af", f"loudnorm=I=-14:TP=-1.5,afade=t=out:st={max(0, dur - 0.1):.2f}:d=0.1",
                "-t", f"{dur:.3f}", "-c:v", "libx264", "-preset", "medium", "-crf", "20", "-pix_fmt", "yuv420p",
                "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", saida], check=True)
print(f"OK {saida} ({dur:.1f}s)")
