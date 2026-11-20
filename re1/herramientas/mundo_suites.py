"""Salas generadas del remake de RE1 (lo que UC no tiene). Metros, marco propio de cada suite.
Cada puerta lleva un id; los enlaces entre puertas están en mundo.py."""

def P(id, celda, lado, pos, **k):
    d = dict(id=id, celda=celda, lado=lado, pos=pos, destino=None); d.update(k); return d

def velas_pared(celda_r, y, lado, n, margen=1.0):
    x0, z0, x1, z1 = celda_r; out = []
    for i in range(n):
        t = (i + 1) / (n + 1)
        if lado == 'N': out.append((x0 + (x1 - x0) * t, y, z1 - 0.15))
        if lado == 'S': out.append((x0 + (x1 - x0) * t, y, z0 + 0.15))
        if lado == 'E': out.append((x1 - 0.15, y, z0 + (z1 - z0) * t))
        if lado == 'O': out.append((x0 + 0.15, y, z0 + (z1 - z0) * t))
    return out

SUITES = []
def S(**k): SUITES.append(k); return k

# ---------------------------------------------------------------- MANSIÓN 1F oeste
S(nombre='te_bar', titulo='Sala de té, bar, escalera oeste exterior y cocina (B1)', estilo='verde',
  celdas=[dict(id='te', r=(0, 0, 9, 7), h=3.4, alfombra=(2.5, 1.5, 6.5, 5.5)),
          dict(id='bar', r=(9, 0, 17, 7), h=3.4, estilo='rojo', alfombra=(10.5, 2, 15.5, 5)),
          dict(id='esc', r=(0, 7, 4, 15), y=-3.2, h=6.6, estilo='servicio'),
          dict(id='coc', r=(4, 9, 16, 15), y=-3.2, h=3.0, estilo='servicio')],
  pasos=[('te', 'E', 3.5, 1.8), ('bar', 'O', 3.5, 1.8), ('te', 'N', 2.0, 1.6), ('esc', 'S', 2.0, 1.6), ('esc', 'E', 6.8, 2.2, 2.6), ('coc', 'O', 4.8, 2.2)],
  escaleras=[((0.2, 7.0, 3.8, 12.6), -3.2, 0.0, 'S', 'servicio')],
  puertas=[P('comedor', 'te', 'S', 4.5, doble=True), P('norte', 'te', 'O', 3.5), P('sotano', 'coc', 'E', 3.0, tex='castillo_puerta')],
  muebles=[('mesa', 3.5, 2.5, 5.5, 4.5, 0.75), ('estante', 0.1, 0.5, 0.6, 2.5, 2.2), ('piano', 13.5, 4.8, 16.5, 6.6, 1.0),
           ('mesa', 10.0, 0.4, 16.5, 1.2, 1.05), ('estante', 9.2, 6.3, 12.0, 6.9, 2.2, 'estante2'),
           ('mesa', 6.0, 11.0, 12.0, 12.5, 0.9, None, -3.2), ('caja', 13.0, 13.8, 15.8, 14.9, 1.8, 'madera_oscura', -3.2)],
  velas=[(4.5, 1.15, 3.5, 0.75)] + velas_pared((0, 0, 9, 7), 2.1, 'O', 2) + velas_pared((9, 0, 17, 7), 2.1, 'N', 2) + [(8.0, -1.2, 11.7)],
  cuadros=[('te', 'N', 6.5, 1.4, 1.0, 1.5, 'cuadro1'), ('bar', 'E', 3.5, 1.0, 1.3, 1.3, 'retrato')])

S(nombre='norte', titulo='Pasillo norte, sala del tigre, dormitorio del investigador, invernadero, escalera oeste interior, botiquín y trastero', estilo='oliva',
  celdas=[dict(id='pas', r=(0, 0, 3, 22), h=3.2),
          dict(id='tig', r=(3, 0, 10, 6), h=3.2, estilo='rojo', alfombra=(4.5, 1.5, 8.5, 4.5)),
          dict(id='inv', r=(3, 8, 12, 15), h=4.0, estilo='jardin', techo=True, tex=dict(techo='ventana', pared='muro_ladrillo'), sin_cielo=True),
          dict(id='dor', r=(-7, 0, 0, 6), h=3.0, estilo='beige', alfombra=(-5.5, 1, -1.5, 5)),
          dict(id='esc', r=(-7, 14, 0, 22), h=6.6, estilo='servicio'),
          dict(id='arr', r=(-7, 22, 0, 25), y=3.3, h=3.0, estilo='servicio'),
          dict(id='bot', r=(-11, 22, -7, 25), y=3.3, h=3.0, estilo='servicio'),
          dict(id='tra', r=(0, 22, 4, 25), y=3.3, h=3.0, estilo='servicio')],
  pasos=[('pas', 'E', 3.0, 1.4), ('tig', 'O', 3.0, 1.4), ('pas', 'E', 11.5, 1.4), ('inv', 'O', 3.5, 1.4), ('pas', 'O', 3.0, 1.2), ('dor', 'E', 3.0, 1.2),
         ('pas', 'O', 18.0, 2.4), ('esc', 'E', 4.0, 2.4), ('esc', 'N', 3.5, 3.0), ('arr', 'S', 3.5, 3.0), ('arr', 'O', 1.5, 1.1), ('bot', 'E', 1.5, 1.1),
         ('arr', 'E', 1.5, 1.1), ('tra', 'O', 1.5, 1.1)],
  escaleras=[((-6.8, 15.0, -3.5, 22.0), 0.0, 3.3, 'N', 'servicio')],
  puertas=[P('te', 'pas', 'S', 1.5), P('vestibulo', 'pas', 'N', 1.5)],
  muebles=[('estatua', 6.0, 2.5, 7.2, 3.7, 2.2, 'laton'), ('cama', -6.6, 3.5, -4.6, 5.8, 0.5), ('mesa', -2.5, 0.3, -0.5, 1.2, 0.78),
           ('estante', -1.2, 4.0, -0.1, 5.8, 2.0), ('caja', 4.0, 13.5, 6.0, 14.5, 0.8, 'madera_tosca'), ('caja', 9.0, 9.0, 11.5, 10.0, 0.8, 'madera_tosca'),
           ('estante', -10.8, 24.3, -7.4, 24.9, 2.0, 'estante2', 3.3), ('caja', 0.4, 23.6, 2.0, 24.8, 1.0, 'madera_tosca', 3.3)],
  velas=velas_pared((0, 0, 3, 22), 2.1, 'E', 3) + [(6.6, 2.4, 3.1)] + velas_pared((-7, 0, 0, 6), 2.0, 'O', 1) + [(-0.6, 1.1, 0.7, 0.78)],
  cuadros=[('pas', 'O', 8.0, 1.0, 1.3, 1.3, 'cuadro2'), ('tig', 'N', 5.0, 1.6, 1.1, 1.4, 'cuadro3')])

