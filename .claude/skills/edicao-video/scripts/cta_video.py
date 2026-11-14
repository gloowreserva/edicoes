"""Estilo 4 (tráfego) com CTA em vídeo: tira falhas, corta o CTA antigo do fim,
melhora a qualidade e emenda um vídeo de CTA novo (uma versão por CTA).

uso: python3 -I cta_video.py VIDEO CORTE_FIM SAIDA_DIR CTA1.mov[:INI:FIM[:INI:FIM...]] [CTA2.mov[...] ...] [--falha INI-FIM ...]
  CORTE_FIM : segundo do vídeo original onde ele termina (antes do CTA antigo, ex.: "se você quer entender...")
  :INI:FIM  : trecho do CTA a usar (do começo ao fim da fala; padrão: o CTA inteiro). Vários pares
              :INI:FIM:INI:FIM tiram pausas/repetições do meio do CTA (os trechos são emendados)
  --falha   : trecho do original com quadros com defeito; esses quadros saem e o quadro anterior segura o lugar
              (o áudio não é tocado, então não perde fala nem dessincroniza)
  --troca   : trecho do original com quadros escuros/piscada NA ENTRADA de uma cena (ex.: 24.0-24.034); esses quadros
              viram o primeiro quadro bom da cena seguinte (sem congelar a cena anterior; áudio intacto)
  --desliza VINI-VFIM:AINI : quadros parados/escuros numa emenda: tira VINI-VFIM do vídeo e o mesmo tempo
              do áudio a partir de AINI (um silêncio logo antes); a fala segue sincronizada depois da emenda
  --cor-cta FILTRO : ajuste de cor extra só no CTA, pra pele bater com o vídeo principal (medir com signalstats
              no centro do rosto: YAVG, SATAVG, UAVG, VAVG). Usar hue=h=..:s=.. (não mexe no branco), não lutyuv.
  --corta   : trecho do original a remover (vídeo e áudio), ex.: travada/pausa em que a mesma cena aparece duas vezes
"""
import json, os, subprocess, sys

args = sys.argv[1:]
falhas, cortes, trocas, desliza = [], [], [], []
cor_cta = ""
if "--cor-cta" in args:
    i = args.index("--cor-cta"); cor_cta = args[i + 1] + ","; del args[i:i + 2]
while "--desliza" in args:
    i = args.index("--desliza"); v, a0 = args[i + 1].split(":"); x, y = map(float, v.split("-"))
    desliza.append((x, y, float(a0))); del args[i:i + 2]
for nome, lista in (("--falha", falhas), ("--corta", cortes), ("--troca", trocas)):
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
# trechos mantidos: vídeo e áudio separados (o --desliza tira quadros parados do vídeo e o mesmo tempo
# de silêncio do áudio logo antes, mantendo a fala sincronizada depois da emenda)
vcut = sorted(cortes + [(a, b) for a, b, _ in desliza])
acut = sorted(cortes + [(c, c + (b - a)) for a, b, c in desliza])
def mantidos(cs):
    keep, t0 = [], 0.0
    for a, b in cs:
        keep.append((t0, a)); t0 = b
    keep.append((t0, corte)); return keep
kv, ka = mantidos(vcut), mantidos(acut)
fc = []
for k, (a, b) in enumerate(kv):
    fc.append(f"[0:v]trim={a}:{b},{'select=' + repr('1' + sel) + ',' if falhas else ''}fps=30,setpts=PTS-STARTPTS,{q}[v{k}]")
for k, (a, b) in enumerate(ka):
    fc.append(f"[0:a]atrim={a}:{b},asetpts=PTS-STARTPTS,aresample=48000,aformat=channel_layouts=stereo[a{k}]")
fc.append("".join(f"[v{k}]" for k in range(len(kv))) + f"concat=n={len(kv)}:v=1:a=0[{'vc' if trocas else 'v'}]")
fc.append("".join(f"[a{k}]" for k in range(len(ka))) + f"concat=n={len(ka)}:v=0:a=1[a]")
def novo_t(t):  # tempo do original -> tempo na base (descontando os cortes de vídeo antes dele)
    return t - sum(b - a for a, b in vcut if b <= t)
