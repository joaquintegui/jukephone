#!/usr/bin/env python3
"""
Correr en la Pi para verificar que todos los inputs funcionan.
    python3 test_hardware.py

Ctrl+C para salir.
"""

import time
import RPi.GPIO as GPIO

# ── Pines ─────────────────────────────────────────────────────────────────────

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
    ('AMA2',  'GRIS1', '3'),
    ('AMA2',  'VIO',   '4'),
    ('MARRON','NARAN', '5'),
    ('AMA2',  'NARAN', '6'),
    ('AZUL',  'GRIS1', '7'),
    ('AZUL',  'VIO',   '8'),
    ('AZUL',  'NARAN', '9'),
    ('AMA1',  'NARAN', '#'),
    ('GRIS2', 'ROJO',  '*'),
]

PIN_NEGROS   = {1: 23, 2: 24, 3: 26, 4: 9}
PIN_AM1      = 17
PIN_AM2      = 27
PIN_HOOK     = 4

# ── Setup GPIO ────────────────────────────────────────────────────────────────

GPIO.cleanup()
GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)

for pin in PINES_TECLADO.values():
    GPIO.setup(pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
for pin in PIN_NEGROS.values():
    GPIO.setup(pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(PIN_AM1,  GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(PIN_AM2,  GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(PIN_HOOK, GPIO.IN, pull_up_down=GPIO.PUD_UP)

# ── Helpers ───────────────────────────────────────────────────────────────────

def scan_tecla():
    for cable_a, cable_b, tecla in TECLAS:
        pin_a = PINES_TECLADO[cable_a]
        pin_b = PINES_TECLADO[cable_b]
        GPIO.setup(pin_a, GPIO.OUT)
        GPIO.output(pin_a, GPIO.LOW)
        GPIO.setup(pin_b, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        detectado = GPIO.input(pin_b) == GPIO.LOW
        GPIO.output(pin_a, GPIO.HIGH)
        GPIO.setup(pin_a, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        if detectado:
            return tecla
    return None

def negros_activos():
    return [n for n, pin in PIN_NEGROS.items() if GPIO.input(pin) == GPIO.LOW]

# ── Estado previo ─────────────────────────────────────────────────────────────

tecla_anterior  = None
negros_prev     = []
am1_prev        = False
am2_prev        = False
hook_prev       = GPIO.input(PIN_HOOK) == GPIO.LOW

print("=" * 42)
print("  JukePhone — Test de hardware")
print("  Presioná botones y teclas")
print("  Ctrl+C para salir")
print("=" * 42)

estado_inicial_hook = "DESCOLGADO" if hook_prev else "COLGADO"
print(f"[HOOK] Estado inicial: {estado_inicial_hook}")

try:
    while True:
        # Teclado
        tecla = scan_tecla()
        if tecla != tecla_anterior:
            if tecla:
                print(f"[TECLADO]   '{tecla}'")
            tecla_anterior = tecla

        # Botones negros
        negros = negros_activos()
        nuevos = [n for n in negros if n not in negros_prev]
        sueltos = [n for n in negros_prev if n not in negros]
        for n in nuevos:
            print(f"[NEGRO {n}]   presionado")
        for n in sueltos:
            print(f"[NEGRO {n}]   suelto")
        negros_prev = negros

        # Botón amarillo 1
        am1 = GPIO.input(PIN_AM1) == GPIO.LOW
        if am1 and not am1_prev:
            print("[AMARILLO 1] presionado")
        elif not am1 and am1_prev:
            print("[AMARILLO 1] suelto")
        am1_prev = am1

        # Botón amarillo 2
        am2 = GPIO.input(PIN_AM2) == GPIO.LOW
        if am2 and not am2_prev:
            print("[AMARILLO 2] presionado")
        elif not am2 and am2_prev:
            print("[AMARILLO 2] suelto")
        am2_prev = am2

        # Hook switch
        hook = GPIO.input(PIN_HOOK) == GPIO.LOW
        if hook and not hook_prev:
            print("[HOOK]       auricular DESCOLGADO")
        elif not hook and hook_prev:
            print("[HOOK]       auricular COLGADO")
        hook_prev = hook

except KeyboardInterrupt:
    print("\nTest terminado.")
finally:
    GPIO.cleanup()
