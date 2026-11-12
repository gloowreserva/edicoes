# marca, a cada 0,2s, se o rosto está de frente pra câmera (detector frontal) -> salva olhar.json
import cv2, sys, json, subprocess, numpy as np
v = sys.argv[1]; out = sys.argv[2]
fd = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")
W, H = 270, 480
p = subprocess.Popen(["ffmpeg", "-v", "error", "-i", v, "-vf", f"fps=5,scale={W}:{H}", "-f", "rawvideo", "-pix_fmt", "gray", "-"], stdout=subprocess.PIPE)
res = []
while True:
    b = p.stdout.read(W * H)
    if len(b) < W * H: break
    g = np.frombuffer(b, np.uint8).reshape(H, W)
    f = fd.detectMultiScale(g, 1.1, 6, minSize=(50, 50))
    res.append(1 if len(f) else 0)
json.dump(res, open(out, "w"))
print(v, len(res) / 5, "s; de frente:", round(sum(res) / len(res) * 100), "%")
