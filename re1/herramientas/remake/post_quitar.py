"""post_quitar.py sala_dir extras.json : quita de la sala ya hecha (sala.obj final) los triángulos de 'quitar_final' (caja + material)"""
import sys, json, re, numpy as np
d, ej = sys.argv[1], sys.argv[2]
qs = json.load(open(ej)).get('quitar_final', [])
if not qs: sys.exit(0)
L = open(f'{d}/sala.obj').read().splitlines()
V = np.array([[float(x) for x in l.split()[1:4]] for l in L if l.startswith('v ')])
out = []; cur = None; n = [0] * len(qs)
for l in L:
    if l.startswith('usemtl'): cur = l.split()[1]
    elif l.startswith('f '):
        c = V[[int(x.split('/')[0]) - 1 for x in l.split()[1:4]]].mean(0); fuera = False
        for k, q in enumerate(qs):
            if np.all(c >= q['min']) and np.all(c <= q['max']) and (not q.get('mat') or re.search(q['mat'], cur, re.I)): n[k] += 1; fuera = True; break
        if fuera: continue
    out.append(l)
open(f'{d}/sala.obj', 'w').write('\n'.join(out) + '\n')
for q, k in zip(qs, n): print(f"quitados al final {k} triángulos: {q.get('que', '')}")
