import json, re, sys
def norm(w): return re.sub(r"[^\wà-ú]", "", w.lower())
def find_repeats(words, max_n=6, max_gap=1.5):
    """Retorna trechos [ini, fim] a cortar: a 1ª tentativa de palavra/frase repetida em sequência."""
    cuts, i, ws = [], 0, [norm(w["word"]) for w in words]
    while i < len(words):
        hit = None
        for n in range(max_n, 0, -1):
            a, b = ws[i:i + n], ws[i + n:i + 2 * n]
            if len(b) == n and a == b and any(len(x) > 2 for x in a) \
               and words[i + n]["start"] - words[i + n - 1]["end"] < (4.0 if n >= 3 else max_gap):
                hit = n; break
        if hit:
            cuts.append([round(words[i]["start"] - 0.03, 2), round(words[i + hit]["start"] - 0.03, 2), " ".join(ws[i:i + hit])])
            i += hit
        else:
            i += 1
    return cuts
if __name__ == "__main__":
    for f in sys.argv[1:]:
        w = [x for s in json.load(open(f)) for x in s["words"]]
        for c in find_repeats(w): print(f.split("/")[-1], c)
