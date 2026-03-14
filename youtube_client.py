#!/usr/bin/env python3
"""
JukePhone - youtube_client.py

Reproduce música de YouTube usando yt-dlp + mpv.
No requiere cuenta ni autenticación.

Setup:
  sudo apt install mpv -y
  sudo pip3 install yt-dlp --break-system-packages
"""

import json
import os
import socket
import subprocess
import audio

SOCKET_PATH = '/tmp/jukephone-mpv.sock'
VOLUME_STEP  = 10


class YouTubeClient:

    def __init__(self):
        self._proceso = None

    def _mpv_send(self, cmd):
        try:
            s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            s.settimeout(1)
            s.connect(SOCKET_PATH)
            s.send(json.dumps(cmd).encode() + b'\n')
            s.close()
        except Exception as e:
            print(f"[YT] mpv IPC: {e}")

    def buscar_urls(self, query):
        """Solo yt-dlp — devuelve lista de URLs sin iniciar reproducción."""
        try:
            resultado = subprocess.run(
                [
                    'yt-dlp',
                    '--flat-playlist',
                    '--print', 'https://youtube.com/watch?v=%(id)s',
                    f'ytsearch15:{query}',
                ],
                capture_output=True, text=True, timeout=30,
            )
            return [u for u in resultado.stdout.strip().splitlines() if u.startswith('http')]
        except Exception as e:
            print(f"[YT] yt-dlp error: {e}")
            return []

    def reproducir_urls(self, urls):
        """Inicia mpv con las URLs ya resueltas."""
        if self._proceso and self._proceso.poll() is None:
            self._proceso.terminate()
            self._proceso = None
        try:
            os.unlink(SOCKET_PATH)
        except OSError:
            pass

        cmd = [
            'mpv',
            '--no-video',
            '--loop=no',
            '--loop-playlist=no',
            f'--audio-device=alsa/{audio.AUDIO_DEVICE_OUT}',
            f'--input-ipc-server={SOCKET_PATH}',
            '--ytdl-format=bestaudio[ext=m4a]/bestaudio/best',
            '--msg-level=all=warn',
        ] + urls
        try:
            self._proceso = subprocess.Popen(cmd)
            return True
        except Exception as e:
            print(f"[YT] mpv error: {e}")
            return False

    def buscar_y_reproducir(self, query):
        urls = self.buscar_urls(query)
        if not urls:
            return False, "Sin resultados"
        ok = self.reproducir_urls(urls)
        return ok, query

    def esperar_inicio(self, timeout=15):
        """Espera hasta que mpv esté reproduciendo de verdad (time-pos > 0)."""
        import time as _time
        inicio = _time.time()
        while _time.time() - inicio < timeout:
            try:
                s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
                s.settimeout(0.5)
                s.connect(SOCKET_PATH)
                s.send(json.dumps({"command": ["get_property", "time-pos"]}).encode() + b'\n')
                resp = b''
                while b'\n' not in resp:
                    chunk = s.recv(256)
                    if not chunk:
                        break
                    resp += chunk
                s.close()
                data = json.loads(resp.decode().split('\n')[0])
                if isinstance(data.get('data'), (int, float)) and data['data'] > 0:
                    return True
            except Exception:
                pass
            _time.sleep(0.3)
        return False

    def play_pause(self):
        self._mpv_send({"command": ["cycle", "pause"]})

    def siguiente(self):
        self._mpv_send({"command": ["playlist-next"]})

    def anterior(self):
        self._mpv_send({"command": ["playlist-prev"]})

    def cambiar_volumen(self, delta):
        self._mpv_send({"command": ["add", "volume", delta]})
