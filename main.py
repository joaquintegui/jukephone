#!/usr/bin/env python3
"""
JukePhone - main.py
"""

import time
from hardware import JukePhoneHardware
from audio import beep, beep_dtmf
from modes import music, debug_mode, parrot, misc

LONGITUD_NUMERO = 7
HANDLERS = {1: music, 2: debug_mode, 3: parrot, 4: misc}

def activar_modo(nuevo, actual):
    try:
        if actual is not None and actual in HANDLERS:
            if hasattr(HANDLERS[actual], 'on_modo_desactivado'):
                HANDLERS[actual].on_modo_desactivado()
    except Exception as e:
        print(f"[MAIN] Error desactivando modo {actual}: {e}")
    try:
        if nuevo is not None and nuevo in HANDLERS:
            print(f"[MAIN] Modo {nuevo} activado")
            if hasattr(HANDLERS[nuevo], 'on_modo_activado'):
                HANDLERS[nuevo].on_modo_activado()
    except Exception as e:
        print(f"[MAIN] Error activando modo {nuevo}: {e}")

def main():
    hw = JukePhoneHardware()

    modo_actual    = None
    numero_marcado = ''
    tecla_anterior = None
    ultimo_tiempo  = 0
    am1_anterior   = False
    am2_anterior   = False

    print("=" * 40)
    print("  JukePhone - Listo")
    print("=" * 40)

    try:
        while True:
            ahora = time.time()

            # ── Botones de modo — máxima prioridad ────────────────────────────
            try:
                modos_apretados = hw.leer_modos()
                if modos_apretados:
                    modo_nuevo = modos_apretados[0]
                    if modo_nuevo != modo_actual:
                        activar_modo(modo_nuevo, modo_actual)
                        modo_actual    = modo_nuevo
                        numero_marcado = ''
                        time.sleep(0.4)
                        continue
            except Exception as e:
                print(f"[MAIN] Error modos: {e}")
                modo_actual = None

            # ── Botones amarillos ─────────────────────────────────────────────
            try:
                am1 = hw.leer_amarillo_1()
                if am1 and not am1_anterior:
                    misc.on_amarillo_1()
                am1_anterior = am1

                am2 = hw.leer_amarillo_2()
                if am2 and not am2_anterior:
                    misc.on_amarillo_2()
                am2_anterior = am2
            except Exception as e:
                print(f"[MAIN] Error amarillos: {e}")

            # ── Teclado ───────────────────────────────────────────────────────
            try:
                tecla = hw.leer_tecla()
            except Exception as e:
                print(f"[MAIN] Error teclado: {e}")
                tecla = None

            if tecla and (tecla != tecla_anterior or ahora - ultimo_tiempo > 0.3):
                tecla_anterior = tecla
                ultimo_tiempo  = ahora

                try:
                    if modo_actual is None:
                        beep(frecuencia=300, duracion=0.1)
                        print("[MAIN] Seleccioná un modo primero")

                    elif modo_actual == 1:
                        if tecla == '*':
                            numero_marcado = numero_marcado[:-1]
                            beep(frecuencia=300, duracion=0.1)
                            print(f"[MÚSICA] [{numero_marcado}]")
                        elif tecla != '#':
                            beep_dtmf(tecla)
                            numero_marcado += tecla
                            print(f"[MÚSICA] [{numero_marcado}]")
                            if len(numero_marcado) == LONGITUD_NUMERO:
                                music.on_numero_marcado(numero_marcado)
                                numero_marcado = ''

                    elif modo_actual == 2:
                        print(f"[DEBUG] Tecla: {tecla}")
                        debug_mode.on_tecla(tecla)

                    elif modo_actual == 3:
                        parrot.on_tecla(tecla)

                    elif modo_actual == 4:
                        beep_dtmf(tecla)

                except Exception as e:
                    print(f"[MAIN] Error modo {modo_actual}: {e}")
                    modo_actual    = None
                    numero_marcado = ''

            if not tecla:
                tecla_anterior = None

            time.sleep(0.05)

    except KeyboardInterrupt:
        print("\nApagando JukePhone...")
    finally:
        try:
            if modo_actual in HANDLERS and hasattr(HANDLERS[modo_actual], 'on_modo_desactivado'):
                HANDLERS[modo_actual].on_modo_desactivado()
        except:
            pass
        hw.cleanup()

if __name__ == '__main__':
    main()