extra = []
ult = "vc"
for k, (a, b) in enumerate(trocas):
    extra += ["-ss", f"{b:.3f}", "-i", video]
    fc.append(f"[{k + 1}:v]trim=end_frame=1,setpts=PTS-STARTPTS,{q}[st{k}];"
              f"[{ult}][st{k}]overlay=enable='between(t,{novo_t(a) - 0.001:.3f},{novo_t(b) - 0.002:.3f})':eof_action=repeat[{'v' if k == len(trocas) - 1 else f'vt{k}'}]")
    ult = f"vt{k}"
if not os.path.exists(base):  # reaproveita a base se um render anterior foi interrompido
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", video, *extra, "-filter_complex", ";".join(fc), "-map", "[v]", "-map", "[a]",
                    "-c:v", "libx264", "-preset", "medium", "-crf", "12", "-c:a", "pcm_s16le", base + ".tmp.mkv"], check=True)
    os.replace(base + ".tmp.mkv", base)

for c in ctas:
    path, *tr = c.split(":")
    trechos = [(float(tr[i]), float(tr[i + 1])) for i in range(0, len(tr), 2)] if tr else [(0.0, None)]
    nome = os.path.splitext(os.path.basename(path))[0]
    saida = os.path.join(outdir, f"{os.path.splitext(os.path.basename(video))[0]}_cta_{nome}.mp4")
    ganho = alvo - loud(path)
    # iPhone grava em HDR (HLG/PQ): sem tone mapping a cor fica lavada ("fantasma"); converte para SDR
    # e aplica o mesmo ajuste de cor do vídeo principal, para a paleta ficar igual do começo ao fim
    trc = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=color_transfer",
                          "-of", "csv=p=0", path], capture_output=True, text=True).stdout.strip()
    hdr = (f"zscale=tin={trc}:min=bt2020nc:pin=bt2020:rin=tv:t=linear:npl=203,format=gbrpf32le,zscale=p=bt709,"
           "tonemap=hable:desat=0,zscale=t=bt709:m=bt709:r=tv,") if trc in ("arib-std-b67", "smpte2084") else ""
    cut = []
    fc = f"[1:v]{hdr}scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,fps=30,eq=contrast=1.04:saturation=1.08,{cor_cta}setsar=1,format=yuv420p,split={len(trechos)}" \
         + "".join(f"[cs{k}]" for k in range(len(trechos))) + f";[1:a]aresample=48000,aformat=channel_layouts=stereo,volume={ganho:.2f}dB,asplit={len(trechos)}" \
         + "".join(f"[as{k}]" for k in range(len(trechos))) + ";"
    for k, (ini, fim) in enumerate(trechos):
        fim_v = f":end={fim}" if fim else ""
        # 40 ms de fade no áudio em cada emenda para não estalar
        fc += (f"[cs{k}]trim=start={ini}{fim_v},setpts=PTS-STARTPTS[cv{k}];"
               f"[as{k}]atrim=start={ini}{fim_v},asetpts=PTS-STARTPTS,afade=t=in:d=0.04,areverse,afade=t=in:d={0.15 if k == len(trechos) - 1 else 0.04},areverse[ca{k}];")
    fc += "".join(f"[cv{k}][ca{k}]" for k in range(len(trechos))) + f"concat=n={len(trechos)}:v=1:a=1[cv][ca];" \
          "[0:v][0:a][cv][ca]concat=n=2:v=1:a=1[v][a]"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", base, *cut, "-i", path, "-filter_complex", fc,
                    "-map", "[v]", "-map", "[a]", "-c:v", "libx264", "-preset", "slow", "-crf", "17",
                    "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", saida], check=True)
    print("OK", saida)
os.remove(base)
