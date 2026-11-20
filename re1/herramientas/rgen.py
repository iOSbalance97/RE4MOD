"""Generador de salas para el remake de RE1 en RE4 (salas que UC no tiene).
Una "suite" = una sala de RE4 hecha de celdas rectangulares (habitaciones, pasillos, exteriores, cuevas),
con huecos de paso entre ellas, puertas (cerradas, con su AEV), escaleras/rampas, muebles, ventanas y velas.
Salida en /home/claude/gen/<suite>/: sala.obj + sala.mtl + texturas (metros, marco propio de la suite),
col.npz (triángulos de colisión en mm y tipo), meta.json (puertas con su punto de llegada, llamas, lámparas).
Las coordenadas de la suite son en metros: x hacia el este, z hacia el norte, y arriba."""
import json, os, shutil, sys
import numpy as np

TEX = {}          # nombre lógico -> ruta png
def _t(n, p): TEX[n] = p
UCM = '/home/claude/uc/m'; UCO = '/home/claude/uc/obj'; R4 = '/home/claude/texlib_re4'
# mansión (UC)
_t('papel_verde', f'{UCM}/r103/EO_r103KABE8.png'); _t('papel_oliva', f'{UCM}/r100/r100_kabe_a.png')
_t('papel_beige', f'{UCM}/r106/r106_kabe000.png'); _t('papel_crema', f'{UCM}/r105/r105_kabegami000.png')
_t('papel_rojo', f'{UCM}/r103/EO_r103KABE9.png'); _t('papel_gris', f'{UCM}/r108/r108_kabe04.png')
_t('marmol_pared', f'{UCM}/r102/yg_wall09.png'); _t('marmol_suelo', f'{UCM}/r102/yg_floor2.png')
_t('zocalo', f'{UCM}/r108/r108_habaki01.png'); _t('zocalo2', f'{UCM}/r105/r105_wood_in04.png')
_t('panel_madera', f'{UCM}/r105/r105_wood_in05.png'); _t('madera_oscura', f'{UCM}/r102/yg_wood21.png')
_t('moldura', f'{UCM}/r102/yg_wood13.png')
_t('parquet', f'{UCM}/r105/r105_yuka_in02.png'); _t('parquet2', f'{UCM}/r108/r108_yuka.png'); _t('tarima', f'{UCM}/r106/r106_yuka02.png')
_t('alfombra', f'{UCM}/r107/st_107jutan_a.png'); _t('alfombra2', f'{UCM}/r102/yg_lug01.png')
_t('techo', f'{UCM}/r102/yg_ceilling02.png'); _t('techo_madera', f'{UCM}/r108/r108_tenjo.png'); _t('techo_cuadros', f'{UCM}/r102/yg_ceilling02.png')
_t('azulejo', f'{UCM}/r105/r105_ham113yuka0.png') if os.path.exists(f'{UCM}/r105/r105_ham113yuka0.png') else None
_t('pared_vieja', f'{UCM}/r106/r106_sotokabe.png'); _t('suelo_viejo', f'{UCM}/r106/r106_sotoyuka.png')
_t('puerta', f'{UCM}/r112/r112_door01.png'); _t('puerta2', f'{UCM}/r102/yg_door05.png'); _t('puerta_doble', f'{UCM}/r105/r105_door01.png')
_t('puerta3', f'{UCM}/r102/yg_door08.png'); _t('puerta_reja', f'{UCM}/r102/yg_door09.png'); _t('puerta_cabana', f'{UCO}/r119/r119_r400_door.png')
_t('cuadro1', f'{UCM}/r102/yg_picture_01.png'); _t('cuadro2', f'{UCM}/r102/yg_picture_02.png'); _t('cuadro3', f'{UCM}/r102/yg_picture_03.png')
_t('retrato', f'{UCM}/r102/yg_portrate01.png'); _t('estante', f'{UCM}/r115/r115_hondana_a512.png'); _t('estante2', f'{UCM}/r115/r115_hondana_b512.png')
_t('laton', f'{UCM}/r102/yg_metal02.png'); _t('tela', f'{UCM}/r102/yg_fabric_01.png'); _t('mesa', f'{UCM}/r102/yg_table_tenban_maru.png')
_t('ventana', f'{UCO}/r111/r111_wakuwindow.png')
# exteriores / cuevas / residencia / laboratorio (UC)
_t('cesped', f'{UCO}/r117/r117_ground12.png'); _t('tierra', f'{UCO}/r118/r118_ground01.png'); _t('grava', f'{UCO}/r117/r117_ground03.png')
_t('losa_ext', f'{UCO}/r116/r116_ground04.png'); _t('muro_piedra', f'{UCO}/r117/r117_wall01.png'); _t('muro_ladrillo', f'{UCO}/r116/r116_wall01.png')
_t('seto', f'{UCO}/r118/r118_wall05.png'); _t('cielo', f'{UCO}/r116/r116_sky.png'); _t('valla', f'{UCO}/r119/r119_wood_fence00.png') if os.path.exists(f'{UCO}/r119/r119_wood_fence00.png') else None
_t('roca', f'{UCO}/r121/r121_gake06a.png'); _t('roca2', f'{UCO}/r120/r120_iwa03.png'); _t('suelo_cueva', f'{UCO}/r121/r121_jyariiwa00.png')
_t('madera_tosca', f'{UCO}/r122/r122_taru01.png'); _t('tablas', f'{UCO}/r123/kabe5_2.png') if os.path.exists(f'{UCO}/r123/kabe5_2.png') else None
_t('lab_pared', f'{UCO}/r139/r139_kabe_a.png'); _t('lab_suelo', f'{UCO}/r140/r140_yuka.png'); _t('lab_techo', f'{UCO}/r138/r138_konkuri_a.png')
_t('lab_panel', f'{UCO}/r140/r140_panel1.png'); _t('lab_puerta', f'{UCO}/r134/r134_doorA.png'); _t('lab_metal', f'{UCO}/r140/r140_teppan2.png')
_t('hormigon', f'{UCO}/r138/r138_konkuri_a.png'); _t('rejilla', f'{UCO}/r120/r120_water.png')
_t('azulejo_lab', f'{UCO}/r139/r139_yuka_a.png')
# RE4 (castillo y pueblo)
_t('castillo_piedra', f'{R4}/r20a_002.png'); _t('castillo_piedra2', f'{R4}/r20a_003.png'); _t('castillo_suelo', f'{R4}/r20a_001.png')
_t('castillo_puerta', f'{R4}/r20a_053.png'); _t('tapiz', f'{R4}/r20a_066.png'); _t('pueblo_madera', f'{R4}/r104_019.png')
_t('pueblo_tablas', f'{R4}/r104_026.png'); _t('pueblo_suelo', f'{R4}/r104_001.png'); _t('cripta', f'{R4}/r200_020.png'); _t('cripta2', f'{R4}/r200_021.png')
_t('re4_metal', f'{R4}/r221_007.png'); _t('re4_metal2', f'{R4}/r221_036.png')
TEX = {k: v for k, v in TEX.items() if v and os.path.exists(v)}

