#!/usr/bin/env python3
"""
JukePhone - debug.py
Muestra qué botón se presionó. Salir con Ctrl+C.
"""

import time
import RPi.GPIO as GPIO
from hardware import JukePhoneHardware, PIN_HOOK, PIN_AMARILLO_1, PIN_AMARILLO_2, PIN_MODO

def main():
    hw = JukePhoneHardware()

    print("JukePhone DEBUG — presioná botones. Ctrl+C para salir.\n")

    hook_prev     = False
    am1_prev      = False
    am2_prev      = False
    negros_prev   = set()
    tecla_prev    = None

    try:
        while True:
            # Hook
            hook = GPIO.input(PIN_HOOK) == GPIO.LOW
            if hook and not hook_prev:
                print("Hook: auricular levantado")
            elif not hook and hook_prev:
                print("Hook: auricular colgado")
            hook_prev = hook

            # Amarillos
            am1 = GPIO.input(PIN_AMARILLO_1) == GPIO.LOW
            if am1 and not am1_prev:
                print("Amarillo 1 presionado")
            am1_prev = am1

            am2 = GPIO.input(PIN_AMARILLO_2) == GPIO.LOW
            if am2 and not am2_prev:
                print("Amarillo 2 presionado")
            am2_prev = am2

            # Botones negros
            negros = {n for n, pin in PIN_MODO.items() if GPIO.input(pin) == GPIO.LOW}
            for n in negros - negros_prev:
                print(f"Negro {n} presionado")
            negros_prev = negros

            # Teclado
            tecla = hw.leer_tecla()
            if tecla and tecla != tecla_prev:
                print(f"Tecla: {tecla}")
            tecla_prev = tecla

            time.sleep(0.05)

    except KeyboardInterrupt:
        print("\nDebug terminado.")
    finally:
        hw.cleanup()

if __name__ == '__main__':
    main()
