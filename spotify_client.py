#!/usr/bin/env python3
"""
JukePhone - spotify_client.py
Token generado con auth_spotify.py en la Mac y copiado a la Pi.
Se renueva automáticamente usando el refresh_token.
"""

import os
import spotipy
from spotipy.oauth2 import SpotifyOAuth

CLIENT_ID     = '4cdfb58d330149eb9932bac6d0a71002'
CLIENT_SECRET = 'c45dcbcb1d0144619fe880a7b80a7ef5'
REDIRECT_URI  = 'http://127.0.0.1:8888/callback'
SCOPE = (
    'user-read-playback-state '
    'user-modify-playback-state '
    'user-read-currently-playing'
)
CACHE_PATH  = os.path.expanduser('~/.jukephone_spotify_cache')
DEVICE_NAME = 'jukebox'
VOLUME_STEP = 10


class SpotifyClient:

    def __init__(self):
        self._sp        = None
        self._device_id = None

    def _conectar(self):
        if self._sp is None:
            self._sp = spotipy.Spotify(auth_manager=SpotifyOAuth(
                client_id=CLIENT_ID,
                client_secret=CLIENT_SECRET,
                redirect_uri=REDIRECT_URI,
                scope=SCOPE,
                cache_path=CACHE_PATH,
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

            results = sp.search(q=f'artist:{query}', type='artist', limit=1)
            artists = results['artists']['items']
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

    def parar(self):
        try:
            sp    = self._conectar()
            state = sp.current_playback()
            if state and state['is_playing']:
                sp.pause_playback()
        except Exception as e:
            print(f"[SPOTIFY] parar error: {e}")

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
            self._conectar().next_track(device_id=self._device_id)
        except Exception as e:
            print(f"[SPOTIFY] siguiente error: {e}")

    def anterior(self):
        try:
            self._conectar().previous_track(device_id=self._device_id)
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
    client = SpotifyClient()
    sp     = client._conectar()
    devices = sp.devices()
    print("Dispositivos disponibles:")
    for d in devices['devices']:
        print(f"  - {d['name']} ({d['type']}) id={d['id']}")