ESTILOS = {
    'verde':    dict(pared='papel_verde', zocalo='zocalo', suelo='parquet', techo='techo', moldura='moldura', puerta='puerta', alfombra='alfombra'),
    'oliva':    dict(pared='papel_oliva', zocalo='zocalo2', suelo='parquet2', techo='techo_madera', moldura='moldura', puerta='puerta', alfombra='alfombra2'),
    'beige':    dict(pared='papel_beige', zocalo='zocalo2', suelo='tarima', techo='techo', moldura='moldura', puerta='puerta2', alfombra='alfombra'),
    'crema':    dict(pared='papel_crema', zocalo='zocalo', suelo='parquet', techo='techo_cuadros', moldura='moldura', puerta='puerta', alfombra='alfombra2'),
    'rojo':     dict(pared='papel_rojo', zocalo='zocalo', suelo='parquet2', techo='techo', moldura='moldura', puerta='puerta', alfombra='alfombra'),
    'gris':     dict(pared='papel_gris', zocalo='zocalo2', suelo='parquet', techo='techo', moldura='moldura', puerta='puerta2', alfombra='alfombra'),
    'madera':   dict(pared='panel_madera', zocalo='madera_oscura', suelo='parquet2', techo='techo_madera', moldura='moldura', puerta='puerta', alfombra='alfombra'),
    'marmol':   dict(pared='marmol_pared', zocalo='madera_oscura', suelo='marmol_suelo', techo='techo_cuadros', moldura='moldura', puerta='puerta_doble', alfombra='alfombra2'),
    'servicio': dict(pared='pared_vieja', zocalo='madera_oscura', suelo='suelo_viejo', techo='techo_madera', moldura=None, puerta='puerta2', alfombra=None),
    'sotano':   dict(pared='castillo_piedra', zocalo=None, suelo='castillo_suelo', techo='castillo_piedra2', moldura=None, puerta='castillo_puerta', alfombra=None),
    'cripta':   dict(pared='cripta', zocalo=None, suelo='cripta2', techo='cripta', moldura=None, puerta='castillo_puerta', alfombra=None),
    'jardin':   dict(pared='muro_piedra', zocalo=None, suelo='cesped', techo=None, moldura=None, puerta='castillo_puerta', alfombra=None, exterior=True),
    'camino':   dict(pared='seto', zocalo=None, suelo='tierra', techo=None, moldura=None, puerta='castillo_puerta', alfombra=None, exterior=True),
    'patio':    dict(pared='muro_ladrillo', zocalo=None, suelo='losa_ext', techo=None, moldura=None, puerta='castillo_puerta', alfombra=None, exterior=True),
    'cueva':    dict(pared='roca', zocalo=None, suelo='suelo_cueva', techo='roca2', moldura=None, puerta='puerta_cabana', alfombra=None, cueva=True),
    'cabana':   dict(pared='pueblo_madera', zocalo=None, suelo='pueblo_suelo', techo='pueblo_tablas', moldura=None, puerta='puerta_cabana', alfombra=None),
    'residencia': dict(pared='papel_crema', zocalo='zocalo2', suelo='tarima', techo='techo_madera', moldura='moldura', puerta='puerta2', alfombra='alfombra2'),
    'lab':      dict(pared='lab_pared', zocalo='lab_metal', suelo='lab_suelo', techo='lab_techo', moldura=None, puerta='lab_puerta', alfombra=None, lab=True),
    'lab_hormigon': dict(pared='hormigon', zocalo='re4_metal', suelo='re4_metal', techo='lab_techo', moldura=None, puerta='lab_puerta', alfombra=None, lab=True),
}

