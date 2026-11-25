"""noche.py dir_sala : el cielo de las ventanas (texturas de cristal) pasa a ser de noche"""
import sys, glob, os, re
import numpy as np
from PIL import Image
for p in glob.glob(os.path.join(sys.argv[1], '*.png')):
    if not re.search(r'glass|garasu', os.path.basename(p), re.I): continue
    im = Image.open(p); modo = im.mode; a = np.asarray(im.convert('RGBA'), np.float32) / 255
    rgb = a[..., :3]; L = rgb @ np.array([0.3, 0.59, 0.11], np.float32)
    cielo = (rgb[..., 2] > rgb[..., 0] + 0.02) & (L > 0.25)
    noche = np.stack([0.035 + 0.10 * L, 0.05 + 0.12 * L, 0.09 + 0.18 * L], -1)
    rgb[cielo] = noche[cielo]; rgb[~cielo] *= 0.55
    a[..., :3] = rgb; Image.fromarray((np.clip(a, 0, 1) * 255).astype(np.uint8)).convert(modo).save(p)
    print('noche:', os.path.basename(p), f'{cielo.mean()*100:.0f}% cielo')