# ---------------------------------------------------------------- MANSIÓN 1F este
S(nombre='arte', titulo='Sala de arte y sala de los espejos', estilo='marmol',
  celdas=[dict(id='art', r=(0, 0, 10, 8), h=4.0, alfombra=(2, 2, 8, 6)), dict(id='esp', r=(10, 0, 16, 8), h=4.0, estilo='crema')],
  pasos=[('art', 'E', 4.0, 1.6), ('esp', 'O', 4.0, 1.6)],
  puertas=[P('entrada', 'art', 'O', 4.0, doble=True)],
  muebles=[('estatua', 4.3, 3.3, 5.7, 4.7, 2.3), ('columna', 0.3, 0.3, 0.9, 0.9, 4.0), ('columna', 9.1, 0.3, 9.7, 0.9, 4.0),
           ('columna', 0.3, 7.1, 0.9, 7.7, 4.0), ('columna', 9.1, 7.1, 9.7, 7.7, 4.0)],
  velas=velas_pared((0, 0, 10, 8), 2.2, 'N', 2) + velas_pared((0, 0, 10, 8), 2.2, 'S', 2) + [(13.0, 2.2, 7.85)],
  cuadros=[('art', 'N', 5.0, 2.2, 1.5, 1.4, 'cuadro1'), ('art', 'S', 5.0, 2.2, 1.5, 1.4, 'cuadro3'), ('esp', 'E', 2.5, 1.2, 2.2, 0.4, 'marmol_pared'),
           ('esp', 'E', 5.5, 1.2, 2.2, 0.4, 'marmol_pared')])

S(nombre='oscuro', titulo='Pasillo oscuro, estudio del patio y galería grande', estilo='gris',
  celdas=[dict(id='pas', r=(0, 0, 3, 18), h=3.2), dict(id='est', r=(3, 0, 10, 6), h=3.2, estilo='madera', alfombra=(4.5, 1.5, 8.5, 4.5)),
          dict(id='gal', r=(-12, 6, 0, 18), h=4.5, estilo='crema', alfombra=(-9, 9, -3, 15))],
  pasos=[('pas', 'E', 3.0, 1.2), ('est', 'O', 3.0, 1.2), ('pas', 'O', 12.0, 1.6), ('gal', 'E', 6.0, 1.6)],
  puertas=[P('entrada', 'pas', 'S', 1.5), P('cementerio', 'gal', 'O', 6.0, doble=True), P('techado', 'pas', 'N', 1.5)],
  muebles=[('mesa', 5.0, 2.0, 7.5, 3.5, 0.78), ('estante', 9.3, 0.5, 9.9, 5.5, 2.2), ('estante', 3.2, 5.3, 6.0, 5.9, 2.2, 'estante2'),
           ('estatua', -6.6, 11.4, -5.4, 12.6, 2.4)],
  velas=velas_pared((0, 0, 3, 18), 2.1, 'E', 2) + [(6.2, 1.15, 2.7, 0.78)] + velas_pared((-12, 6, 0, 18), 2.3, 'N', 3) + velas_pared((-12, 6, 0, 18), 2.3, 'S', 2),
  cuadros=[('gal', 'N', 2.5, 1.8, 1.4, 1.5, 'cuadro1'), ('gal', 'N', 6.0, 1.8, 1.4, 1.5, 'cuadro2'), ('gal', 'N', 9.5, 1.8, 1.4, 1.5, 'cuadro3'),
           ('gal', 'S', 3.0, 1.6, 1.2, 1.5, 'retrato'), ('gal', 'S', 9.0, 1.6, 1.2, 1.5, 'cuadro2')])

