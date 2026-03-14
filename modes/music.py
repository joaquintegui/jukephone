#!/usr/bin/env python3
"""
JukePhone - modes/music.py
Modo música: marcar 8 dígitos → busca artista en database.json → reproduce en YouTube.
"""

import json
import os
import sys
import threading
import time
from audio import beep, hablar_bg
from youtube_client import YouTubeClient

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
import sync_database

DB_PATH      = os.path.join(os.path.dirname(__file__), '..', 'database.json')
VOLUME_STEP  = 10
CODIGO_SYNC  = '12345678'

_spotify = YouTubeClient()


def _cargar_database():
    with open(DB_PATH, 'r') as f:
        return json.load(f)['artists']


def on_modo_activado():
    print("[MÚSICA] Modo activo — marcá 8 dígitos para llamar a un artista")


def on_modo_desactivado():
    pass


def _ring_loop(stop):
    """Tono de llamada: dos pulsos cortos, pausa larga. Para cuando stop se activa."""
    time.sleep(0.8)   # esperar que termine el espeak "Llamando a..."
    while not stop.is_set():
        beep(frecuencia=480, duracion=0.35)
        if stop.is_set():
            break
        time.sleep(0.15)
        beep(frecuencia=480, duracion=0.35)
        if stop.is_set():
            break
        time.sleep(1.8)   # pausa entre timbrazos


def on_numero_marcado(numero):
    print(f"[MÚSICA] Número: {numero}")

    if numero == CODIGO_SYNC:
        print("[MÚSICA] Sincronizando agenda...")
        hablar_bg("Actualizando agenda")
        threading.Thread(target=sync_database.sync, daemon=True).start()
        return True

    try:
        db      = _cargar_database()
        artista = db.get(numero)
        if not artista:
            print(f"[MÚSICA] {numero} no encontrado en database.json")
            beep(frecuencia=200, duracion=0.3)
            return False

        print(f"[MÚSICA] Llamando a: {artista}")
        hablar_bg(f"Llamando a {artista}")

        stop = threading.Event()
        threading.Thread(target=_ring_loop, args=(stop,), daemon=True).start()

        # yt-dlp busca mientras suena el ring
        urls = _spotify.buscar_urls(artista)
        stop.set()   # para el ring — yt-dlp ya terminó, mpv empieza ya

        if not urls:
            print(f"[MÚSICA] Sin resultados para: {artista}")
            beep(frecuencia=200, duracion=0.3)
            return False

        ok = _spotify.reproducir_urls(urls)
        if ok:
            print(f"[MÚSICA] Reproduciendo: {artista}")
        else:
            print(f"[MÚSICA] Error iniciando mpv")
            beep(frecuencia=200, duracion=0.3)
        return ok

    except Exception as e:
        print(f"[MÚSICA] Error: {e}")
        beep(frecuencia=200, duracion=0.3)
        return False


# ── Controles de reproducción (llamados desde main.py) ──────────────────────

def play_pause():
    _spotify.play_pause()

def siguiente():
    _spotify.siguiente()

def anterior():
    _spotify.anterior()

def subir_volumen():
    _spotify.cambiar_volumen(+VOLUME_STEP)

def bajar_volumen():
    _spotify.cambiar_volumen(-VOLUME_STEP)
