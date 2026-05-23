#!/usr/bin/env python3
"""
Modo música via YouTube Music + Playwright.
Abre Chromium en el escritorio, guarda sesión entre usos.
"""

import os
import json
import queue
import threading
from pathlib import Path
from audio import beep, hablar, hablar_bg

# Necesario para que Chromium abra en el escritorio de la Pi
os.environ.setdefault('DISPLAY', ':0')

DB_PATH     = Path(__file__).parent.parent / 'database.json'
SESSION_PATH = Path.home() / '.ytm_session.json'
CODIGO_SYNC = '12345678'

_q      = queue.Queue()
_ready  = threading.Event()
_thread = None


# ── Interface pública ──────────────────────────────────────────────────────────

def on_modo_activado():
    global _thread
    print("[YTM] Iniciando...")
    _ready.clear()
    _thread = threading.Thread(target=_run_browser, daemon=True)
    _thread.start()
    if _ready.wait(timeout=40):
        print("[YTM] Listo — marcá 8 dígitos para llamar un artista")
    else:
        print("[YTM] Timeout — Chromium tardó demasiado")

def on_modo_desactivado():
    print("[YTM] Cerrando...")
    _q.put(('quit', None))
    _ready.clear()

def on_numero_marcado(numero):
    if numero == CODIGO_SYNC:
        hablar_bg("Actualizando agenda")
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

    print(f"[YTM] Llamando a: {artista}")
    hablar(f"Llamando a {artista}")
    _q.put(('search', artista))

def play_pause():
    _q.put(('key', 'k'))

def siguiente():
    _q.put(('key', 'Shift+N'))

def anterior():
    _q.put(('key', 'Shift+P'))

def subir_volumen():
    _q.put(('key', 'Shift+ArrowUp'))

def bajar_volumen():
    _q.put(('key', 'Shift+ArrowDown'))


# ── Browser loop (corre en hilo separado) ─────────────────────────────────────

def _run_browser():
    from playwright.sync_api import sync_playwright

    with sync_playwright() as p:
        # Usa Chromium del sistema si el de Playwright no está disponible en ARM
        launch_kwargs = dict(
            headless=False,
            args=[
                '--autoplay-policy=no-user-gesture-required',
                '--no-sandbox',
                '--disable-dev-shm-usage',
            ]
        )
        sys_chromium = '/usr/bin/chromium-browser'
        if os.path.exists(sys_chromium):
            launch_kwargs['executable_path'] = sys_chromium

        try:
            browser = p.chromium.launch(**launch_kwargs)
        except Exception as e:
            print(f"[YTM] Error lanzando Chromium: {e}")
            return

        ctx_kwargs = {}
        if SESSION_PATH.exists():
            print("[YTM] Cargando sesión guardada")
            ctx_kwargs['storage_state'] = str(SESSION_PATH)

        context = browser.new_context(**ctx_kwargs)
        page    = context.new_page()
        page.goto('https://music.youtube.com')
        _ready.set()

        while True:
            try:
                cmd, arg = _q.get(timeout=0.2)
            except queue.Empty:
                continue

            if cmd == 'quit':
                _guardar_sesion(context)
                break
            elif cmd == 'key':
                try:
                    page.keyboard.press(arg)
                except Exception as e:
                    print(f"[YTM] Error tecla {arg}: {e}")
            elif cmd == 'search':
                _buscar_y_reproducir(page, arg)

        browser.close()


def _buscar_y_reproducir(page, artista):
    try:
        url = f'https://music.youtube.com/search?q={artista.replace(" ", "+")}'
        page.goto(url)
        page.wait_for_load_state('domcontentloaded', timeout=15000)

        # Intentar clic en resultado tipo "Artista" → shuffle
        artist_section = page.locator('ytmusic-card-shelf-renderer').first
        if artist_section.is_visible(timeout=3000):
            shuffle_btn = artist_section.locator(
                'button[aria-label*="shuffl" i], button[aria-label*="mezcl" i]'
            ).first
            if shuffle_btn.is_visible(timeout=2000):
                shuffle_btn.click()
                print(f"[YTM] Shuffle de artista: {artista}")
                return
            artist_section.click()
            print(f"[YTM] Abriendo artista: {artista}")
            return

        # Fallback: primer resultado de la lista
        first = page.locator('ytmusic-responsive-list-item-renderer').first
        if first.is_visible(timeout=3000):
            first.click()
            print(f"[YTM] Reproduciendo primer resultado: {artista}")
    except Exception as e:
        print(f"[YTM] Error buscando '{artista}': {e}")
        beep(frecuencia=200, duracion=0.3)


def _guardar_sesion(context):
    try:
        context.storage_state(path=str(SESSION_PATH))
        print("[YTM] Sesión guardada")
    except Exception as e:
        print(f"[YTM] Error guardando sesión: {e}")
