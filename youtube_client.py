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

    def buscar_y_reproducir(self, query):
        # Terminar reproducción anterior
        if self._proceso and self._proceso.poll() is None:
            self._proceso.terminate()
            self._proceso = None

        try:
            os.unlink(SOCKET_PATH)
        except OSError:
            pass

        search = f"ytsearch15:{query}"
        cmd = [
            'mpv',
            '--no-video',
            '--audio-device=alsa/default',
            f'--input-ipc-server={SOCKET_PATH}',
            '--ytdl-format=bestaudio[ext=m4a]/bestaudio/best',
            '--msg-level=all=warn',
            search,
        ]
        try:
            self._proceso = subprocess.Popen(cmd)
            return True, query
        except Exception as e:
            return False, str(e)

    def play_pause(self):
        self._mpv_send({"command": ["cycle", "pause"]})

    def siguiente(self):
        self._mpv_send({"command": ["playlist-next"]})

    def anterior(self):
        self._mpv_send({"command": ["playlist-prev"]})

    def cambiar_volumen(self, delta):
        self._mpv_send({"command": ["add", "volume", delta]})
