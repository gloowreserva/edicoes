"""Classifica cada segundo da gravação do Meet: M = orador em câmera cheia, S = tela compartilhada, O = outra pessoa.
Uso: ffmpeg -i VIDEO -vf fps=1,scale=96:54 -f rawvideo -pix_fmt rgb24 PASTA/tiny.rgb
     python3 -I classifica_layout.py PASTA [SEGUNDO_COM_ORADOR_EM_CAMERA]
Gera PASTA/layout.json (uma letra por segundo) e imprime os trechos."""
import numpy as np, json, sys
W=sys.argv[1]
a=np.fromfile(W+'/tiny.rgb',np.uint8).reshape(-1,54,96,3).astype(np.float32)
ref=a[int(sys.argv[2]) if len(sys.argv)>2 else 30]  # quadro com o orador em câmera
out=[]
for i,f in enumerate(a):
    topright=f[0:15,75:96].mean()   # black in screen share
    if topright<25: c='S'   # screen share
    else:
        d=np.abs(f[:, :]-ref)
        # compare background regions (right side frames + top-left wall)
        bg=np.concatenate([d[0:20,0:20].ravel(), d[5:30,55:80].ravel()]).mean()
        c='M' if bg<45 else 'O'
    out.append(c)
s=''.join(out)
json.dump(s,open(W+'/layout.json','w'))
# runs
runs=[];st=0
for i in range(1,len(s)+1):
    if i==len(s) or s[i]!=s[st]:
        runs.append((s[st],st,i));st=i
for c,a0,b in runs:
    if b-a0>=8: print(c,a0,b,b-a0)
print({k:s.count(k) for k in 'SMO'})
