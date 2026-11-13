# folha de revisão: uma linha por trecho = 0,5s do começo (5 quadros) | 1,0s do fim (10 quadros), tempo do BRUTO
import json, sys, subprocess
v, segs, out = sys.argv[1], json.load(open(sys.argv[2])), sys.argv[3]
rows = []
for i, (a, b) in enumerate(segs):
    o = f"/tmp/claude-0/-home-user-Claude-x-Vitor-/db0df03d-6517-5f01-9b28-7a1996109635/scratchpad/lote2/pt_{i:02d}.jpg"
    sel = f"between(t,{a:.2f},{a + 0.3:.2f})+between(t,{max(a, b - 0.8):.2f},{b:.2f})"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", v, "-vf",
        f"fps=10,select='{sel}',scale=118:210,drawtext=text='%{{pts\\:hms}}':x=1:y=1:fontsize=12:fontcolor=yellow:box=1:boxcolor=black,tile=11x1",
        "-frames:v", "1", "-fps_mode", "passthrough", o], check=True)
    rows.append(o)
subprocess.run(["ffmpeg", "-v", "error", "-y", *sum([["-i", r] for r in rows], []), "-filter_complex",
    "".join(f"[{i}:v]" for i in range(len(rows))) + f"vstack={len(rows)}", out], check=True)
