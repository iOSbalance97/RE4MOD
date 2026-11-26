"""Lector mínimo de FBX binario (v7.x): árbol de nodos con propiedades; arrays con zlib."""
import struct, zlib
import numpy as np

class Nodo:
    __slots__ = ('nombre', 'props', 'hijos')
    def __init__(self, n, p, h): self.nombre, self.props, self.hijos = n, p, h
    def hijo(self, n):
        for h in self.hijos:
            if h.nombre == n: return h
    def todos(self, n): return [h for h in self.hijos if h.nombre == n]
    def __repr__(self): return f'<{self.nombre} {self.props[:3]}>'

def _prop(d, p):
    t = chr(d[p]); p += 1
    if t == 'Y': return struct.unpack_from('<h', d, p)[0], p + 2
    if t == 'C': return d[p] != 0, p + 1
    if t == 'I': return struct.unpack_from('<i', d, p)[0], p + 4
    if t == 'F': return struct.unpack_from('<f', d, p)[0], p + 4
    if t == 'D': return struct.unpack_from('<d', d, p)[0], p + 8
    if t == 'L': return struct.unpack_from('<q', d, p)[0], p + 8
    if t in 'SR':
        n = struct.unpack_from('<I', d, p)[0]; p += 4; b = d[p:p + n]
        return (b.decode('utf8', 'replace') if t == 'S' else b), p + n
    if t in 'fdlib':
        n, enc, clen = struct.unpack_from('<III', d, p); p += 12; raw = d[p:p + clen]; p += clen
        if enc == 1: raw = zlib.decompress(raw)
        dt = {'f': '<f4', 'd': '<f8', 'l': '<i8', 'i': '<i4', 'b': 'u1'}[t]
        return np.frombuffer(raw, dt, n), p
    raise ValueError('tipo ' + t)

def leer(ruta):
    d = open(ruta, 'rb').read(); ver = struct.unpack_from('<I', d, 23)[0]; ancho = 8 if ver >= 7500 else 4
    fmt = '<QQQ' if ancho == 8 else '<III'; hdr = 3 * ancho + 1
    def nodo(p):
        fin, nprops, plen = struct.unpack_from(fmt, d, p); nl = d[p + 3 * ancho]
        if fin == 0: return None, p + hdr
        nombre = d[p + hdr:p + hdr + nl].decode('ascii', 'replace'); q = p + hdr + nl
        props = []
        for _ in range(nprops):
            v, q = _prop(d, q); props.append(v)
        hijos = []
        while q < fin:
            h, q = nodo(q)
            if h is None: break
            hijos.append(h)
        return Nodo(nombre, props, hijos), fin
    p = 27; raiz = []
    while p < len(d) - hdr:
        n, p = nodo(p)
        if n is None: break
        raiz.append(n)
    return Nodo('raiz', [], raiz)
