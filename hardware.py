#!/usr/bin/env python3
"""
JukePhone - hardware.py
"""

import RPi.GPIO as GPIO
import time

# ── Teclado ───────────────────────────────────────────────────────────────────
PINES_TECLADO = {
    'AMA1':  5,   # pin 29
    'AMA2':  6,   # pin 31
    'GRIS1': 12,  # pin 32
    'VIO':   13,  # pin 33
    'MARRON':19,  # pin 35
    'NARAN': 16,  # pin 36
    'AZUL':  20,  # pin 38
    'GRIS2': 21,  # pin 40
    'ROJO':  25,  # pin 22
}

TECLAS = [
    ('AMA1',  'VIO',   '0'),
    ('MARRON','GRIS1', '1'),
    ('MARRON','VIO',   '2'),
    ('MARRON','NARAN', '3'),
    ('AMA2',  'GRIS1', '4'),
    ('AMA2',  'VIO',   '5'),
    ('AMA2',  'NARAN', '6'),
    ('AZUL',  'GRIS1', '7'),
    ('AZUL',  'VIO',   '8'),
    ('AZUL',  'NARAN', '9'),
    ('AMA1',  'NARAN', '#'),
    ('GRIS2', 'ROJO',  '*'),
]

# ── Modos (botones negros) ────────────────────────────────────────────────────
PIN_MODO = {1: 23, 2: 24, 3: 26, 4: 9}

# ── Hook switch ───────────────────────────────────────────────────────────────
PIN_HOOK     = 4   # Verde → físico 7
PIN_HOOK_GND = 14  # Negro → físico 8 (configurado como OUTPUT LOW)

# ── Botones amarillos ─────────────────────────────────────────────────────────
PIN_AMARILLO_1 = 17   # Blanco → físico 11
PIN_AMARILLO_2 = 27   # Verde  → físico 13
# Común azul → GND físico 9


class JukePhoneHardware:

    def __init__(self):
        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)
        GPIO.cleanup()
        self._setup()

    def _setup(self):
        # Teclado
        for pin in PINES_TECLADO.values():
            GPIO.setup(pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        # Modos
        for pin in PIN_MODO.values():
            GPIO.setup(pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        # Amarillos
        GPIO.setup(PIN_AMARILLO_1, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        GPIO.setup(PIN_AMARILLO_2, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        # Hook
        GPIO.setup(PIN_HOOK_GND, GPIO.OUT)
        GPIO.output(PIN_HOOK_GND, GPIO.LOW)
        GPIO.setup(PIN_HOOK, GPIO.IN, pull_up_down=GPIO.PUD_UP)

    def leer_tecla(self):
        primera = self._scan_tecla()
        if not primera:
            return None
        # Requiere 4 lecturas consecutivas idénticas con 40ms entre c/u (~160ms total)
        for _ in range(3):
            time.sleep(0.040)
            if self._scan_tecla() != primera:
                return None
        return primera

    def _scan_tecla(self):
        for cable_a, cable_b, tecla in TECLAS:
            pin_a = PINES_TECLADO[cable_a]
            pin_b = PINES_TECLADO[cable_b]
            GPIO.setup(pin_a, GPIO.OUT)
            GPIO.output(pin_a, GPIO.LOW)
            GPIO.setup(pin_b, GPIO.IN, pull_up_down=GPIO.PUD_UP)
            time.sleep(0.010)   # 10ms settle — reduce crosstalk
            detectado = GPIO.input(pin_b) == GPIO.LOW
            GPIO.output(pin_a, GPIO.HIGH)
            GPIO.setup(pin_a, GPIO.IN, pull_up_down=GPIO.PUD_UP)
            if detectado:
                return tecla
        return None

    def leer_modos(self):
        """Devuelve lista de modos actualmente apretados (1-4)"""
        return [n for n, pin in PIN_MODO.items() if GPIO.input(pin) == GPIO.LOW]

    def leer_amarillo_1(self):
        return GPIO.input(PIN_AMARILLO_1) == GPIO.LOW

    def leer_amarillo_2(self):
        return GPIO.input(PIN_AMARILLO_2) == GPIO.LOW

    def auricular_descolgado(self):
        return GPIO.input(PIN_HOOK) == GPIO.HIGH

    def cleanup(self):
        GPIO.cleanup()
