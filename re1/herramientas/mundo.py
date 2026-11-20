"""Mapa completo del remake de RE1 (H12): qué sala va en qué hueco de RE4 y cómo se enlazan las puertas.
Puntos de puerta:
  g:<suite>:<puerta>      sala generada (mundo_suites.py)
  m:<rUC>:<n>             puerta libre de una sala UC de la mansión (puertas_libres.json, n por orden)
  a:<rUC>:<letra>         sala UC de patio/cuevas/residencia/laboratorio (punto aproximado en metros de UC, se ajusta al suelo)
  v:<nombre>              puerta solo-AEV en una sala UC de la mansión (posición RE4 mm a mano)"""

# huecos de RE4: (fase, sala)
HUECO = {
    # mansión generada (fase 1)
    'te_bar': (1, 0x17), 'norte': (1, 0x18), 'arte': (1, 0x19), 'oscuro': (1, 0x1a), 'cementerio': (1, 0x1b),
    'techado': (1, 0x1c), 'bano': (1, 0x1d), 'salon': (1, 0x1e), 'pasillo_c': (1, 0x1f),
    # fase 2
    'balcones': (2, 0x00), 'ciervo': (2, 0x01), 'dormitorio': (2, 0x02), 'ascensor': (2, 0x03), 'espejos': (2, 0x04),
    'altar': (2, 0x05), 'piscina': (2, 0x06), 'cabana': (2, 0x07), 'cuevas_b1': (2, 0x08), 'cuevas_b2': (2, 0x09),
    'habitaciones': (2, 0x0a), 'residencia': (2, 0x0b), 'lab_entrada': (2, 0x0c), 'lab_b3': (2, 0x0d),
    # salas de UC fuera de la mansión (fase 2)
    'r116': (2, 0x0e), 'r117': (2, 0x0f), 'r118': (2, 0x10), 'r119': (2, 0x11), 'r120': (2, 0x12), 'r121': (2, 0x13),
    'r122': (2, 0x14), 'r123': (2, 0x15), 'r125': (2, 0x16), 'r126': (2, 0x17), 'r127': (2, 0x18), 'r128': (2, 0x19),
    'r130': (2, 0x1a), 'r133': (2, 0x1b), 'r134': (2, 0x1d), 'r135': (2, 0x20), 'r137': (2, 0x21), 'r138': (2, 0x22),
    'r139': (2, 0x23), 'r140': (2, 0x27), 'r142': (2, 0x25), 'r144': (2, 0x26),
}
NOMBRE = {
    'r116': 'Patio: entrada con fuente', 'r117': 'Patio: sendero', 'r118': 'Jardín principal (fuente, ascensor al laboratorio)',
    'r119': 'Patio: camino a la piscina', 'r120': 'Cuevas: entrada', 'r121': 'Cuevas: pasaje de las rocas', 'r122': 'Cuevas: sala de la estatua',
    'r123': 'Residencia: pasillo de entrada', 'r125': 'Residencia: pasillo central', 'r126': 'Residencia: almacén',
    'r127': 'Acuario B1: pasarela', 'r128': 'Acuario B2: tanque', 'r130': 'Residencia: sala de la planta 42',
    'r133': 'Laboratorio: pasillo de bajada', 'r134': 'Laboratorio: pasillo B2', 'r135': 'Laboratorio: cruce B3',
    'r137': 'Laboratorio: celdas', 'r138': 'Laboratorio: sala de energía', 'r139': 'Laboratorio: pasillo B4', 'r140': 'Laboratorio principal (B4)',
    'r142': 'Laboratorio: pasaje al helipuerto', 'r144': 'Helipuerto',
}
# salas UC de fuera de la mansión: puntos de puerta aproximados (x, z en metros de UC)
AREAS = {
    'r116': dict(O=(-9.8, 3.5), N=(4.0, 8.6), S=(1.0, -7.6)),
    'r117': dict(A=(-10.5, -10.8), B=(1.0, -8.2)),
    'r118': dict(S=(0.0, -13.8), N=(0.0, 9.6), E=(7.5, 0.0), O=(-7.5, -0.5)),
    'r119': dict(A=(-25.5, -26.8), B=(-8.3, -0.5)),
    'r120': dict(A=(-4.0, 0.0), B=(2.5, -1.0)),
    'r121': dict(A=(-17.5, 6.5), B=(-1.0, 10.0), C=(-4.0, 0.8)),
    'r122': dict(A=(-1.0, 18.5), B=(-4.0, 11.2)),
    'r123': dict(A=(5.3, -1.0), B=(1.5, 4.7), C=(-7.0, 2.5), D=(-7.0, -4.3)),
    'r125': dict(A=(0.2, 6.5), B=(12.5, -7.8), C=(2.0, 5.4), D=(6.0, 5.4)),
    'r126': dict(A=(13.5, -4.0), B=(19.0, -8.0)),
    'r127': dict(A=(-24.5, -5.5), B=(0.0, -13.5)),
    'r128': dict(A=(-3.0, -13.0), B=(0.0, 11.0)),
    'r130': dict(A=(-5.0, 0.0), B=(5.0, -5.0)),
    'r133': dict(A=(-21.0, -1.5), B=(0.0, 8.5)),
    'r134': dict(A=(-12.5, 9.5), B=(-1.0, 10.0)),
    'r135': dict(A=(6.5, 28.5), B=(11.0, 14.0), C=(0.0, 20.0)),
    'r137': dict(A=(1.5, 41.0), B=(11.5, 38.0)),
    'r138': dict(A=(6.0, 46.2), B=(0.5, 53.5)),
    'r139': dict(A=(2.0, 18.5), B=(11.0, 14.2)),
    'r140': dict(A=(2.0, 19.5), B=(12.0, 25.0)),
    'r142': dict(A=(-27.0, -16.0), B=(-3.0, -0.5)),
    'r144': dict(A=(-9.0, 0.0), B=(10.0, 10.0)),
}
# puertas solo-AEV en salas UC de la mansión: posición del umbral (RE4 mm), dirección hacia dentro (x, z)
VIRTUALES = {
    'altar_vestibulo': dict(sala='r102', centro=(-33300.0, -990.0, 6200.0), normal=(-1.0, 0.0), ancho=1200.0),
}
ENLACES = [
    # mansión 1F oeste
    ('m:r100:0', 'g:te_bar:comedor'), ('m:r100:1', 'g:norte:vestibulo'), ('g:te_bar:norte', 'g:norte:te'),
    ('g:te_bar:sotano', 'g:ascensor:ascensor'),
    # mansión 1F este
    ('m:r105:0', 'g:bano:entrada'), ('m:r105:1', 'g:salon:entrada'), ('g:bano:salon', 'g:salon:bano'), ('g:bano:caldera', 'g:bano:cal_in'),
    ('m:r106:0', 'g:oscuro:entrada'), ('m:r106:1', 'g:arte:entrada'), ('g:oscuro:cementerio', 'g:cementerio:galeria'),
    ('g:oscuro:techado', 'g:techado:oscuro'), ('g:cementerio:altar', 'g:altar:cripta'), ('v:altar_vestibulo', 'g:altar:vestibulo'),
    # mansión 2F
    ('m:r108:0', 'g:pasillo_c:entrada'), ('m:r108:1', 'g:ciervo:entrada'), ('g:pasillo_c:balcon', 'g:balcones:pasillo_c'),
    ('g:balcones:ascensor', 'g:ascensor:balcones'), ('m:r112:0', 'g:espejos:entrada'), ('m:r113:0', 'g:dormitorio:entrada'),
    ('m:r113:1', 'g:ascensor:entrada'),
    # patio
    ('g:techado:patio', 'a:r116:O'), ('a:r116:N', 'a:r117:A'), ('a:r117:B', 'a:r118:S'), ('a:r118:O', 'a:r119:B'),
    ('a:r119:A', 'g:piscina:patio'), ('a:r118:E', 'a:r116:S'), ('a:r118:N', 'g:lab_entrada:ascensor'),
    ('g:piscina:cabana', 'g:cabana:cascada'), ('g:cabana:cuevas', 'a:r120:A'),
    # cuevas
    ('a:r120:B', 'a:r121:A'), ('a:r121:B', 'a:r122:B'), ('a:r121:C', 'g:cuevas_b1:cueva_uc'), ('g:cuevas_b1:b2', 'g:cuevas_b2:b1'),
    # residencia
    ('g:piscina:residencia', 'a:r123:A'), ('a:r123:B', 'a:r125:A'), ('a:r123:C', 'g:residencia:entrada'), ('a:r125:C', 'g:habitaciones:residencia'),
    ('a:r125:D', 'a:r126:A'), ('a:r125:B', 'a:r130:A'), ('g:residencia:salida', 'a:r127:A'), ('a:r127:B', 'a:r128:A'),
    # laboratorio
    ('g:lab_entrada:helipuerto', 'a:r144:A'), ('g:lab_entrada:b3', 'a:r133:A'), ('a:r133:B', 'a:r134:A'), ('a:r134:B', 'a:r135:A'),
    ('a:r135:B', 'g:lab_b3:arriba'), ('a:r135:C', 'a:r139:A'), ('a:r139:B', 'a:r140:A'), ('g:lab_b3:b4', 'a:r137:A'),
    ('a:r137:B', 'a:r138:A'), ('a:r138:B', 'a:r142:A'), ('a:r142:B', 'a:r144:B'),
]