class Suite:
    def __init__(self, nombre):
        self.nombre = nombre; self.quads = []; self.col = []; self.puertas = []; self.llamas = []; self.lamparas = []
    # ------------------------------------------------------------ primitivas
    def quad(self, tex, P, uv=None, col=None):
        """P: 4 puntos en orden antihorario visto desde el lado visible. col: 0 suelo, 1 pendiente, 2 pared (None = sin colisión)"""
        P = np.asarray(P, float)
        if uv is None:
            n = np.cross(P[1] - P[0], P[3] - P[0]); n /= np.linalg.norm(n) + 1e-12
            if abs(n[1]) > 0.7: uv = P[:, [0, 2]] / 2.0
            else:
                d = P[1] - P[0]; d[1] = 0; L = np.linalg.norm(d); s0 = P[0][0] * abs(d[2]) / max(L, 1e-9) + P[0][2] * abs(d[0]) / max(L, 1e-9)
                uv = np.array([[s0, P[0][1]], [s0 + L, P[1][1]], [s0 + L, P[2][1]], [s0, P[3][1]]]) / 2.0
        self.quads.append((tex, P, np.asarray(uv, float)))
        if col is not None:
            self.col.append((col, P[[0, 1, 2]])); self.col.append((col, P[[0, 2, 3]]))
    def caja(self, tex, x0, y0, z0, x1, y1, z1, colision=True, tapa=True, tex_tapa=None, escala=None):
        """caja maciza (mueble): 4 lados + tapa; colisión de pared en los lados"""
        c = 2 if colision else None
        s = escala
        def uvw(L, h): return None if s is None else np.array([[0, 0], [L, 0], [L, h], [0, h]]) / s
        self.quad(tex, [(x0, y0, z0), (x1, y0, z0), (x1, y1, z0), (x0, y1, z0)][::-1], col=c)      # cara sur (mira -z)
        self.quad(tex, [(x1, y0, z1), (x0, y0, z1), (x0, y1, z1), (x1, y1, z1)][::-1], col=c)
        self.quad(tex, [(x0, y0, z1), (x0, y0, z0), (x0, y1, z0), (x0, y1, z1)][::-1], col=c)
        self.quad(tex, [(x1, y0, z0), (x1, y0, z1), (x1, y1, z1), (x1, y1, z0)][::-1], col=c)
        if tapa: self.quad(tex_tapa or tex, [(x0, y1, z0), (x0, y1, z1), (x1, y1, z1), (x1, y1, z0)])
    # ------------------------------------------------------------ pared con aberturas
    def pared(self, est, a, b, y0, h, normal, aberturas, techo=True, exterior=False):
        """pared de a a b (xz) mirando hacia `normal` (hacia dentro). aberturas: [(s0, s1, alto, tipo)] a lo largo de a->b"""
        a = np.array(a, float); b = np.array(b, float); L = np.linalg.norm(b - a); u = (b - a) / L
        def P(s, y): p = a + u * s; return (p[0], y, p[1])
        # orden de vértices: que la cara mire hacia normal
        def q(tex, s0, s1, ya, yb, col=2):
            pts = [P(s0, ya), P(s1, ya), P(s1, yb), P(s0, yb)]
            n = np.cross(np.subtract(pts[1], pts[0]), np.subtract(pts[3], pts[0]))
            if n[0] * normal[0] + n[2] * normal[1] < 0: pts = [pts[1], pts[0], pts[3], pts[2]]
            self.quad(tex, pts, col=col)
        ab = sorted(aberturas)
        tramos = []; s = 0.0
        for s0, s1, alto, tipo in ab:
            if s0 > s: tramos.append((s, s0, None))
            tramos.append((s0, s1, (alto, tipo))); s = s1
        if s < L: tramos.append((s, L, None))
        zh = 0.9 if est.get('zocalo') else 0.0
        for s0, s1, ab_ in tramos:
            if s1 - s0 < 1e-4: continue
            if ab_ is None and est.get('cueva'):
                self._roca(est['pared'], P, s0, s1, y0, y0 + h, normal); continue
            if ab_ is None:
                if zh: q(est['zocalo'], s0, s1, y0, y0 + zh, col=None); q(est['pared'], s0, s1, y0 + zh, y0 + h, col=None)
                else: q(est['pared'], s0, s1, y0, y0 + h, col=None)
                if est.get('moldura') and techo: q(est['moldura'], s0, s1, y0 + h - 0.22, y0 + h - 0.02, col=None)
            else:
                alto, tipo = ab_
                if alto < h: q(est['pared'], s0, s1, y0 + alto, y0 + h, col=None)        # dintel
        # colisión de toda la pared salvo pasos abiertos (las puertas quedan cerradas: colisión continua)
        s = 0.0
        for s0, s1, alto, tipo in ab:
            if tipo == 'paso':
                if s0 > s: self._colpared(P, s, s0, y0, h, normal)
                s = s1
        if s < L: self._colpared(P, s, L, y0, h, normal)
    def _roca(self, tex, P, s0, s1, ya, yb, normal):
        """pared de roca: rejilla de 1 m con relieve (solo visual; la colisión es la pared plana)"""
        ns = max(1, int(np.ceil((s1 - s0) / 1.0))); ny = max(1, int(np.ceil((yb - ya) / 1.0)))
        nn = np.array([normal[0], 0.0, normal[1]])
        def pt(i, j):
            s = s0 + (s1 - s0) * i / ns; y = ya + (yb - ya) * j / ny; p = np.array(P(s, y), float)
            borde = i in (0, ns) or j in (0, ny)
            k = np.sin(p[0] * 12.9898 + p[1] * 78.233 + p[2] * 37.719) * 43758.5453; r = (k - np.floor(k))
            return p + nn * ((0.05 if borde else 0.35) * r - 0.02), np.array([s, y]) / 2.0
        for i in range(ns):
            for j in range(ny):
                (a, ua), (b, ub), (c, uc), (d, ud) = pt(i, j), pt(i + 1, j), pt(i + 1, j + 1), pt(i, j + 1)
                pts = [a, b, c, d]; uv = [ua, ub, uc, ud]
                n = np.cross(pts[1] - pts[0], pts[3] - pts[0])
                if n[0] * normal[0] + n[2] * normal[1] < 0: pts = [b, a, d, c]; uv = [ub, ua, ud, uc]
                self.quads.append((tex, np.array(pts), np.array(uv)))
    def _colpared(self, P, s0, s1, y0, h, normal):
        pts = np.array([P(s0, y0), P(s1, y0), P(s1, y0 + max(h, 2.6)), P(s0, y0 + max(h, 2.6))])
        n = np.cross(pts[1] - pts[0], pts[3] - pts[0])
        if n[0] * normal[0] + n[2] * normal[1] < 0: pts = pts[[1, 0, 3, 2]]
        self.col.append((2, pts[[0, 1, 2]])); self.col.append((2, pts[[0, 2, 3]]))
    # ------------------------------------------------------------ puerta (hoja cerrada + marco)
    def hoja(self, est, centro, u, normal, y0, ancho, alto, doble=False, tex=None):
        tex = tex or est['puerta']; c = np.array(centro, float); u = np.array(u, float); n = np.array(normal, float)
        e = 0.03
        p0 = c - u * ancho / 2 + n * e; p1 = c + u * ancho / 2 + n * e
        pts = [(p0[0], y0, p0[1]), (p1[0], y0, p1[1]), (p1[0], y0 + alto, p1[1]), (p0[0], y0 + alto, p0[1])]
        nn = np.cross(np.subtract(pts[1], pts[0]), np.subtract(pts[3], pts[0]))
        if nn[0] * n[0] + nn[2] * n[1] < 0: pts = [pts[1], pts[0], pts[3], pts[2]]
        if doble:
            m = (np.array(pts[0]) + np.array(pts[1])) / 2; mt = (np.array(pts[3]) + np.array(pts[2])) / 2
            self.quad(tex, [pts[0], m, mt, pts[3]], uv=[[0, 0], [1, 0], [1, 1], [0, 1]])
            self.quad(tex, [m, pts[1], pts[2], mt], uv=[[1, 0], [0, 0], [0, 1], [1, 1]])
        else:
            self.quad(tex, pts, uv=[[0, 0], [1, 0], [1, 1], [0, 1]])
        # marco
        mt = 'madera_oscura' if 'madera_oscura' in TEX else tex
        for s in (-1, 1):
            q0 = c + u * s * (ancho / 2 + 0.06); q1 = c + u * s * (ancho / 2 - 0.04)
            self.caja(mt, min(q0[0], q1[0]) - (0.06 if abs(u[1]) > 0.5 else 0), y0, min(q0[1], q1[1]) - (0.06 if abs(u[0]) > 0.5 else 0),
                      max(q0[0], q1[0]) + (0.06 if abs(u[1]) > 0.5 else 0), y0 + alto + 0.08, max(q0[1], q1[1]) + (0.06 if abs(u[0]) > 0.5 else 0), colision=False)
    # ------------------------------------------------------------ salida
    def guardar(self, out):
        if os.path.exists(out): shutil.rmtree(out)
        os.makedirs(out)
        usados = sorted(set(t for t, _, _ in self.quads))
        with open(f'{out}/sala.mtl', 'w') as f:
            for t in usados:
                fn = os.path.basename(TEX[t]); shutil.copy(TEX[t], f'{out}/{t}.png')
                f.write(f'newmtl {t}\nKd 1 1 1\nmap_Kd {t}.png\n')
        with open(f'{out}/sala.obj', 'w') as f:
            f.write('mtllib sala.mtl\n'); vb = 1; cur = None
            for t, P, uv in sorted(self.quads, key=lambda q: q[0]):
                if t != cur: f.write(f'usemtl {t}\n'); cur = t
                for p in P: f.write(f'v {p[0]:.4f} {p[1]:.4f} {p[2]:.4f}\n')
                for w in uv: f.write(f'vt {w[0]:.4f} {w[1]:.4f}\n')
                f.write(f'f {vb}/{vb} {vb+1}/{vb+1} {vb+2}/{vb+2}\nf {vb}/{vb} {vb+2}/{vb+2} {vb+3}/{vb+3}\n'); vb += 4
        K = np.array([k for k, _ in self.col], int); T = np.array([t for _, t in self.col], float) * 1000.0
        np.savez(f'{out}/col.npz', K=K, T=T)
        json.dump(dict(puertas=self.puertas, llamas=[list(map(float, p)) for p in self.llamas],
                       lamparas=[list(map(float, p)) for p in self.lamparas]), open(f'{out}/meta.json', 'w'), indent=1)
        return len(self.quads) * 2, len(usados)

