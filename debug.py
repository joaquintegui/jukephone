#!/usr/bin/env python3
"""
JukePhone - debug.py
Muestra qué botón se presionó. Salir con Ctrl+C.
"""

import sys
import time
sys.stdout.reconfigure(line_buffering=True)
import RPi.GPIO as GPIO
from hardware import JukePhoneHardware, PIN_HOOK, PIN_AMARILLO_1, PIN_AMARILLO_2, PIN_MODO

# Cantidad de lecturas consecutivas iguales para confirmar (50ms c/u = 150ms total)
LECTURAS_REQUERIDAS = 3

def main():
    hw = JukePhoneHardware()

    print("JukePhone DEBUG — presioná botones. Ctrl+C para salir.\n")

    # Estado confirmado (lo que ya se reportó)
    hook_conf   = False
    am1_conf    = False
    am2_conf    = False
    negros_conf = set()
    tecla_conf  = None

    # Contadores de lecturas estables
    hook_cnt        = 0
    am1_cnt         = 0
    am2_cnt         = 0
    negros_cnt      = {}   # n -> count
    tecla_raw_prev  = None
    tecla_cnt       = 0

    try:
        while True:
            # ── Hook ──────────────────────────────────────────────────────────
            hook_raw = GPIO.input(PIN_HOOK) == GPIO.LOW
            if hook_raw == hook_conf:
                hook_cnt = 0
            else:
                hook_cnt += 1
                if hook_cnt >= LECTURAS_REQUERIDAS:
                    hook_conf = hook_raw
                    hook_cnt  = 0
                    print("Hook: auricular levantado" if hook_raw else "Hook: auricular colgado")

            # ── Amarillo 1 ────────────────────────────────────────────────────
            am1_raw = GPIO.input(PIN_AMARILLO_1) == GPIO.LOW
            if am1_raw == am1_conf:
                am1_cnt = 0
            else:
                am1_cnt += 1
                if am1_cnt >= LECTURAS_REQUERIDAS:
                    am1_conf = am1_raw
                    am1_cnt  = 0
                    if am1_raw:
                        print("Amarillo 1 presionado")

            # ── Amarillo 2 ────────────────────────────────────────────────────
            am2_raw = GPIO.input(PIN_AMARILLO_2) == GPIO.LOW
            if am2_raw == am2_conf:
                am2_cnt = 0
            else:
                am2_cnt += 1
                if am2_cnt >= LECTURAS_REQUERIDAS:
                    am2_conf = am2_raw
                    am2_cnt  = 0
                    if am2_raw:
                        print("Amarillo 2 presionado")

            # ── Botones negros ────────────────────────────────────────────────
            negros_raw = {n for n, pin in PIN_MODO.items() if GPIO.input(pin) == GPIO.LOW}
            todos = set(negros_raw) | set(negros_conf)
            for n in todos:
                raw_on  = n in negros_raw
                conf_on = n in negros_conf
                if raw_on == conf_on:
                    negros_cnt[n] = 0
                else:
                    negros_cnt[n] = negros_cnt.get(n, 0) + 1
                    if negros_cnt[n] >= LECTURAS_REQUERIDAS:
                        negros_cnt[n] = 0
                        if raw_on:
                            negros_conf.add(n)
                            print(f"Negro {n} presionado")
                        else:
                            negros_conf.discard(n)

            # ── Teclado ───────────────────────────────────────────────────────
            tecla_raw = hw.leer_tecla()
            if tecla_raw != tecla_raw_prev:
                tecla_cnt     = 1
                tecla_raw_prev = tecla_raw
            else:
                tecla_cnt += 1

            if tecla_cnt == LECTURAS_REQUERIDAS:
                if tecla_raw != tecla_conf:
                    tecla_conf = tecla_raw
                    if tecla_raw:
                        print(f"Tecla: {tecla_raw}")

            time.sleep(0.05)

    except KeyboardInterrupt:
        print("\nDebug terminado.")
    finally:
        hw.cleanup()

if __name__ == '__main__':
    main()
