# B88: the stealth tutorial panel (Spanish), drawn to an I4 texture (GX tiles 8x8, 4 bit) for barn.c
import numpy as np, struct
from PIL import Image, ImageDraw, ImageFont
W, H = 512, 256
S = 2                                                     # supersample
im = Image.new('L', (W * S, H * S), 0); dr = ImageDraw.Draw(im)
F = '/usr/share/fonts/truetype/crosextra/Caladea-%s.ttf'
title = ImageFont.truetype(F % 'Bold', 34 * S); body = ImageFont.truetype(F % 'Regular', 21 * S)
def circle_btn(x, y):
    r = 11 * S; dr.ellipse((x, y, x + 2 * r, y + 2 * r), outline=255, width=2 * S)
    dr.ellipse((x + 6 * S, y + 6 * S, x + 2 * r - 6 * S, y + 2 * r - 6 * S), outline=255, width=3 * S)
    return 2 * r + 5 * S
def cross_btn(x, y):
    r = 11 * S; dr.ellipse((x, y, x + 2 * r, y + 2 * r), outline=255, width=2 * S)
    m = 7 * S; dr.line((x + m, y + m, x + 2 * r - m, y + 2 * r - m), fill=255, width=3 * S); dr.line((x + 2 * r - m, y + m, x + m, y + 2 * r - m), fill=255, width=3 * S)
    return 2 * r + 5 * S
y = 10 * S
tw = dr.textlength('SIGILO', font=title); dr.text(((W * S - tw) / 2, y), 'SIGILO', font=title, fill=255)
y += 48 * S
dr.line((60 * S, y, (W - 60) * S, y), fill=150, width=S); y += 12 * S
lines = [[('t', 'Pulsa '), ('o', ''), ('t', ' para agacharte. Agachado haces muy poco')],
         [('t', 'ruido: un Ganado solo te nota a un paso de él.')],
         [('t', 'Acércate por su espalda sin que te vea y, cuando')],
         [('t', 'aparezca '), ('x', ''), ('t', ', púlsalo para acabar con él en silencio.')],
         [('t', 'Si te descubre, tendrás que luchar.')]]
for ln in lines:
    x = 34 * S
    for k, s in ln:
        if k == 't': dr.text((x, y), s, font=body, fill=255); x += dr.textlength(s, font=body)
        elif k == 'o': x += circle_btn(x, y + 2 * S)
        else: x += cross_btn(x, y + 2 * S)
    y += 28 * S
sm = ImageFont.truetype(F % 'Italic', 17 * S); y += 4 * S
x = (W - 175) * S; dr.text((x, y), 'Continuar', font=sm, fill=200); x += dr.textlength('Continuar ', font=sm); cross_btn(x, y)
img = np.array(im.resize((W, H), Image.LANCZOS)).astype(np.float32)
q = np.clip(np.round(img / 17.0), 0, 15).astype(np.uint8)
out = bytearray()
for ty in range(0, H, 8):
    for tx in range(0, W, 8):
        t = q[ty:ty + 8, tx:tx + 8]
        for r in t: out += bytes((r[i] << 4) | r[i + 1] for i in range(0, 8, 2))
open('data/tut_stealth.i4', 'wb').write(out); open('data/tut_stealth.dim', 'wb').write(struct.pack('>HH', W, H))
Image.fromarray((q * 17).astype(np.uint8)).save('/tmp/tut.png'); print(len(out))
