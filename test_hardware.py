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

PIN_NEGROS   = {1: 23, 2: 24, 3: 26, 4: 9}
PIN_AM1      = 17
PIN_AM2      = 27
PIN_HOOK     = 4

# ── Setup GPIO ────────────────────────────────────────────────────────────────

GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)
GPIO.cleanup()

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
        time.sleep(0.010)
        detectado = GPIO.input(pin_b) == GPIO.LOW
        GPIO.output(pin_a, GPIO.HIGH)
        GPIO.setup(pin_a, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        if detectado:
            return tecla
    return None

def leer_tecla():
    primera = scan_tecla()
    if not primera:
        return None
    for _ in range(3):
        time.sleep(0.040)
        if scan_tecla() != primera:
            return None
    return primera

def negros_activos():
    return [n for n, pin in PIN_NEGROS.items() if GPIO.input(pin) == GPIO.LOW]

# ── Estado previo ─────────────────────────────────────────────────────────────

tecla_anterior  = None
ultimo_tecla    = 0
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
        ahora = time.time()

        # Teclado
        tecla = leer_tecla()
        if tecla and (tecla != tecla_anterior or ahora - ultimo_tecla > 0.3):
            print(f"[TECLADO]   '{tecla}'")
            tecla_anterior = tecla
            ultimo_tecla   = ahora
        if not tecla:
            tecla_anterior = None

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

        time.sleep(0.05)

except KeyboardInterrupt:
    print("\nTest terminado.")
finally:
    GPIO.cleanup()
