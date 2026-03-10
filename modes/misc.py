#!/usr/bin/env python3
"""
JukePhone - modes/misc.py
Modo 4: reproduce Seminare.mp3
Amarillos: beep por ahora
"""

import subprocess
import os
from audio import beep, AUDIO_DEVICE_OUT

CANCION = os.path.expanduser('~/Seminare.mp3')
_proceso_musica = None

def on_modo_activado():
    global _proceso_musica
    print(f"[MODO 4] Reproduciendo {CANCION}")
    if os.path.exists(CANCION):
        _proceso_musica = subprocess.Popen(
            ['mpg123', '-a', AUDIO_DEVICE_OUT, CANCION],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
        )
    else:
        print(f"[MODO 4] No se encontró {CANCION}")
        beep(frecuencia=200, duracion=0.5)

def on_modo_desactivado():
    global _proceso_musica
    if _proceso_musica and _proceso_musica.poll() is None:
        _proceso_musica.terminate()
        _proceso_musica = None
    beep(frecuencia=440, duracion=0.1)

def on_amarillo_1():
    print("[AMARILLO 1] Apretado")
    beep(frecuencia=523, duracion=0.15)

def on_amarillo_2():
    print("[AMARILLO 2] Apretado")
    beep(frecuencia=659, duracion=0.15)