S(nombre='cementerio', titulo='Cementerio, cripta y pasillos de hormigón', estilo='jardin',
  celdas=[dict(id='cem', r=(0, 0, 16, 14), h=3.8, estilo='jardin', tex=dict(suelo='tierra')),
          dict(id='baj', r=(6, 14, 10, 22), y=-4.0, h=7.8, estilo='cripta', techo=False, tex=dict()),
          dict(id='cri', r=(2, 22, 14, 30), y=-4.0, h=3.6, estilo='cripta'),
          dict(id='hor', r=(14, 24, 24, 27), y=-4.0, h=3.0, estilo='sotano')],
  pasos=[('cem', 'N', 8.0, 4.0, 4.0), ('baj', 'S', 2.0, 4.0, 3.8), ('baj', 'N', 2.0, 4.0), ('cri', 'S', 6.0, 4.0), ('cri', 'E', 3.5, 2.0), ('hor', 'O', 1.5, 2.0)],
  escaleras=[((6.2, 14.0, 9.8, 21.8), -4.0, 0.0, 'S', 'cripta')],
  puertas=[P('galeria', 'cem', 'S', 8.0, doble=True, tex='castillo_puerta'), P('altar', 'hor', 'E', 1.5, tex='castillo_puerta')],
  muebles=[('lapida', 2, 3, 3.2, 3.4, 1.2), ('lapida', 5, 3, 6.2, 3.4, 1.0), ('lapida', 10, 3, 11.2, 3.4, 1.3), ('lapida', 13, 3, 14.2, 3.4, 1.1),
           ('lapida', 2, 8, 3.2, 8.4, 1.1), ('lapida', 13, 8, 14.2, 8.4, 1.2), ('lapida', 3.5, 11, 4.7, 11.4, 0.9), ('lapida', 11.5, 11, 12.7, 11.4, 1.0),
           ('arbol', 0.5, 12.5, 1.5, 13.5, 4.5), ('arbol', 14.5, 0.5, 15.5, 1.5, 4.5),
           ('lapida', 6.5, 26, 9.5, 28, 0.9, 'castillo_piedra', -4.0), ('lapida', 3, 23, 4.5, 29, 1.6, 'cripta2', -4.0), ('lapida', 11.5, 23, 13, 29, 1.6, 'cripta2', -4.0)],
  velas=[(8.0, -2.2, 21.85), (2.3, -2.0, 26.0), (13.7, -2.0, 26.0), (8.0, -2.0, 29.85), (8.0, 2.8, 0.2)])

S(nombre='techado', titulo='Pasillo techado y cobertizo del jardín', estilo='patio',
  celdas=[dict(id='pas', r=(0, 0, 3, 16), h=3.4, estilo='patio', techo=True, tex=dict(techo='pueblo_tablas'), sin_cielo=False),
          dict(id='cob', r=(-3, 16, 6, 24), h=3.0, estilo='cabana')],
  pasos=[('pas', 'N', 1.5, 2.0), ('cob', 'S', 4.5, 2.0)],
  puertas=[P('oscuro', 'pas', 'S', 1.5), P('patio', 'cob', 'N', 4.5, tex='puerta_cabana')],
  muebles=[('caja', -2.8, 16.2, -1.0, 17.4, 1.0), ('caja', 4.0, 22.5, 5.8, 23.8, 1.4), ('estante', -2.9, 20.0, -2.3, 23.5, 2.0, 'pueblo_tablas'),
           ('mesa', 1.0, 21.5, 3.0, 23.0, 0.85, 'pueblo_madera')],
  velas=[(1.5, 2.9, 6.0), (1.5, 2.9, 12.0), (2.0, 1.25, 22.3, 0.85)])

S(nombre='bano', titulo='Pasillo sinuoso, baño y caldera exterior', estilo='beige',
  celdas=[dict(id='pas', r=(0, 0, 3, 10), h=3.2), dict(id='pa2', r=(3, 7, 12, 10), h=3.2),
          dict(id='ban', r=(-6, 2, 0, 8), h=3.0, estilo='servicio', tex=dict(suelo='azulejo_lab')),
          dict(id='cal', r=(12, 4, 18, 12), h=3.6, estilo='patio', techo=True, tex=dict(techo='pueblo_tablas'))],
  pasos=[('pas', 'E', 8.5, 2.9, 3.2), ('pa2', 'O', 1.5, 2.9, 3.2), ('pas', 'O', 4.0, 1.1), ('ban', 'E', 2.0, 1.1), ('pa2', 'E', 1.5, 1.1), ('cal', 'O', 4.5, 1.1)],
  puertas=[P('entrada', 'pas', 'S', 1.5), P('salon', 'pa2', 'N', 6.0)],
  muebles=[('caja', -5.5, 6.0, -3.5, 7.7, 0.6, 'azulejo_lab'), ('caja', -0.8, 2.3, -0.2, 3.0, 0.9, 'azulejo_lab'), ('tanque', 14.0, 9.0, 17.5, 11.5, 2.4, 're4_metal'),
           ('caja', 16.5, 4.5, 17.8, 6.0, 1.2, 're4_metal2')],
  velas=velas_pared((0, 0, 3, 10), 2.1, 'E', 1) + velas_pared((3, 7, 12, 10), 2.1, 'N', 2), lamparas=[(15.0, 3.3, 8.0)],
  cuadros=[('pas', 'O', 7.5, 0.9, 1.2, 1.3, 'cuadro3')])
# la caldera es otra celda de la misma sala: las dos puertas se enlazan entre sí (cal_in <-> caldera)

S(nombre='salon', titulo='Sala del techo trampa y sala de estar', estilo='crema',
  celdas=[dict(id='tra', r=(0, 0, 6, 6), h=3.0, estilo='gris'), dict(id='sal', r=(6, -2, 16, 8), h=3.6, alfombra=(8, 0.5, 14, 5.5))],
  pasos=[('tra', 'E', 3.0, 1.1), ('sal', 'O', 5.0, 1.1)],
  puertas=[P('entrada', 'tra', 'S', 3.0), P('bano', 'sal', 'N', 5.0)],
  muebles=[('mesa', 9.5, 2.0, 12.5, 4.0, 0.5), ('caja', 8.5, 5.8, 13.5, 6.8, 0.8, 'tela'), ('chimenea', 15.0, 1.0, 15.9, 5.0, 1.4),
           ('estante', 0.2, 4.5, 2.8, 5.8, 1.9, 'estante2'), ('caja', 3.0, 0.3, 5.5, 1.3, 1.0, 'madera_oscura')],
  velas=[(11.0, 0.65, 3.0, 0.5), (15.4, 1.75, 1.4), (15.4, 1.75, 4.6)] + velas_pared((0, 0, 6, 6), 2.0, 'O', 1),
  cuadros=[('sal', 'E', 3.0, 1.2, 1.0, 1.7, 'retrato'), ('sal', 'S', 5.0, 1.6, 1.1, 1.5, 'cuadro2')])

