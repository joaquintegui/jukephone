#!/usr/bin/env python3
"""Script de autenticación Spotify — correr una sola vez en la Mac."""
import os
import json
import webbrowser
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import spotipy
from spotipy.oauth2 import SpotifyOAuth

CLIENT_ID     = os.environ.get('SPOTIPY_CLIENT_ID', '')
REDIRECT_URI  = 'http://127.0.0.1:8888/callback'
CACHE_PATH    = os.path.expanduser('~/.jukephone_spotify_cache')
SCOPE = (
    'streaming '
    'user-read-playback-state '
    'user-modify-playback-state '
    'user-read-currently-playing'
)

code_received = None

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        global code_received
        params = parse_qs(urlparse(self.path).query)
        if 'code' in params:
            code_received = params['code'][0]
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b'<h1>Autenticado! Podes cerrar esta ventana.</h1>')

    def log_message(self, *args):
        pass

if not CLIENT_ID:
    print("ERROR: falta SPOTIPY_CLIENT_ID")
    exit(1)

auth = SpotifyOAuth(
    client_id=CLIENT_ID,
    client_secret='',
    redirect_uri=REDIRECT_URI,
    scope=SCOPE,
    cache_path=CACHE_PATH,
    open_browser=False,
)

url = auth.get_authorize_url()
print(f"\nAbriendo browser para autenticar...\n{url}\n")
webbrowser.open(url)

print("Esperando callback en http://127.0.0.1:8888 ...")
server = HTTPServer(('127.0.0.1', 8888), Handler)
server.handle_request()

if code_received:
    token = auth.get_access_token(code_received, as_dict=False)
    print(f"\nOK — token guardado en {CACHE_PATH}")

    sp = spotipy.Spotify(auth_manager=auth)
    devices = sp.devices()
    nombres = [d['name'] for d in devices.get('devices', [])]
    print(f"Dispositivos activos: {nombres}")
else:
    print("ERROR: no se recibió código de autorización")
