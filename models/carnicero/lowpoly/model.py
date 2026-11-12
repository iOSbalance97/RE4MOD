"""El Carnicero, GAME (low-poly) version: the detailed model's own shapes (model_hi.py) meshed coarse and
decimated to the game budget (~3200 triangles); the detail lives in the painted texture (tex.py samples
model_hi for materials). Same names/joints as model_hi."""
from model_hi import *
import model_hi as _h
PARTS = [('body', _h.body, _h.BODY_BOX, 7.0, 2000), ('mask', _h.hood, _h.HOOD_BOX, 4.0, 420), ('fist', _h.fist, _h.FIST_BOX, 4.0, 120),
         ('claw', _h.claw, _h.CLAW_BOX, 3.0, 330), ('acc', _h.acc, _h.ACC_BOX, 3.0, 260), ('weapon', _h.weapon, _h.WEAPON_BOX, 2.5, 300)]