# ---------------------------------------------------------------- MANSIÓN 2F
S(nombre='pasillo_c', titulo="Pasillo en C, sala de descanso, biblioteca pequeña y comedor pequeño", estilo='verde',
  celdas=[dict(id='c1', r=(0, 0, 3, 14), h=3.2), dict(id='c2', r=(3, 11, 14, 14), h=3.2), dict(id='c3', r=(14, 0, 17, 14), h=3.2),
          dict(id='des', r=(3, 0, 9, 6), h=3.0, estilo='beige', alfombra=(4, 1, 8, 5)), dict(id='bib', r=(17, 4, 25, 12), h=3.6, estilo='madera'),
          dict(id='com', r=(6, 14, 13, 20), h=3.2, estilo='rojo', alfombra=(7, 15, 12, 19))],
  pasos=[('c1', 'E', 12.5, 2.9, 3.2), ('c2', 'O', 1.5, 2.9, 3.2), ('c2', 'E', 1.5, 2.9, 3.2), ('c3', 'O', 12.5, 2.9, 3.2),
         ('c1', 'E', 3.0, 1.1), ('des', 'O', 3.0, 1.1), ('c3', 'E', 8.0, 1.2), ('bib', 'O', 4.0, 1.2), ('c2', 'N', 6.5, 1.2), ('com', 'S', 3.5, 1.2)],
  puertas=[P('entrada', 'c1', 'S', 1.5), P('balcon', 'c3', 'S', 1.5)],
  muebles=[('cama', 4.0, 3.5, 6.0, 5.8, 0.5), ('mesa', 6.8, 0.3, 8.6, 1.2, 0.78), ('estante', 17.2, 4.2, 24.8, 4.8, 3.0), ('estante', 17.2, 11.2, 24.8, 11.8, 3.0, 'estante2'),
           ('mesa', 20.0, 7.0, 22.5, 9.0, 0.78), ('mesa', 7.8, 16.5, 11.2, 18.0, 0.78)],
  velas=velas_pared((0, 0, 3, 14), 2.1, 'O', 2) + velas_pared((3, 11, 14, 14), 2.1, 'N', 2) + velas_pared((14, 0, 17, 14), 2.1, 'E', 1) +
        [(21.2, 1.15, 8.0, 0.78), (9.5, 1.15, 17.2, 0.78), (7.6, 1.1, 0.7, 0.78)],
  cuadros=[('c2', 'S', 5.5, 1.2, 1.0, 1.4, 'cuadro1'), ('com', 'N', 3.5, 1.6, 1.0, 1.5, 'cuadro3')])

S(nombre='balcones', titulo='Balcón exterior y terraza', estilo='patio',
  celdas=[dict(id='bal', r=(0, 0, 14, 4), h=3.0, estilo='patio', tex=dict(pared='muro_piedra')), dict(id='ter', r=(14, -6, 22, 4), h=3.0, estilo='patio')],
  pasos=[('bal', 'E', 2.0, 3.0), ('ter', 'O', 8.0, 3.0)],
  puertas=[P('pasillo_c', 'bal', 'O', 2.0), P('ascensor', 'ter', 'S', 4.0, tex='puerta2')],
  muebles=[('caja', 3, 3.6, 11, 4.0, 1.0, 'muro_piedra'), ('caja', 16, -5.5, 17.5, -4.5, 0.8, 'losa_ext'), ('arbol', 20.5, 2.5, 21.5, 3.5, 3.0)],
  velas=[(7.0, 2.4, 0.15), (18.0, 2.4, 3.85)])

S(nombre='ciervo', titulo='Sala del ciervo, pasaje de la muerte y ático', estilo='madera',
  celdas=[dict(id='cie', r=(0, 0, 8, 7), h=3.6, alfombra=(2, 1.5, 6, 5.5)), dict(id='pas', r=(8, 2, 20, 5), h=3.0, estilo='gris'),
          dict(id='ent', r=(20, 0, 24, 7), h=3.0, estilo='servicio'), dict(id='ati', r=(24, -4, 36, 11), h=4.5, estilo='servicio', tex=dict(techo='pueblo_tablas'))],
  pasos=[('cie', 'E', 3.5, 1.2), ('pas', 'O', 1.5, 1.2), ('pas', 'E', 1.5, 1.6), ('ent', 'O', 3.5, 1.6), ('ent', 'E', 3.5, 1.4), ('ati', 'O', 7.5, 1.4)],
  puertas=[P('entrada', 'cie', 'O', 3.5)],
  muebles=[('mesa', 3, 2.5, 5, 4.5, 0.78), ('estante', 0.2, 0.3, 0.8, 3.0, 2.2), ('caja', 26, -3.5, 28, -2, 1.2), ('caja', 33, 8, 35.5, 10.5, 1.6),
           ('caja', 29, 4, 31, 5.5, 0.9), ('caja', 25, 9, 26.5, 10.5, 1.1)],
  velas=[(4.0, 1.15, 3.5, 0.78), (7.85, 2.2, 1.0), (7.85, 2.2, 6.0), (14.0, 2.4, 2.15), (30.0, 3.6, -3.85)],
  cuadros=[('cie', 'N', 4.0, 1.6, 1.2, 1.8, 'cuadro2'), ('pas', 'N', 6.0, 1.4, 1.0, 1.3, 'retrato')])

