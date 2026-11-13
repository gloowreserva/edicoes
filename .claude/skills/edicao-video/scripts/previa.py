# mosaico (3 quadros/s) só do que vai entrar no vídeo, com o tempo no BRUTO em cada quadro
import json, sys, subprocess, math
v, segs, out = sys.argv[1], json.load(open(sys.argv[2])), sys.argv[3]
sel = "+".join(f"between(t,{a:.2f},{b:.2f})" for a, b in segs)
n = sum(b - a for a, b in segs) * 3
rows = math.ceil(n / 18)
subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", v, "-vf",
    f"fps=3,select='{sel}',scale=100:178,drawtext=text='%{{pts\\:hms}}':x=1:y=1:fontsize=10:fontcolor=yellow:box=1:boxcolor=black,tile=18x{rows}",
    "-frames:v", "1", "-fps_mode", "passthrough", out], check=True)
