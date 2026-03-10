#!/usr/bin/env python3
"""
JukePhone - modes/debug_mode.py
Modo 2: Debug — cada tecla es anunciada por voz y logueada en CLI
"""

import subprocess
from audio import beep

NOMBRES = {
    '0': 'cero',   '1': 'uno',    '2': 'dos',    '3': 'tres',
    '4': 'cuatro', '5': 'cinco',  '6': 'seis',   '7': 'siete',
    '8': 'ocho',   '9': 'nueve',  '*': 'estrella', '#': 'numeral'
}

def on_modo_activado():
    print("[DEBUG] Modo debug activado — cada tecla será anunciada")
    beep(frecuencia=880, duracion=0.1)
    _hablar("modo debug activado")

def on_modo_desactivado():
    beep(frecuencia=440, duracion=0.1)

def on_tecla(tecla):
    nombre = NOMBRES.get(tecla, tecla)
    print(f"[DEBUG] '{tecla}' → {nombre}")
    _hablar(nombre)

def _hablar(texto):
    subprocess.Popen(
        ['espeak', '-v', 'es', '-s', '140', '-a', '200', texto],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
    )