S(nombre='dormitorio', titulo='Dormitorio y estudio del guarda', estilo='beige',
  celdas=[dict(id='dor', r=(0, 0, 8, 6), h=3.0, alfombra=(1.5, 1, 6.5, 5)), dict(id='est', r=(8, 0, 13, 6), h=3.0, estilo='madera')],
  pasos=[('dor', 'E', 3.0, 1.1), ('est', 'O', 3.0, 1.1)],
  puertas=[P('entrada', 'dor', 'O', 3.0)],
  muebles=[('cama', 1.0, 3.5, 3.0, 5.8, 0.5), ('mesa', 5.5, 4.5, 7.5, 5.7, 0.78), ('estante', 12.3, 0.3, 12.9, 5.7, 2.2), ('mesa', 9.5, 2.0, 11.5, 3.5, 0.78)],
  velas=[(6.5, 1.1, 5.1, 0.78), (10.5, 1.1, 2.7, 0.78), (0.15, 2.0, 1.5)],
  cuadros=[('dor', 'S', 4.0, 1.2, 0.9, 1.4, 'cuadro3')])

S(nombre='ascensor', titulo='Pasillo del ascensor, sala de las columnas, sala de materiales, sala de la trampa y pasaje secreto', estilo='crema',
  celdas=[dict(id='pas', r=(0, 0, 3, 16), h=3.2), dict(id='col', r=(3, 10, 12, 16), h=3.8, estilo='marmol'),
          dict(id='mat', r=(-6, 0, 0, 6), h=3.0, estilo='servicio'), dict(id='tra', r=(3, 0, 9, 6), h=3.0, estilo='gris'),
          dict(id='sec', r=(9, 2, 17, 4), h=2.6, estilo='sotano')],
  pasos=[('pas', 'E', 13.0, 1.6), ('col', 'O', 3.0, 1.6), ('pas', 'O', 3.0, 1.1), ('mat', 'E', 3.0, 1.1), ('pas', 'E', 3.0, 1.1), ('tra', 'O', 3.0, 1.1),
         ('tra', 'E', 3.0, 1.2, 2.4), ('sec', 'O', 1.0, 1.2, 2.4)],
  puertas=[P('entrada', 'pas', 'N', 1.5), P('balcones', 'col', 'E', 3.0, tex='puerta2'), P('ascensor', 'pas', 'S', 1.5, tex='lab_puerta')],
  muebles=[('columna', 5.0, 12.0, 5.8, 12.8, 3.8), ('columna', 9.0, 12.0, 9.8, 12.8, 3.8), ('columna', 7.0, 14.2, 7.8, 15.0, 3.8),
           ('estante', -5.8, 0.2, -0.2, 0.8, 2.2, 'estante2'), ('caja', -5.5, 4.0, -3.5, 5.8, 1.0), ('caja', 5.0, 2.5, 7.0, 3.5, 0.8, 'madera_oscura')],
  velas=velas_pared((0, 0, 3, 16), 2.1, 'O', 1) + [(12 - 0.15, 2.4, 13.0), (7.4, 2.6, 10.15), (16.8, 1.8, 3.0)],
  cuadros=[('pas', 'E', 8.0, 0.9, 1.2, 1.3, 'cuadro1')])

S(nombre='espejos', titulo='Pasillo de los espejos y sala de trofeos', estilo='rojo',
  celdas=[dict(id='pas', r=(0, 0, 3, 14), h=3.2), dict(id='tro', r=(3, 6, 12, 14), h=3.6, estilo='madera', alfombra=(5, 8, 10, 12))],
  pasos=[('pas', 'E', 10.0, 1.4), ('tro', 'O', 4.0, 1.4)],
  puertas=[P('entrada', 'pas', 'S', 1.5)],
  muebles=[('estante', 11.3, 6.5, 11.9, 13.5, 2.4), ('mesa', 6.0, 9.0, 9.0, 11.0, 0.78), ('estatua', 3.5, 12.6, 4.5, 13.6, 1.9, 'laton')],
  velas=velas_pared((0, 0, 3, 14), 2.1, 'E', 1) + velas_pared((0, 0, 3, 14), 2.1, 'O', 2) + [(7.5, 1.15, 10.0, 0.78), (11.85, 2.5, 7.0)],
  cuadros=[('pas', 'O', 3.5, 1.0, 2.0, 0.4, 'marmol_pared'), ('pas', 'O', 10.5, 1.0, 2.0, 0.4, 'marmol_pared'), ('tro', 'N', 4.5, 1.6, 1.2, 1.8, 'retrato')])

S(nombre='altar', titulo='Escalera bajo el vestíbulo y tumba de Jessica', estilo='cripta',
  celdas=[dict(id='esc', r=(0, 0, 3, 12), y=-6.0, h=9.0, techo=False), dict(id='pas', r=(0, 12, 3, 20), y=-6.0, h=3.2),
          dict(id='tum', r=(-5, 20, 8, 32), y=-6.0, h=6.0, estilo='cripta')],
  pasos=[('esc', 'N', 1.5, 3.0), ('pas', 'S', 1.5, 3.0), ('pas', 'N', 1.5, 3.0), ('tum', 'S', 6.5, 3.0)],
  escaleras=[((0.2, 0.0, 2.8, 11.8), -6.0, 0.0, 'S', 'cripta')],
  puertas=[P('vestibulo', 'esc', 'S', 1.5, tex='castillo_puerta'), P('cripta', 'tum', 'O', 6.0, tex='castillo_puerta')],
  muebles=[('lapida', -0.5, 25, 3.5, 27.5, 1.0, 'cripta2', -6.0), ('columna', -4, 21, -3.2, 21.8, 6.0, 'cripta', -6.0), ('columna', 6.2, 21, 7.0, 21.8, 6.0, 'cripta', -6.0),
           ('columna', -4, 30, -3.2, 30.8, 6.0, 'cripta', -6.0), ('columna', 6.2, 30, 7.0, 30.8, 6.0, 'cripta', -6.0)],
  velas=[(1.5, -2.5, 11.85), (-0.2, -4.8, 26.2), (3.2, -4.8, 26.2), (1.5, -3.5, 31.85), (-4.85, -3.8, 26), (7.85, -3.8, 26)])

