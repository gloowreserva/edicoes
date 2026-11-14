import subprocess, sys, numpy as np
def frames(path, t0, dur):
    raw = subprocess.run(["ffmpeg","-v","error","-ss",str(t0),"-i",path,"-t",str(dur),"-vf","fps=30,scale=36:64,format=gray","-f","rawvideo","-"],capture_output=True).stdout
    return np.frombuffer(raw,np.uint8).reshape(-1,64,36).astype(float)
orig, out = sys.argv[1], sys.argv[2]
for pair in sys.argv[3:]:
    to, esperado = map(float, pair.split(":"))
    o = frames(out, to, 0.034)[0]
    c = frames(orig, esperado-0.3, 0.6)
    d = [np.abs(o-f).mean() for f in c]
    k = int(np.argmin(d)); print(f"saida {to:.3f} -> original {esperado-0.3+k/30:.3f} (esperado {esperado:.3f}, desvio {(esperado-0.3+k/30-esperado)*1000:+.0f} ms, dif {d[k]:.1f})")
