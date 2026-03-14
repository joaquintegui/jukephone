#!/usr/bin/env python3
"""
JukePhone - hardware.py
"""

import RPi.GPIO as GPIO
import time

# ── Teclado ───────────────────────────────────────────────────────────────────
PINES_TECLADO = {
    'Amarillo_t': 5,
    'Marron':     6,
    'Gris_t':     12,
    'Azul_t':     13,
    'Rojo_t':     19,
    'Verde_t':    16,
    'Violeta':    20,
    'Naranja_t':  21,
    'Negro_t':    25,
}

TECLAS = [
    ('Amarillo_t', 'Naranja_t', '4'),
    ('Amarillo_t', 'Verde_t',   '1'),
    ('Amarillo_t', 'Azul_t',    '7'),
    ('Rojo_t',     'Verde_t',   '3'),
    ('Rojo_t',     'Naranja_t', '6'),
    ('Rojo_t',     'Azul_t',    '9'),
    ('Rojo_t',     'Negro_t',   '#'),
    ('Azul_t',     'Violeta',   '8'),
    ('Marron',     'Gris_t',    '*'),
    ('Negro_t',    'Violeta',   '0'),
    ('Verde_t',    'Violeta',   '2'),
    ('Naranja_t',  'Violeta',   '5'),
]

# ── Modos (botones negros) ────────────────────────────────────────────────────
PIN_MODO = {1: 23, 2: 24, 3: 26, 4: 9}

# ── Hook switch ───────────────────────────────────────────────────────────────
PIN_HOOK = 4  # Verde → físico 7 | Negro → GND físico 6

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
        GPIO.setup(PIN_HOOK, GPIO.IN, pull_up_down=GPIO.PUD_UP)

    def leer_tecla(self):
        primera = self._scan_tecla()
        if not primera:
            return None
        # Requiere 4 lecturas consecutivas idénticas con 60ms entre c/u (~240ms total)
        for _ in range(3):
            time.sleep(0.060)
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
        return GPIO.input(PIN_HOOK) == GPIO.LOW

    def cleanup(self):
        GPIO.cleanup()
