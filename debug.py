#!/usr/bin/env python3
"""
JukePhone - debug.py

Muestra en tiempo real el estado de todos los botones, teclado y hook.
Correr en la Pi: python3 debug.py
Salir con Ctrl+C
"""

import time
import RPi.GPIO as GPIO
from hardware import (
    JukePhoneHardware,
    PIN_HOOK, PIN_AMARILLO_1, PIN_AMARILLO_2, PIN_MODO, PINES_TECLADO, TECLAS
)

def main():
    hw = JukePhoneHardware()

    print("=" * 50)
    print("  JukePhone DEBUG — presioná botones para probar")
    print("  Ctrl+C para salir")
    print("=" * 50)
    print()

    estado_anterior = {}

    try:
        while True:
            estado = {}

            # Hook
            estado['hook'] = GPIO.input(PIN_HOOK) == GPIO.LOW

            # Amarillos
            estado['amarillo_1'] = GPIO.input(PIN_AMARILLO_1) == GPIO.LOW
            estado['amarillo_2'] = GPIO.input(PIN_AMARILLO_2) == GPIO.LOW

            # Botones negros (modos)
            for n, pin in PIN_MODO.items():
                estado[f'negro_{n}'] = GPIO.input(pin) == GPIO.LOW

            # Teclado
            estado['tecla'] = hw.leer_tecla()

            # Detectar cambios y loguear
            for key, val in estado.items():
                prev = estado_anterior.get(key)

                if key == 'tecla':
                    if val and val != prev:
                        print(f"  [TECLADO]    Tecla presionada: [{val}]")
                else:
                    if val and not prev:
                        nombre = {
                            'hook':       'Hook switch    (auricular levantado)',
                            'amarillo_1': 'Amarillo 1     (modo música)',
                            'amarillo_2': 'Amarillo 2     (modo juegos)',
                            'negro_1':    'Negro 1        (play/pause)',
                            'negro_2':    'Negro 2        (siguiente)',
                            'negro_3':    'Negro 3        (anterior)',
                            'negro_4':    'Negro 4        (modificador volumen)',
                        }.get(key, key)
                        print(f"  [PRESIONADO] {nombre}")
                    elif not val and prev:
                        if key not in ('tecla',):
                            pass  # silencioso al soltar — comentar si querés ver releases

            estado_anterior = dict(estado)
            time.sleep(0.05)

    except KeyboardInterrupt:
        print("\nDebug terminado.")
    finally:
        hw.cleanup()


if __name__ == '__main__':
    main()