# ---------------------------------------------------------------- PATIO / BOSQUE
S(nombre='piscina', titulo='Piscina, camino en zigzag y cascada', estilo='jardin',
  celdas=[dict(id='z1', r=(0, 0, 4, 14), h=3.5, estilo='camino'), dict(id='z2', r=(4, 10, 16, 14), h=3.5, estilo='camino'),
          dict(id='pis', r=(16, 4, 30, 20), h=3.5, estilo='patio'), dict(id='cas', r=(30, 8, 38, 16), h=6.0, estilo='jardin', tex=dict(pared='roca'))],
  pasos=[('z1', 'E', 12.0, 3.9, 3.5), ('z2', 'O', 2.0, 3.9, 3.5), ('z2', 'E', 2.0, 4.0, 3.5), ('pis', 'O', 8.0, 4.0, 3.5), ('pis', 'E', 8.0, 6.0, 3.5), ('cas', 'O', 4.0, 6.0, 3.5)],
  puertas=[P('patio', 'z1', 'S', 2.0, tex='castillo_puerta'), P('residencia', 'pis', 'N', 7.0, doble=True, tex='puerta_cabana'), P('cabana', 'cas', 'E', 4.0, tex='puerta_cabana')],
  muebles=[('agua', 19.5, 7.5, 26.5, 16.5, 0.0, 'rejilla'), ('arbol', 1, 1, 2, 2, 5), ('arbol', 12, 12.5, 13, 13.5, 5), ('arbol', 28, 18, 29, 19, 5),
           ('caja', 31, 14.5, 37.5, 15.9, 2.5, 'roca')],
  velas=[(2.0, 2.6, 13.8), (16.15, 2.6, 6.0), (29.85, 2.6, 18.0)])

S(nombre='cabana', titulo='Sendero del bosque, cabaña y lápida pequeña', estilo='camino',
  celdas=[dict(id='sen', r=(0, 0, 4, 20), h=3.5), dict(id='cab', r=(-6, 20, 6, 28), h=3.0, estilo='cabana'), dict(id='lap', r=(4, 6, 12, 12), h=3.5, estilo='jardin')],
  pasos=[('sen', 'N', 2.0, 1.4), ('cab', 'S', 8.0, 1.4), ('sen', 'E', 9.0, 3.0, 3.5), ('lap', 'O', 3.0, 3.0, 3.5)],
  puertas=[P('cascada', 'sen', 'S', 2.0, tex='castillo_puerta'), P('cuevas', 'cab', 'O', 4.0, tex='puerta_cabana')],
  muebles=[('mesa', -3, 22, -0.5, 23.5, 0.8, 'pueblo_madera'), ('cama', 2.5, 25.5, 5.5, 27.6, 0.5), ('caja', -5.6, 26.5, -4, 27.6, 1.0),
           ('lapida', 7.5, 8.5, 8.7, 9.0, 1.0), ('arbol', 10, 10, 11, 11, 5), ('arbol', 0.5, 15, 1.5, 16, 5)],
  velas=[(-1.7, 1.2, 22.7, 0.8), (5.8, 2.0, 21.0), (2.0, 2.6, 0.2)])

S(nombre='cuevas_b1', titulo='Cuevas B1: pasajes, sala del generador, sala de la araña y sala de Enrico', estilo='cueva',
  celdas=[dict(id='p1', r=(0, 0, 3, 16), h=3.0), dict(id='gen', r=(3, 10, 11, 18), h=3.5, estilo='sotano'), dict(id='p2', r=(-12, 13, 0, 16), h=3.0),
          dict(id='ara', r=(-22, 8, -12, 22), h=6.0), dict(id='enr', r=(-6, 0, 0, 6), h=4.0)],
  pasos=[('p1', 'E', 13.5, 1.6), ('gen', 'O', 3.5, 1.6), ('p1', 'O', 14.5, 2.4), ('p2', 'E', 1.5, 2.4), ('p2', 'O', 1.5, 2.4), ('ara', 'E', 6.5, 2.4),
         ('p1', 'O', 3.0, 2.0), ('enr', 'E', 3.0, 2.0)],
  puertas=[P('cueva_uc', 'p1', 'S', 1.5, tex='puerta_cabana'), P('b2', 'ara', 'O', 7.0, tex='puerta_cabana')],
  muebles=[('tanque', 6.0, 15.5, 10.5, 17.6, 1.8, 're4_metal'), ('caja', 3.5, 10.5, 5.0, 12.0, 1.2, 're4_metal2'), ('caja', -5.5, 0.5, -4.0, 2.0, 0.8),
           ('caja', -21, 9, -19, 11, 1.4), ('caja', -15, 19.5, -13, 21.5, 1.0)],
  lamparas=[(7.0, 3.2, 14.0)], velas=[(1.5, 2.2, 0.2), (-3.0, 2.4, 5.8), (-17.0, 3.0, 21.8), (-11.95, 2.4, 9.5)])

