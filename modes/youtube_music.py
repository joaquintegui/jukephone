#!/usr/bin/env python3
"""
Modo música via YouTube Music + Selenium/Chromium.
"""

import os
import json
import queue
import threading
import time
from pathlib import Path
from audio import beep, hablar, hablar_bg

os.environ.setdefault('DISPLAY', ':0')

DB_PATH      = Path(__file__).parent.parent / 'database.json'
SESSION_DIR  = Path.home() / '.ytm_profile'
CODIGO_SYNC  = '12345678'

_q      = queue.Queue()
_ready  = threading.Event()
_thread = None


# ── Interface pública ──────────────────────────────────────────────────────────

def on_modo_activado():
    global _thread
    print("[YTM] Iniciando Chromium...")
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
    _q.put(('key', 'shift+n'))

def anterior():
    _q.put(('key', 'shift+p'))

def subir_volumen():
    _q.put(('key', 'shift+up'))

def bajar_volumen():
    _q.put(('key', 'shift+down'))


# ── Browser loop ───────────────────────────────────────────────────────────────

def _run_browser():
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.chrome.service import Service
    from selenium.webdriver.common.keys import Keys
    from selenium.webdriver.common.by import By

    opts = Options()
    opts.add_argument(f'--user-data-dir={SESSION_DIR}')  # sesión persistente
    opts.add_argument('--no-sandbox')
    opts.add_argument('--disable-dev-shm-usage')
    opts.add_argument('--autoplay-policy=no-user-gesture-required')
    # Raspberry Pi OS Trixie: 'chromium' | versiones viejas: 'chromium-browser'
    for candidate in ['/usr/bin/chromium', '/usr/bin/chromium-browser']:
        if os.path.exists(candidate):
            opts.binary_location = candidate
            break

    # chromedriver: 'chromium-driver' (Trixie) | 'chromium-chromedriver' (legacy)
    driver_path = '/usr/bin/chromedriver'
    service = Service(driver_path)

    try:
        driver = webdriver.Chrome(service=service, options=opts)
    except Exception as e:
        print(f"[YTM] Error lanzando Chromium: {e}")
        return

    driver.get('https://music.youtube.com')
    _ready.set()

    KEY_MAP = {
        'k':        'k',
        'shift+n':  Keys.SHIFT + 'n',
        'shift+p':  Keys.SHIFT + 'p',
        'shift+up': Keys.SHIFT + Keys.ARROW_UP,
        'shift+down': Keys.SHIFT + Keys.ARROW_DOWN,
    }

    while True:
        try:
            cmd, arg = _q.get(timeout=0.2)
        except queue.Empty:
            continue

        if cmd == 'quit':
            try:
                driver.quit()
            except:
                pass
            break
        elif cmd == 'key':
            try:
                body = driver.find_element(By.TAG_NAME, 'body')
                body.send_keys(KEY_MAP.get(arg, arg))
            except Exception as e:
                print(f"[YTM] Error tecla {arg}: {e}")
        elif cmd == 'search':
            _buscar_y_reproducir(driver, arg)


def _buscar_y_reproducir(driver, artista):
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC

    try:
        url = f'https://music.youtube.com/search?q={artista.replace(" ", "+")}'
        driver.get(url)
        wait = WebDriverWait(driver, 10)

        # Intentar click en sección de artista → shuffle
        try:
            artist_card = wait.until(
                EC.presence_of_element_located((By.TAG_NAME, 'ytmusic-card-shelf-renderer'))
            )
            # Buscar botón shuffle dentro de la card
            btns = artist_card.find_elements(By.TAG_NAME, 'button')
            for btn in btns:
                label = btn.get_attribute('aria-label') or ''
                if 'shuffle' in label.lower() or 'mezcl' in label.lower():
                    btn.click()
                    print(f"[YTM] Shuffle: {artista}")
                    return
            # Si no hay shuffle, click en la card
            artist_card.click()
            print(f"[YTM] Abriendo artista: {artista}")
            return
        except:
            pass

        # Fallback: primer resultado de la lista
        try:
            first = wait.until(
                EC.presence_of_element_located((By.TAG_NAME, 'ytmusic-responsive-list-item-renderer'))
            )
            first.click()
            print(f"[YTM] Primer resultado: {artista}")
        except Exception as e:
            print(f"[YTM] Sin resultados para '{artista}': {e}")
            beep(frecuencia=200, duracion=0.3)

    except Exception as e:
        print(f"[YTM] Error buscando '{artista}': {e}")
        beep(frecuencia=200, duracion=0.3)
