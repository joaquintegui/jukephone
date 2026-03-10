#!/usr/bin/env python3
"""
JukePhone - modes/music.py
"""

import json
import os
import subprocess
from audio import beep

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'database.json')

def cargar_database():
    with open(DB_PATH, 'r') as f:
        return json.load(f)['artists']

def llamar_artista(numero):
    try:
        db = cargar_database()
        artista = db.get(numero)
        if not artista:
            print(f"[MÚSICA] {numero} no encontrado — marcá otro número")
            beep(frecuencia=200, duracion=0.3)
            return False
        print(f"[MÚSICA] Encontrado: {artista}")
        # Anunciar en background para no bloquear
        subprocess.Popen(
            ['espeak', '-v', 'es', '-s', '140', f"Llamando a {artista}"],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
        )
        # TODO: Spotify
        print(f"[MÚSICA] TODO: reproducir {artista} en Spotify")
        return True
    except Exception as e:
        print(f"[MÚSICA] Error: {e}")
        return False

def on_numero_marcado(numero):
    print(f"[MÚSICA] Número: {numero}")
    return llamar_artista(numero)
