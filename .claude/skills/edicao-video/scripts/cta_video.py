"""Estilo 4 (tráfego) com CTA em vídeo: tira falhas, corta o CTA antigo do fim,
melhora a qualidade e emenda um vídeo de CTA novo (uma versão por CTA).

uso: python3 -I cta_video.py VIDEO CORTE_FIM SAIDA_DIR CTA1.mov[:INI:FIM] [CTA2.mov[:INI:FIM] ...] [--falha INI-FIM ...]
  CORTE_FIM : segundo do vídeo original onde ele termina (antes do CTA antigo, ex.: "se você quer entender...")
  :INI:FIM  : trecho do CTA a usar (do começo ao fim da fala; padrão: o CTA inteiro)
  --falha   : trecho do original com quadros com defeito; esses quadros saem e o quadro anterior segura o lugar
              (o áudio não é tocado, então não perde fala nem dessincroniza)
  --corta   : trecho do original a remover (vídeo e áudio), ex.: travada/pausa em que a mesma cena aparece duas vezes
"""
import json, os, subprocess, sys

args = sys.argv[1:]
falhas, cortes = [], []
for nome, lista in (("--falha", falhas), ("--corta", cortes)):
    while nome in args:
        i = args.index(nome); a, b = map(float, args[i + 1].split("-")); lista.append((a, b)); del args[i:i + 2]
video, corte, outdir, ctas = args[0], float(args[1]), args[2], args[3:]
os.makedirs(outdir, exist_ok=True)

def loud(path):
    out = subprocess.run(["ffmpeg", "-i", path, "-af", "ebur128", "-f", "null", "-"], capture_output=True, text=True).stderr
    return float([l for l in out.splitlines() if l.strip().startswith("I:")][-1].split()[1])

alvo = loud(video)  # o CTA fica no mesmo volume do vídeo original
base = os.path.join(outdir, "_base.mkv")
sel = "".join(f"*not(between(t,{a},{b}))" for a, b in falhas)
q = "hqdn3d=1.5:1.5:3:3,scale=1080:1920:flags=lanczos,cas=0.6,eq=contrast=1.04:saturation=1.08,setsar=1,format=yuv420p"
# trechos mantidos (tirando os --corta), emendados
keep, t0 = [], 0.0
for a, b in sorted(cortes):
    keep.append((t0, a)); t0 = b
keep.append((t0, corte))
fc = []
for k, (a, b) in enumerate(keep):
    fc.append(f"[0:v]trim={a}:{b},{'select=' + repr('1' + sel) + ',' if falhas else ''}fps=30,setpts=PTS-STARTPTS,{q}[v{k}];"
              f"[0:a]atrim={a}:{b},asetpts=PTS-STARTPTS,aresample=48000,aformat=channel_layouts=stereo[a{k}]")
fc.append("".join(f"[v{k}][a{k}]" for k in range(len(keep))) + f"concat=n={len(keep)}:v=1:a=1[v][a]")
if not os.path.exists(base):  # reaproveita a base se um render anterior foi interrompido
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", video, "-filter_complex", ";".join(fc), "-map", "[v]", "-map", "[a]",
                    "-c:v", "libx264", "-preset", "medium", "-crf", "12", "-c:a", "pcm_s16le", base + ".tmp.mkv"], check=True)
    os.replace(base + ".tmp.mkv", base)

for c in ctas:
    path, *tr = c.split(":")
    ini, fim = (float(tr[0]), float(tr[1])) if tr else (0.0, None)
    nome = os.path.splitext(os.path.basename(path))[0]
    saida = os.path.join(outdir, f"{os.path.splitext(os.path.basename(video))[0]}_cta_{nome}.mp4")
    ganho = alvo - loud(path)
    # iPhone grava em HDR (HLG/PQ): sem tone mapping a cor fica lavada ("fantasma"); converte para SDR
    # e aplica o mesmo ajuste de cor do vídeo principal, para a paleta ficar igual do começo ao fim
    trc = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=color_transfer",
                          "-of", "csv=p=0", path], capture_output=True, text=True).stdout.strip()
    hdr = (f"zscale=tin={trc}:min=bt2020nc:pin=bt2020:rin=tv:t=linear:npl=203,format=gbrpf32le,zscale=p=bt709,"
           "tonemap=hable:desat=0,zscale=t=bt709:m=bt709:r=tv,") if trc in ("arib-std-b67", "smpte2084") else ""
    cut = ["-ss", f"{ini:.3f}"] + (["-t", f"{fim - ini:.3f}"] if fim else [])
    fc = (f"[1:v]{hdr}scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,fps=30,"
          "eq=contrast=1.04:saturation=1.08,setsar=1,format=yuv420p[cv];"
          f"[1:a]aresample=48000,aformat=channel_layouts=stereo,volume={ganho:.2f}dB,afade=t=out:st={max(0, (fim or 0) - ini - 0.15):.3f}:d=0.15[ca];"
          "[0:v][0:a][cv][ca]concat=n=2:v=1:a=1[v][a]")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", base, *cut, "-i", path, "-filter_complex", fc,
                    "-map", "[v]", "-map", "[a]", "-c:v", "libx264", "-preset", "slow", "-crf", "17",
                    "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", saida], check=True)
    print("OK", saida)
os.remove(base)
