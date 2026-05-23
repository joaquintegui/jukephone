#!/usr/bin/env python3
"""
Modo música via yt-dlp + mpv (sin browser, sin Selenium).

Instalar en la Pi:
    sudo apt install mpv -y
    pip install yt-dlp --break-system-packages
"""

import json
import os
import socket
import subprocess
import threading
from pathlib import Path
from audio import beep, beep_en, DEVICE_TUBO

DB_PATH      = Path(__file__).parent.parent / 'database.json'
MPV_SOCKET   = '/tmp/mpvsocket'
AUDIO_DEVICE = 'alsa/plughw:1,0'   # parlante externo (jack 3.5mm Pi)
CODIGO_SYNC  = '12345678'

_mpv_proc  = None
_stop_ring = threading.Event()


# ── Interface pública ──────────────────────────────────────────────────────────

def precalentar():
    pass


def on_modo_activado():
    print("[YTM] Modo música activo")
    beep(frecuencia=880, duracion=0.1)
    beep(frecuencia=1100, duracion=0.1)


def on_modo_desactivado():
    print("[YTM] Cerrando...")
    _stop_ring.set()
    _mpv_kill()


def on_numero_marcado(numero):
    if numero == CODIGO_SYNC:
        return

    try:
        data    = json.loads(DB_PATH.read_text())
        artista = data.get('artists', {}).get(numero)
    except Exception as e:
        print(f"[YTM] Error leyendo DB: {e}")
        beep(frecuencia=200, duracion=0.3)
        return

    if not artista:
        print(f"[YTM] {numero} no encontrado")
        beep(frecuencia=200, duracion=0.3)
        return

    print(f"[YTM] Buscando: {artista}")
    _stop_ring.clear()
    threading.Thread(target=_ring_loop, daemon=True).start()
    threading.Thread(target=_buscar_y_reproducir, args=(artista,), daemon=True).start()


def play_pause():
    _send_mpv(['cycle', 'pause'])


def siguiente():
    _send_mpv(['playlist-next', 'force'])


def anterior():
    _send_mpv(['playlist-prev', 'force'])


def subir_volumen():
    _send_mpv(['add', 'volume', 5])


def bajar_volumen():
    _send_mpv(['add', 'volume', -5])


# ── Internos ───────────────────────────────────────────────────────────────────

def _ring_loop():
    while not _stop_ring.is_set():
        beep_en(DEVICE_TUBO, frecuencia=480, duracion=0.35)
        if _stop_ring.wait(timeout=0.15):
            break
        beep_en(DEVICE_TUBO, frecuencia=480, duracion=0.35)
        if _stop_ring.wait(timeout=1.8):
            break


def _mpv_kill():
    global _mpv_proc
    if _mpv_proc and _mpv_proc.poll() is None:
        _mpv_proc.terminate()
        try:
            _mpv_proc.wait(timeout=3)
        except subprocess.TimeoutExpired:
            _mpv_proc.kill()
    _mpv_proc = None


def _send_mpv(cmd):
    try:
        s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        s.settimeout(1)
        s.connect(MPV_SOCKET)
        s.sendall(json.dumps({'command': cmd}).encode() + b'\n')
        s.close()
    except Exception as e:
        print(f"[YTM] mpv IPC: {e}")


def _buscar_y_reproducir(artista):
    global _mpv_proc
    _mpv_kill()

    try:
        os.remove(MPV_SOCKET)
    except FileNotFoundError:
        pass

    cmd = [
        'mpv',
        '--no-video',
        f'--audio-device={AUDIO_DEVICE}',
        f'--input-ipc-server={MPV_SOCKET}',
        '--ytdl-format=bestaudio/best',
        '--ytdl-path=yt-dlp',
        f'ytsearch1:{artista}',
    ]

    print(f"[YTM] mpv: {artista}")
    _mpv_proc = subprocess.Popen(
        cmd,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.PIPE,
    )

    _stop_ring.set()

    def _log_stderr():
        for line in _mpv_proc.stderr:
            txt = line.decode(errors='replace').strip()
            if txt:
                print(f"[MPV] {txt}")
    threading.Thread(target=_log_stderr, daemon=True).start()
