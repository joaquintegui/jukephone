#!/usr/bin/env python3
"""
JukePhone - modes/parrot.py
* para grabar, # para reproducir
"""

import os
import subprocess
import time
from audio import grabar, AUDIO_DEVICE_OUT, SAMPLE_RATE

_proceso = None
_archivo = None
_grabando = False

def on_modo_activado():
    print("[LORO] * para grabar  |  # para reproducir")

def on_modo_desactivado():
    _detener()

def on_tecla(tecla):
    global _grabando
    if tecla == '*':
        _iniciar_grabacion()
    elif tecla == '#':
        _reproducir()

def _iniciar_grabacion():
    global _proceso, _archivo, _grabando
    _detener()
    _archivo, _proceso = grabar()
    _grabando = True
    print("[LORO] Grabando... apretá * de nuevo para parar")

def _reproducir():
    global _proceso, _archivo, _grabando
    # Si está grabando, detener primero
    if _grabando:
        _detener()
        time.sleep(0.3)

    if not _archivo or not os.path.exists(_archivo):
        print("[LORO] Nada grabado todavía")
        return

    size = os.path.getsize(_archivo)
    print(f"[LORO] Reproduciendo ({size} bytes)...")

    ret = subprocess.run(
        ['aplay', '-D', AUDIO_DEVICE_OUT, _archivo],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE
    )
    if ret.returncode != 0:
        print(f"[LORO] Error: {ret.stderr.decode().strip()}")
    else:
        print("[LORO] OK")

def _detener():
    global _proceso, _grabando
    if _proceso and _proceso.poll() is None:
        _proceso.terminate()
        try:
            _proceso.wait(timeout=2)
        except subprocess.TimeoutExpired:
            _proceso.kill()
    _proceso = None
    _grabando = False
