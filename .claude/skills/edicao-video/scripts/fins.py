# últimos 0,6s de cada trecho NO VÍDEO FINAL (confere se termina com ele de frente)
import json, sys, subprocess
v, segs, out = sys.argv[1], json.load(open(sys.argv[2])), sys.argv[3]
t = 0; rows = []
for i, (a, b) in enumerate(segs):
    t += b - a; st = max(0, t - 0.6); o = f"{out}_{i:02d}.jpg"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", f"{st:.2f}", "-t", "0.6", "-i", v, "-vf",
        f"fps=10,scale=in_color_matrix=bt709:in_range=tv:w=100:h=178,drawtext=text='{i} %{{pts\\:hms\\:{st:.2f}}}':x=1:y=1:fontsize=10:fontcolor=yellow:box=1:boxcolor=black,tile=6x1",
        "-frames:v", "1", o]); rows.append(o)
subprocess.run(["ffmpeg", "-v", "error", "-y", *sum([["-i", r] for r in rows], []), "-filter_complex",
    "".join(f"[{i}:v]" for i in range(len(rows))) + f"vstack={len(rows)}", out + ".jpg"])
for r in rows: subprocess.run(["rm", "-f", r])
