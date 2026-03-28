#!/usr/bin/env python3
"""
Renueva el access token de Spotify e inyecta en /etc/raspotify/conf.
Correr con sudo — configurado en cron cada 45 minutos.
"""

import json
import os
import re
import subprocess
import sys

CACHE_PATH    = os.path.expanduser('~/.jukephone_spotify_cache')
RASPOTIFY_CONF = '/etc/raspotify/conf'

# Mismo auth que spotify_client.py
CLIENT_ID     = '4cdfb58d330149eb9932bac6d0a71002'
CLIENT_SECRET = 'c45dcbcb1d0144619fe880a7b80a7ef5'
REDIRECT_URI  = 'http://127.0.0.1:8888/callback'
SCOPE = (
    'streaming '
    'user-read-playback-state '
    'user-modify-playback-state '
    'user-read-currently-playing'
)

import spotipy
from spotipy.oauth2 import SpotifyOAuth

def get_fresh_token():
    auth = SpotifyOAuth(
        client_id=CLIENT_ID,
        client_secret=CLIENT_SECRET,
        redirect_uri=REDIRECT_URI,
        scope=SCOPE,
        cache_path=CACHE_PATH,
        open_browser=False,
    )
    token_info = auth.get_cached_token()
    if not token_info:
        print("ERROR: no hay token cacheado. Corré auth_spotify.py primero.")
        sys.exit(1)
    if auth.is_token_expired(token_info):
        token_info = auth.refresh_access_token(token_info['refresh_token'])
    return token_info['access_token']

def update_raspotify_conf(token):
    with open(RASPOTIFY_CONF, 'r') as f:
        content = f.read()

    # Reemplaza o agrega LIBRESPOT_ACCESS_TOKEN
    if 'LIBRESPOT_ACCESS_TOKEN=' in content:
        content = re.sub(
            r'LIBRESPOT_ACCESS_TOKEN=.*',
            f'LIBRESPOT_ACCESS_TOKEN="{token}"',
            content
        )
    else:
        content += f'\nLIBRESPOT_ACCESS_TOKEN="{token}"\n'

    # Asegura que discovery esté deshabilitada (evita colisión de nombre)
    if '#LIBRESPOT_DISABLE_DISCOVERY=' in content or 'LIBRESPOT_DISABLE_DISCOVERY=' not in content:
        content = re.sub(r'#?LIBRESPOT_DISABLE_DISCOVERY=.*\n', '', content)
        content += 'LIBRESPOT_DISABLE_DISCOVERY=\n'

    with open(RASPOTIFY_CONF, 'w') as f:
        f.write(content)

    print(f"Token actualizado en {RASPOTIFY_CONF}")

if __name__ == '__main__':
    token = get_fresh_token()
    update_raspotify_conf(token)
    subprocess.run(['systemctl', 'restart', 'raspotify'])
    print("raspotify reiniciado con nuevo token.")