S(nombre='cuevas_b2', titulo='Cuevas B2: pasaje sinuoso, compactador de basura, almacén subterráneo y habitación de Lisa', estilo='cueva',
  celdas=[dict(id='w1', r=(0, 0, 3, 12), h=3.0), dict(id='w2', r=(3, 9, 14, 12), h=3.0), dict(id='bas', r=(14, 6, 22, 16), h=4.5, estilo='sotano'),
          dict(id='alm', r=(-8, 4, 0, 10), h=3.2, estilo='sotano'), dict(id='lis', r=(22, 8, 29, 14), h=3.0, estilo='cabana')],
  pasos=[('w1', 'E', 10.5, 2.9, 3.0), ('w2', 'O', 1.5, 2.9, 3.0), ('w2', 'E', 1.5, 2.4), ('bas', 'O', 4.5, 2.4), ('w1', 'O', 7.0, 1.8), ('alm', 'E', 3.0, 1.8),
         ('bas', 'E', 5.0, 1.1), ('lis', 'O', 3.0, 1.1)],
  puertas=[P('b1', 'w1', 'S', 1.5, tex='puerta_cabana')],
  muebles=[('caja', 15, 13, 21, 15.5, 2.0, 're4_metal'), ('caja', -7.5, 4.5, -5, 6, 1.2), ('caja', -7.5, 8, -4.5, 9.6, 1.6), ('estante', -3.5, 9.3, -0.3, 9.9, 2.0, 'pueblo_tablas'),
           ('cama', 26, 11.5, 28.8, 13.8, 0.4), ('mesa', 23, 8.3, 25, 9.5, 0.8, 'pueblo_madera')],
  velas=[(24.0, 1.2, 8.9, 0.8), (28.85, 2.0, 9.5), (1.5, 2.2, 0.2)], lamparas=[(18.0, 4.2, 11.0)])

# ---------------------------------------------------------------- RESIDENCIA
S(nombre='habitaciones', titulo='Habitaciones 001, 002 y 003 con sus baños', estilo='residencia',
  celdas=[dict(id='pas', r=(0, 0, 3, 18), h=3.0), dict(id='h1', r=(3, 0, 10, 6), h=3.0, alfombra=(4, 1, 9, 5)), dict(id='b1', r=(10, 0, 13, 3), h=3.0, estilo='servicio', tex=dict(suelo='azulejo_lab')),
          dict(id='h2', r=(3, 6, 10, 12), h=3.0, estilo='gris'), dict(id='b2', r=(10, 6, 13, 9), h=3.0, estilo='servicio', tex=dict(suelo='azulejo_lab')),
          dict(id='h3', r=(3, 12, 10, 18), h=3.0, estilo='beige'), dict(id='b3', r=(10, 12, 13, 15), h=3.0, estilo='servicio', tex=dict(suelo='azulejo_lab'))],
  pasos=[('pas', 'E', 3.0, 1.0), ('h1', 'O', 3.0, 1.0), ('pas', 'E', 9.0, 1.0), ('h2', 'O', 3.0, 1.0), ('pas', 'E', 15.0, 1.0), ('h3', 'O', 3.0, 1.0),
         ('h1', 'E', 1.5, 0.9), ('b1', 'O', 1.5, 0.9), ('h2', 'E', 1.5, 0.9), ('b2', 'O', 1.5, 0.9), ('h3', 'E', 1.5, 0.9), ('b3', 'O', 1.5, 0.9)],
  puertas=[P('residencia', 'pas', 'S', 1.5)],
  muebles=[('cama', 7.5, 3.5, 9.8, 5.8, 0.5), ('mesa', 4, 0.3, 6, 1.2, 0.78), ('cama', 7.5, 9.5, 9.8, 11.8, 0.5), ('estante', 3.2, 11.3, 6, 11.9, 2.0, 'estante2'),
           ('cama', 7.5, 15.5, 9.8, 17.8, 0.5), ('mesa', 4, 12.3, 6, 13.2, 0.78), ('caja', 11.5, 0.3, 12.8, 1.5, 0.6, 'azulejo_lab'),
           ('caja', 11.5, 6.3, 12.8, 7.5, 0.6, 'azulejo_lab'), ('caja', 11.5, 12.3, 12.8, 13.5, 0.6, 'azulejo_lab')],
  velas=[(5.0, 1.1, 0.75, 0.78), (5.0, 1.1, 12.75, 0.78), (2.85, 2.1, 9.0)], lamparas=[(1.5, 2.8, 4.0), (1.5, 2.8, 14.0)],
  cuadros=[('h1', 'N', 3.5, 1.0, 0.8, 1.4, 'cuadro2'), ('h2', 'S', 3.5, 1.0, 0.8, 1.4, 'cuadro1')])

S(nombre='residencia', titulo='Sala de recreo, galería, enfermería y almacén de la residencia', estilo='residencia',
  celdas=[dict(id='pas', r=(0, 0, 16, 3), h=3.0), dict(id='rec', r=(0, 3, 8, 11), h=3.2, estilo='madera', alfombra=(1.5, 4.5, 6.5, 9.5)),
          dict(id='gal', r=(8, 3, 16, 11), h=3.4, estilo='crema'), dict(id='med', r=(0, -6, 6, 0), h=3.0, estilo='lab'), dict(id='alm', r=(10, -5, 16, 0), h=3.0, estilo='servicio')],
  pasos=[('pas', 'N', 4.0, 1.4), ('rec', 'S', 4.0, 1.4), ('pas', 'N', 12.0, 1.4), ('gal', 'S', 4.0, 1.4), ('pas', 'S', 3.0, 1.1), ('med', 'N', 3.0, 1.1),
         ('pas', 'S', 13.0, 1.1), ('alm', 'N', 3.0, 1.1)],
  puertas=[P('entrada', 'pas', 'O', 1.5), P('salida', 'pas', 'E', 1.5)],
  muebles=[('mesa', 2.5, 6.0, 5.5, 8.0, 0.8, 'madera_oscura'), ('estante', 0.2, 10.3, 3, 10.9, 2.0, 'estante2'), ('estatua', 11.5, 6.5, 12.5, 7.5, 1.8, 'laton'),
           ('estante', 0.2, -5.8, 0.8, -1.0, 2.0, 'lab_panel'), ('cama', 3.5, -5.8, 5.8, -3.5, 0.6), ('caja', 10.5, -4.5, 12.5, -3, 1.4), ('caja', 13.5, -4.5, 15.5, -2.0, 1.8)],
  velas=[(4.0, 1.2, 7.0, 0.8), (15.85, 2.2, 7.0), (8.15, 2.2, 7.0)], lamparas=[(8.0, 2.8, 1.5), (3.0, 2.8, -3.0)],
  cuadros=[('gal', 'N', 2.0, 1.4, 1.0, 1.5, 'cuadro1'), ('gal', 'N', 6.0, 1.4, 1.0, 1.5, 'cuadro3'), ('gal', 'E', 4.0, 1.6, 1.2, 1.4, 'cuadro2')])

