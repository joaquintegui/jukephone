#!/usr/bin/env python3
"""
JukePhone - spotify_client.py

Setup inicial (una sola vez):
  1. En https://developer.spotify.com/dashboard → tu app → Edit settings
     Agregar redirect URI: http://127.0.0.1:8888/callback
     (escribirlo manualmente y hacer clic en Add, luego Save)

  2. Exportar credenciales en la Raspberry (agregar a ~/.bashrc):
       export SPOTIPY_CLIENT_ID="tu_client_id"
       export SPOTIPY_REDIRECT_URI="http://127.0.0.1:8888/callback"
     (PKCE no necesita client_secret)
     Luego: source ~/.bashrc

  3. Correr una vez para autenticar:
       python3 spotify_client.py
     - Abre la URL que aparece en un navegador
     - Spotify redirige a http://127.0.0.1:8888/callback?code=...
       (puede mostrar "sitio no disponible" — eso es normal)
     - Copiá la URL completa de la barra del navegador y pegala en la terminal

  4. El token queda cacheado en ~/.jukephone_spotify_cache y se renueva solo.
"""

import os
import spotipy
from spotipy.oauth2 import SpotifyPKCE

SCOPE = (
    'user-read-playback-state '
    'user-modify-playback-state '
    'user-read-currently-playing'
)
CACHE_PATH   = os.path.expanduser('~/.jukephone_spotify_cache')
REDIRECT_URI = 'http://127.0.0.1:8888/callback'
DEVICE_NAME  = 'jukephone'
VOLUME_STEP  = 10


class SpotifyClient:

    def __init__(self):
        self._sp        = None
        self._device_id = None

    def _conectar(self):
        if self._sp is None:
            self._sp = spotipy.Spotify(auth_manager=SpotifyPKCE(
                scope=SCOPE,
                cache_path=CACHE_PATH,
                redirect_uri=REDIRECT_URI,
                open_browser=False,
            ))
        return self._sp

    def _get_device_id(self):
        try:
            devices = self._conectar().devices()
            for d in devices['devices']:
                if DEVICE_NAME.lower() in d['name'].lower():
                    self._device_id = d['id']
                    return d['id']
            print(f"[SPOTIFY] Dispositivo '{DEVICE_NAME}' no encontrado entre: "
                  f"{[d['name'] for d in devices['devices']]}")
        except Exception as e:
            print(f"[SPOTIFY] Error buscando dispositivo: {e}")
        return None

    def buscar_y_reproducir(self, query):
        try:
            sp        = self._conectar()
            device_id = self._get_device_id()
            if not device_id:
                return False, "Dispositivo no disponible"

            results  = sp.search(q=f'artist:{query}', type='artist', limit=1)
            artists  = results['artists']['items']
            if not artists:
                return False, "Artista no encontrado"

            artist = artists[0]
            sp.start_playback(
                device_id=device_id,
                context_uri=f"spotify:artist:{artist['id']}",
            )
            return True, artist['name']
        except Exception as e:
            print(f"[SPOTIFY] Error: {e}")
            return False, str(e)

    def play_pause(self):
        try:
            sp    = self._conectar()
            state = sp.current_playback()
            if state and state['is_playing']:
                sp.pause_playback()
            else:
                sp.start_playback(device_id=self._device_id)
        except Exception as e:
            print(f"[SPOTIFY] play_pause error: {e}")

    def siguiente(self):
        try:
            self._conectar().next_track()
        except Exception as e:
            print(f"[SPOTIFY] siguiente error: {e}")

    def anterior(self):
        try:
            self._conectar().previous_track()
        except Exception as e:
            print(f"[SPOTIFY] anterior error: {e}")

    def cambiar_volumen(self, delta):
        try:
            sp    = self._conectar()
            state = sp.current_playback()
            if state:
                actual = state['device']['volume_percent']
                nuevo  = max(0, min(100, actual + delta))
                sp.volume(nuevo, device_id=self._device_id)
                print(f"[SPOTIFY] Volumen: {nuevo}%")
        except Exception as e:
            print(f"[SPOTIFY] volumen error: {e}")


if __name__ == '__main__':
    print("Autenticando con Spotify...")
    client = SpotifyClient()
    sp     = client._conectar()
    print(f"OK — token guardado en {CACHE_PATH}")
    devices = sp.devices()
    print("Dispositivos disponibles:")
    for d in devices['devices']:
        print(f"  - {d['name']} ({d['type']}) id={d['id']}")
