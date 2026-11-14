import json,sys,re
f=sys.argv[1]; r=json.load(open(f"olhar_{f}.json"))
ws=[w for s in json.load(open(f"IMG_{f}.json")) for w in s["words"]]
# frases: quebra em pausa > 0.6s ou pontuação final
fr=[];cur=[]
for w in ws:
    if cur and (w["start"]-cur[-1]["end"]>0.6 or re.search(r"[.?!]$",cur[-1]["word"].strip())): fr.append(cur);cur=[]
    cur.append(w)
if cur: fr.append(cur)
for c in fr:
    a,b=c[0]["start"],c[-1]["end"]; s=r[int(a*5):max(int(a*5)+1,int(b*5))]
    print(f"{a:6.2f}-{b:6.2f} {100*sum(s)//len(s):3d}% "+" ".join(w["word"].strip() for w in c))