# ---------------------------------------------------------------- LABORATORIO
S(nombre='lab_entrada', titulo='Entrada del laboratorio, pasaje al helipuerto, sala del baúl, escalera y sala de datos visuales', estilo='lab',
  celdas=[dict(id='ent', r=(0, 0, 8, 8), h=3.4), dict(id='pas', r=(8, 3, 22, 6), h=3.0, estilo='lab_hormigon'),
          dict(id='esc', r=(0, 8, 4, 18), y=-4.0, h=7.4, estilo='lab_hormigon'), dict(id='baul', r=(4, 14, 10, 18), y=-4.0, h=3.0),
          dict(id='dat', r=(-8, 12, 0, 18), y=-4.0, h=3.2, estilo='lab')],
  pasos=[('ent', 'E', 4.5, 2.0), ('pas', 'O', 1.5, 2.0), ('ent', 'N', 2.0, 3.0), ('esc', 'S', 2.0, 3.0), ('esc', 'E', 8.0, 1.6, 2.6), ('baul', 'O', 2.0, 1.6),
         ('esc', 'O', 7.0, 1.6, 2.6), ('dat', 'E', 3.0, 1.6)],
  escaleras=[((0.2, 8.0, 3.8, 13.8), -4.0, 0.0, 'S', 'lab_hormigon')],
  puertas=[P('ascensor', 'ent', 'S', 4.0, tex='lab_puerta', doble=True), P('helipuerto', 'pas', 'E', 1.5, tex='lab_puerta'), P('b3', 'baul', 'E', 2.0, tex='lab_puerta')],
  muebles=[('consola', 0.2, 2.0, 0.9, 6.0, 1.2), ('caja', 6.5, 16.5, 9.8, 17.8, 0.9, 're4_metal'), ('consola', -7.8, 15.5, -2.0, 17.8, 1.5),
           ('tanque', 6.5, 0.3, 7.8, 1.6, 2.2)],
  lamparas=[(4.0, 3.3, 4.0), (15.0, 2.9, 4.5), (2.0, 3.2, 12.0), (-4.0, -0.9, 15.0), (7.0, -1.1, 16.0)])

S(nombre='lab_b3', titulo='Laboratorio B3: morgue, rayos X, quirófano, sala del cirujano, celda, pasillo de la clave y control de energía', estilo='lab',
  celdas=[dict(id='pas', r=(0, 0, 3, 30), h=3.0, estilo='lab_hormigon'),
          dict(id='mor', r=(3, 0, 11, 7), h=3.0, tex=dict(suelo='azulejo_lab')), dict(id='rx', r=(3, 8, 9, 14), h=3.0), dict(id='qui', r=(3, 15, 11, 22), h=3.2, tex=dict(suelo='azulejo_lab')),
          dict(id='cir', r=(-7, 2, 0, 9), h=3.0, estilo='residencia'), dict(id='cel', r=(-6, 12, 0, 18), h=3.0, estilo='sotano'),
          dict(id='ene', r=(-9, 22, 0, 30), h=3.6, estilo='lab_hormigon')],
  pasos=[('pas', 'E', 3.5, 1.4), ('mor', 'O', 3.5, 1.4), ('pas', 'E', 11.0, 1.2), ('rx', 'O', 3.0, 1.2), ('pas', 'E', 18.5, 1.4), ('qui', 'O', 3.5, 1.4),
         ('pas', 'O', 5.5, 1.1), ('cir', 'E', 3.5, 1.1), ('pas', 'O', 15.0, 1.1), ('cel', 'E', 3.0, 1.1), ('pas', 'O', 26.0, 1.6), ('ene', 'E', 4.0, 1.6)],
  puertas=[P('arriba', 'pas', 'S', 1.5, tex='lab_puerta'), P('b4', 'pas', 'N', 1.5, tex='lab_puerta', doble=True)],
  muebles=[('caja', 4, 0.3, 10.5, 1.4, 1.0, 're4_metal'), ('caja', 4, 5.6, 10.5, 6.7, 1.0, 're4_metal'), ('consola', 8.2, 9, 8.8, 13, 1.8),
           ('cama', 6, 17, 8.5, 19.5, 0.9), ('consola', 3.3, 21.2, 7, 21.8, 1.4), ('mesa', -6, 3, -4, 4.5, 0.78), ('estante', -6.8, 7.5, -3.5, 8.8, 2.0, 'estante2'),
           ('caja', -5.5, 16.5, -3.5, 17.7, 0.5, 'tela'), ('consola', -8.5, 28.5, -2, 29.6, 1.6), ('tanque', -8.5, 22.5, -6.5, 24.5, 2.6)],
  lamparas=[(1.5, 2.9, 5.0), (1.5, 2.9, 15.0), (1.5, 2.9, 25.0), (7.0, 2.9, 3.5), (7.0, 3.0, 18.5), (-4.5, 3.4, 26.0)], velas=[(-5.0, 1.1, 3.75, 0.78)])
