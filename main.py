#!/usr/bin/env python3
"""
JukePhone - main.py

Controles:
  Amarillo 1          → Modo música
  Amarillo 2          → Modo juegos (loro)
  Negro 1             → Play / Pause
  Negro 2             → Siguiente canción
  Negro 3             → Canción anterior
  Negro 4 + Negro 2   → Subir volumen
  Negro 4 + Negro 3   → Bajar volumen
  Hook (colgar)       → Audio por bluetooth
  Hook (descolgar)    → Audio por auricular / marcar artistas
  Teclado 8 dígitos   → Llamar artista (modo música, auricular levantado)
"""

import time
from hardware import JukePhoneHardware
from audio import beep, beep_dtmf, set_salida, DEVICE_PARLANTE, DEVICE_TUBO
from modes import music, parrot
import bluetooth_manager

LONGITUD_NUMERO = 8

MODOS = {
    'musica': music,
    'juegos': parrot,
}


def activar_modo(nuevo, actual):
    try:
        if actual in MODOS and hasattr(MODOS[actual], 'on_modo_desactivado'):
            MODOS[actual].on_modo_desactivado()
    except Exception as e:
        print(f"[MAIN] Error desactivando {actual}: {e}")
    try:
        if nuevo in MODOS:
            print(f"[MAIN] Modo: {nuevo}")
            if hasattr(MODOS[nuevo], 'on_modo_activado'):
                MODOS[nuevo].on_modo_activado()
    except Exception as e:
        print(f"[MAIN] Error activando {nuevo}: {e}")


def main():
    hw = JukePhoneHardware()

    modo_actual           = None
    numero_marcado        = ''
    tecla_anterior        = None
    ultimo_tiempo         = 0
    am1_anterior          = False
    am2_anterior          = False
    hook_anterior         = False
    modos_anteriores      = []
    loro_asterisco_activo = False

    print("=" * 40)
    print("  JukePhone - Listo")
    print("=" * 40)

    try:
        while True:
            ahora = time.time()

            # ── Botones negros — reproducción ──────────────────────────────
            try:
                modos  = hw.leer_modos()
                nuevos = [m for m in modos if m not in modos_anteriores]

                if nuevos:
                    if   2 in nuevos and 4 in modos:  music.subir_volumen()
                    elif 3 in nuevos and 4 in modos:  music.bajar_volumen()
                    elif 1 in nuevos and 4 not in modos: music.play_pause()
                    elif 2 in nuevos and 4 not in modos: music.siguiente()
                    elif 3 in nuevos and 4 not in modos: music.anterior()

                modos_anteriores = modos
            except Exception as e:
                print(f"[MAIN] Error botones negros: {e}")
                modos_anteriores = []

            # ── Botones amarillos — selector de modo ───────────────────────
            try:
                am1 = hw.leer_amarillo_1()
                if am1 and not am1_anterior:
                    set_salida(DEVICE_PARLANTE)
                    if modo_actual != 'musica':
                        activar_modo('musica', modo_actual)
                        modo_actual           = 'musica'
                        numero_marcado        = ''
                        loro_asterisco_activo = False
                am1_anterior = am1

                am2 = hw.leer_amarillo_2()
                if am2 and not am2_anterior:
                    set_salida(DEVICE_TUBO)
                    if modo_actual != 'juegos':
                        activar_modo('juegos', modo_actual)
                        modo_actual           = 'juegos'
                        numero_marcado        = ''
                        loro_asterisco_activo = False
                am2_anterior = am2
            except Exception as e:
                print(f"[MAIN] Error amarillos: {e}")

            # ── Hook switch — enrutamiento de audio ────────────────────────
            try:
                hook = hw.auricular_descolgado()
                if hook != hook_anterior:
                    if hook:
                        # Auricular levantado → audio al auricular
                        bluetooth_manager.switch_to_handset()
                        print("[MAIN] Auricular levantado")
                    else:
                        # Colgado → conectar BT y rutear audio
                        print("[MAIN] Auricular colgado")
                        if bluetooth_manager.BT_MAC:
                            bluetooth_manager.connect()
                            bluetooth_manager.switch_to_bluetooth()
                    hook_anterior = hook
            except Exception as e:
                print(f"[MAIN] Error hook: {e}")

            # ── Teclado ────────────────────────────────────────────────────
            try:
                tecla = hw.leer_tecla()
            except Exception as e:
                print(f"[MAIN] Error teclado: {e}")
                tecla = None

            # Loro: detección hold/release de *
            if modo_actual == 'juegos':
                asterisco_ahora = (tecla == '*')
                if asterisco_ahora and not loro_asterisco_activo:
                    loro_asterisco_activo = True
                    parrot.iniciar_grabacion()
                elif not asterisco_ahora and loro_asterisco_activo:
                    loro_asterisco_activo = False
                    parrot.detener_grabacion()

            if tecla and (tecla != tecla_anterior or ahora - ultimo_tiempo > 0.3):
                tecla_anterior = tecla
                ultimo_tiempo  = ahora

                try:
                    if modo_actual is None:
                        beep(frecuencia=300, duracion=0.1)
                        print("[MAIN] Seleccioná un modo (amarillo 1=música, 2=juegos)")

                    elif modo_actual == 'musica':
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

                    elif modo_actual == 'juegos':
                        if tecla == '#':
                            parrot.reproducir()

                except Exception as e:
                    print(f"[MAIN] Error modo {modo_actual}: {e}")
                    numero_marcado = ''

            if not tecla:
                tecla_anterior = None

            time.sleep(0.05)

    except KeyboardInterrupt:
        print("\nApagando JukePhone...")
    finally:
        try:
            if modo_actual in MODOS and hasattr(MODOS[modo_actual], 'on_modo_desactivado'):
                MODOS[modo_actual].on_modo_desactivado()
        except:
            pass
        hw.cleanup()


if __name__ == '__main__':
    main()