LADOS = {'S': (lambda r: ((r[0], r[1]), (r[2], r[1])), (0, 1)), 'N': (lambda r: ((r[2], r[3]), (r[0], r[3])), (0, -1)),
         'O': (lambda r: ((r[0], r[3]), (r[0], r[1])), (1, 0)), 'E': (lambda r: ((r[2], r[1]), (r[2], r[3])), (-1, 0))}

def construir(spec):
    """spec: dict(nombre, celdas=[dict(id, r=(x0,z0,x1,z1), y, h, estilo, techo)], pasos=[(celda, lado, pos, ancho)],
    puertas=[dict(id, celda, lado, pos, ancho, alto, doble, destino)], escaleras=[...], muebles=[...], velas=[...], lamparas=[...], ventanas=[...], cuadros=[...])"""
    S = Suite(spec['nombre'])
    cel = {c['id']: c for c in spec['celdas']}
    for c in spec['celdas']:
        c.setdefault('y', 0.0); c.setdefault('h', 3.2); c.setdefault('estilo', spec.get('estilo', 'verde'))
    ab = {(c['id'], l): [] for c in spec['celdas'] for l in 'NSEO'}
    def pos_lado(c, l, pos):
        (a, b), n = LADOS[l][0](c['r']), LADOS[l][1]
        a = np.array(a, float); b = np.array(b, float); u = (b - a) / np.linalg.norm(b - a)
        return a, b, u, np.array(n, float)
    for p in spec.get('pasos', []):
        cid, l, pos, w = p[:4]; alto = p[4] if len(p) > 4 else 2.7
        ab[(cid, l)].append((pos - w / 2, pos + w / 2, alto, 'paso'))
    for d in spec.get('puertas', []):
        c = cel[d['celda']]; d.setdefault('ancho', 1.3 if d.get('doble') else 1.0); d.setdefault('alto', 2.4)
        ab[(d['celda'], d['lado'])].append((d['pos'] - d['ancho'] / 2, d['pos'] + d['ancho'] / 2, d['alto'], 'puerta'))
    for v in spec.get('ventanas', []):
        pass
    for c in spec['celdas']:
        est = dict(ESTILOS[c['estilo']]); est.update(c.get('tex', {}))
        x0, z0, x1, z1 = c['r']; y = c['y']; h = c['h']
        # suelo (las rampas de escalera ponen el suyo)
        if not c.get('sin_suelo'):
            S.quad(c.get('suelo') or est['suelo'], [(x0, y, z0), (x0, y, z1), (x1, y, z1), (x1, y, z0)], col=0)
        if c.get('alfombra') and est.get('alfombra'):
            ax0, az0, ax1, az1 = c['alfombra']
            S.quad(est['alfombra'], [(ax0, y + 0.01, az0), (ax0, y + 0.01, az1), (ax1, y + 0.01, az1), (ax1, y + 0.01, az0)],
                   uv=[[0, 0], [0, 1], [1, 1], [1, 0]])
        techo = c.get('techo', est.get('techo') is not None)
        if techo and est.get('techo'):
            S.quad(est['techo'], [(x0, y + h, z0), (x1, y + h, z0), (x1, y + h, z1), (x0, y + h, z1)])
        for l in 'NSEO':
            if l in c.get('abierto', ''): continue
            a, b, u, n = pos_lado(c, l, 0)
            S.pared(est, a, b, y, h, n, ab[(c['id'], l)], techo=techo)
        if est.get('cueva'): pass
    # hojas de puerta y datos de AEV
    for d in spec.get('puertas', []):
        c = cel[d['celda']]; est = dict(ESTILOS[c['estilo']]); est.update(c.get('tex', {}))
        a, b, u, n = pos_lado(c, d['lado'], d['pos'])
        cen = a + u * d['pos']
        S.hoja(est, cen, u, n, c['y'], d['ancho'], d['alto'], d.get('doble', False), d.get('tex'))
        frente = cen + n * 0.9
        S.puertas.append(dict(id=d['id'], destino=d['destino'], centro=[float(cen[0]), c['y'], float(cen[1])], normal=n.tolist(),
                              u=u.tolist(), ancho=d['ancho'], llegada=[float(frente[0]), c['y'], float(frente[1])],
                              ang=float(np.arctan2(n[0], n[1]))))
    # escaleras: ('x0,z0,x1,z1', y0, y1, dirección de subida 'N'|'S'|'E'|'O', estilo)
    for e in spec.get('escaleras', []):
        (x0, z0, x1, z1), y0, y1, dr = e[:4]; est = ESTILOS[e[4] if len(e) > 4 else spec.get('estilo', 'verde')]
        n = max(2, int(round((y1 - y0) / 0.18)))
        ax = {'N': (2, 1), 'S': (2, -1), 'E': (0, 1), 'O': (0, -1)}[dr]
        lo_, hi_ = (z0, z1) if ax[0] == 2 else (x0, x1)
        for k in range(n):
            t0 = k / n; t1 = (k + 1) / n
            s0 = lo_ + (hi_ - lo_) * (t0 if ax[1] > 0 else 1 - t1); s1 = lo_ + (hi_ - lo_) * (t1 if ax[1] > 0 else 1 - t0)
            yy = y0 + (y1 - y0) * (k + 1) / n
            if ax[0] == 2: S.caja(est['suelo'], x0, y0, s0, x1, yy, s1, colision=False, escala=1.0)
            else: S.caja(est['suelo'], s0, y0, z0, s1, yy, z1, colision=False, escala=1.0)
        # rampa de colisión
        if ax[0] == 2:
            ya, yb = (y0, y1) if ax[1] > 0 else (y1, y0)
            P = np.array([(x0, ya, z0), (x0, yb, z1), (x1, yb, z1), (x1, ya, z0)])
        else:
            ya, yb = (y0, y1) if ax[1] > 0 else (y1, y0)
            P = np.array([(x0, ya, z0), (x0, ya, z1), (x1, yb, z1), (x1, yb, z0)])
        nrm = np.cross(P[1] - P[0], P[3] - P[0])
        if nrm[1] < 0: P = P[[0, 3, 2, 1]]
        k = 0 if abs(y1 - y0) < 1e-6 else 1
        S.col.append((k, P[[0, 1, 2]])); S.col.append((k, P[[0, 2, 3]]))
        # barandillas como paredes de colisión a los lados
        if e[5:6] and e[5]:
            pass
    # muebles: (tipo, x0, z0, x1, z1, alto, [tex], [y])
    for m in spec.get('muebles', []):
        tipo, x0, z0, x1, z1, h = m[:6]; tex = m[6] if len(m) > 6 and m[6] else None; yb = m[7] if len(m) > 7 else 0.0
        if tipo == 'mesa':
            t = tex or 'madera_oscura'; e_ = 0.08
            S.caja(t, x0, yb + h - 0.06, z0, x1, yb + h, z1, colision=False, tex_tapa='mesa' if 'mesa' in TEX else t)
            for px, pz in ((x0, z0), (x1 - e_, z0), (x0, z1 - e_), (x1 - e_, z1 - e_)): S.caja(t, px, yb, pz, px + e_, yb + h - 0.06, pz + e_, colision=False)
            S._colcaja(x0, z0, x1, z1, yb, 1.0)
        elif tipo == 'estante':
            S.caja(tex or 'estante', x0, yb, z0, x1, yb + h, z1, escala=None)
        elif tipo == 'caja':
            S.caja(tex or 'madera_tosca', x0, yb, z0, x1, yb + h, z1)
        elif tipo == 'columna':
            S.caja(tex or 'marmol_pared', x0, yb, z0, x1, yb + h, z1)
        elif tipo == 'lapida':
            S.caja(tex or 'castillo_piedra', x0, yb, z0, x1, yb + h, z1)
        elif tipo == 'cama':
            S.caja('madera_oscura', x0, yb, z0, x1, yb + 0.45, z1, tex_tapa='tela'); S.caja('madera_oscura', x0, yb, z0, x1, yb + 1.1, z0 + 0.08)
        elif tipo == 'piano':
            S.caja('madera_oscura', x0, yb, z0, x1, yb + 1.0, z1)
        elif tipo == 'estatua':
            S.caja(tex or 'marmol_pared', x0, yb, z0, x1, yb + 0.9, z1); cx, cz = (x0 + x1) / 2, (z0 + z1) / 2
            S.caja(tex or 'marmol_pared', cx - 0.25, yb + 0.9, cz - 0.25, cx + 0.25, yb + h, cz + 0.25, colision=False)
        elif tipo == 'tanque':
            S.caja(tex or 'lab_metal', x0, yb, z0, x1, yb + h, z1)
        elif tipo == 'consola':
            S.caja(tex or 'lab_panel', x0, yb, z0, x1, yb + h, z1)
        elif tipo == 'arbol':
            cx, cz = (x0 + x1) / 2, (z0 + z1) / 2
            S.caja('madera_tosca', cx - 0.2, yb, cz - 0.2, cx + 0.2, yb + h, cz + 0.2)
        elif tipo == 'agua':
            S.quad('rejilla' if tex is None else tex, [(x0, yb + h, z0), (x0, yb + h, z1), (x1, yb + h, z1), (x1, yb + h, z0)])
            S._colcaja(x0, z0, x1, z1, yb, 1.2)
        elif tipo == 'chimenea':
            S.caja('castillo_piedra', x0, yb, z0, x1, yb + h, z1)
    # velas / candelabros: (x, y, z) punta de la llama; se dibuja un candelero de latón
    for v in spec.get('velas', []):
        x, y, z = v[:3]; base = v[3] if len(v) > 3 else None
        S.llamas.append((x * 1000, y * 1000, z * 1000))
        S.caja('laton', x - 0.03, y - 0.35, z - 0.03, x + 0.03, y - 0.02, z + 0.03, colision=False)
        if base is not None and base < y - 0.35: S.caja('laton', x - 0.015, base, z - 0.015, x + 0.015, y - 0.35, z + 0.015, colision=False)
    for v in spec.get('lamparas', []):
        x, y, z = v[:3]; S.lamparas.append((x * 1000, y * 1000, z * 1000))
        S.caja('lab_panel' if 'lab_panel' in TEX else 'laton', x - 0.3, y, z - 0.08, x + 0.3, y + 0.05, z + 0.08, colision=False)
    # cuadros: (celda, lado, pos, ancho, alto, y, tex)
    for q in spec.get('cuadros', []):
        cid, l, pos, w, h, yq, tex = q; c = cel[cid]
        a, b, u, n = pos_lado(c, l, pos); cen = a + u * pos + n * 0.02
        p0 = cen - u * w / 2; p1 = cen + u * w / 2; yy = c['y'] + yq
        pts = [(p0[0], yy, p0[1]), (p1[0], yy, p1[1]), (p1[0], yy + h, p1[1]), (p0[0], yy + h, p0[1])]
        nn = np.cross(np.subtract(pts[1], pts[0]), np.subtract(pts[3], pts[0]))
        uv = [[0, 0], [1, 0], [1, 1], [0, 1]]
        if nn[0] * n[0] + nn[2] * n[1] < 0: pts = [pts[1], pts[0], pts[3], pts[2]]; uv = [[1, 0], [0, 0], [0, 1], [1, 1]]
        S.quad(tex, pts, uv=uv)
    return S

def _colcaja(self, x0, z0, x1, z1, y0, h):
    for P in ([(x0, y0, z0), (x1, y0, z0), (x1, y0 + h, z0), (x0, y0 + h, z0)], [(x1, y0, z0), (x1, y0, z1), (x1, y0 + h, z1), (x1, y0 + h, z0)],
              [(x1, y0, z1), (x0, y0, z1), (x0, y0 + h, z1), (x1, y0 + h, z1)], [(x0, y0, z1), (x0, y0, z0), (x0, y0 + h, z0), (x0, y0 + h, z1)]):
        P = np.array(P, float); self.col.append((2, P[[0, 1, 2]])); self.col.append((2, P[[0, 2, 3]]))
Suite._colcaja = _colcaja
