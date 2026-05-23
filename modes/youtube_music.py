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
from audio import beep, beep_en, hablar, hablar_bg, DEVICE_TUBO

os.environ.setdefault('DISPLAY', ':0')

DB_PATH      = Path(__file__).parent.parent / 'database.json'
SESSION_DIR  = Path.home() / '.ytm_profile'
CODIGO_SYNC  = '12345678'

_q         = queue.Queue()
_ready     = threading.Event()
_thread    = None
_stop_ring = threading.Event()


# ── Interface pública ──────────────────────────────────────────────────────────

def precalentar():
    """Inicia Chromium en background al arrancar main.py, sin bloquear."""
    global _thread
    if _thread and _thread.is_alive():
        return
    print("[YTM] Precalentando Chromium...")
    _thread = threading.Thread(target=_run_browser, daemon=True)
    _thread.start()

def on_modo_activado():
    global _thread
    if not (_thread and _thread.is_alive()):
        _thread = threading.Thread(target=_run_browser, daemon=True)
        _thread.start()
    if not _ready.is_set():
        print("[YTM] Esperando Chromium...")
        _ready.wait(timeout=60)
    print("[YTM] Modo música activo")
    beep(frecuencia=880, duracion=0.1)
    beep(frecuencia=1100, duracion=0.1)

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
    _stop_ring.clear()
    threading.Thread(target=_ring_loop, daemon=True).start()
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


def _ring_loop():
    while not _stop_ring.is_set():
        beep_en(DEVICE_TUBO, frecuencia=480, duracion=0.35)
        if _stop_ring.wait(timeout=0.15):
            break
        beep_en(DEVICE_TUBO, frecuencia=480, duracion=0.35)
        if _stop_ring.wait(timeout=1.8):
            break


# ── Browser loop ───────────────────────────────────────────────────────────────

def _run_browser():
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.chrome.service import Service
    from selenium.webdriver.common.keys import Keys
    from selenium.webdriver.common.by import By

    opts = Options()
    opts.add_argument(f'--user-data-dir={SESSION_DIR}')  # sesión persistente entre reinicios
    opts.add_argument('--no-sandbox')
    opts.add_argument('--disable-dev-shm-usage')
    opts.add_argument('--autoplay-policy=no-user-gesture-required')
    # Ocultar huella de automatización para que Google no bloquee el login
    opts.add_argument('--disable-blink-features=AutomationControlled')
    opts.add_experimental_option('excludeSwitches', ['enable-automation'])
    opts.add_experimental_option('useAutomationExtension', False)

    # Raspberry Pi OS Trixie: 'chromium' | versiones viejas: 'chromium-browser'
    for candidate in ['/usr/bin/chromium', '/usr/bin/chromium-browser']:
        if os.path.exists(candidate):
            opts.binary_location = candidate
            break

    # chromedriver: 'chromium-driver' (Trixie) | 'chromium-chromedriver' (legacy)
    service = Service('/usr/bin/chromedriver')

    try:
        driver = webdriver.Chrome(service=service, options=opts)
    except Exception as e:
        print(f"[YTM] Error lanzando Chromium: {e}")
        return

    # Eliminar el flag navigator.webdriver que Google detecta
    driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
        'source': 'Object.defineProperty(navigator, "webdriver", {get: () => undefined})'
    })

    _ready.set()  # Chromium listo — no esperamos a que cargue la página
    driver.get('https://music.youtube.com')

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
                _js_key(driver, KEY_MAP.get(arg, arg))
            except Exception as e:
                print(f"[YTM] Error tecla {arg}: {e}")
        elif cmd == 'search':
            _buscar_y_reproducir(driver, arg)
            _stop_ring.set()


def _js_key(driver, key):
    driver.execute_script(
        "document.dispatchEvent(new KeyboardEvent('keydown', "
        "{'key': arguments[0], 'bubbles': true, 'cancelable': true}));",
        key
    )

def _buscar_y_reproducir(driver, artista):
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC

    try:
        q = artista.replace(" ", "+")
        driver.get(f'https://music.youtube.com/search?q={q}')
        wait = WebDriverWait(driver, 15)

        # Buscar el botón de play interno del primer resultado (el triángulo chico)
        try:
            play_in_item = wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR,
                    'ytmusic-responsive-list-item-renderer ytmusic-play-button-renderer button, '
                    'ytmusic-responsive-list-item-renderer .play-button-container button'
                ))
            )
            driver.execute_script("arguments[0].click();", play_in_item)
            print(f"[YTM] Click play interno: {artista}")
        except Exception as e:
            # Fallback: click en la fila completa
            print(f"[YTM] Play interno no encontrado ({e}), intentando fila...")
            try:
                first = wait.until(
                    EC.presence_of_element_located((By.TAG_NAME, 'ytmusic-responsive-list-item-renderer'))
                )
                driver.execute_script("arguments[0].click();", first)
                print(f"[YTM] Click en fila: {artista}")
            except Exception as e2:
                print(f"[YTM] Sin resultados para '{artista}': {e2}")
                beep(frecuencia=200, duracion=0.3)
                return

        # Esperar que aparezca el player bar y hacer click en play
        try:
            play_btn = WebDriverWait(driver, 8).until(
                EC.presence_of_element_located((By.CSS_SELECTOR,
                    '#play-pause-button, .play-pause-button'
                ))
            )
            time.sleep(0.5)
            driver.execute_script("arguments[0].click();", play_btn)
            print(f"[YTM] Play: {artista}")
        except Exception as e:
            print(f"[YTM] No encontré botón play, intentando con tecla: {e}")
            time.sleep(3)
            # Último recurso: send_keys real al body
            try:
                driver.find_element(By.TAG_NAME, 'body').click()
                driver.find_element(By.TAG_NAME, 'body').send_keys('k')
            except:
                pass

    except Exception as e:
        print(f"[YTM] Error buscando '{artista}': {e}")
        beep(frecuencia=200, duracion=0.3)
