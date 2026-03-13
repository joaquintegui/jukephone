#!/usr/bin/env python3
"""
JukePhone - bluetooth_manager.py

Setup inicial del parlante bluetooth (una sola vez desde la Raspberry):
  sudo bluetoothctl
  > power on
  > agent on
  > scan on                        ← esperar que aparezca el parlante
  > pair   XX:XX:XX:XX:XX:XX
  > trust  XX:XX:XX:XX:XX:XX
  > connect XX:XX:XX:XX:XX:XX
  > quit

  Luego cargar la MAC en BT_MAC abajo.

Requisitos PulseAudio:
  sudo apt install pulseaudio pulseaudio-module-bluetooth -y
  sudo adduser joaquin bluetooth
  (reiniciar)
"""

import subprocess
import time

# Completar con la MAC del parlante después de parear
BT_MAC = None   # ej. "AA:BB:CC:DD:EE:FF"


def _run(*args, timeout=10):
    try:
        return subprocess.run(
            list(args), capture_output=True, text=True, timeout=timeout
        ).stdout
    except Exception as e:
        print(f"[BT] Error ejecutando {args[0]}: {e}")
        return ''


def connect():
    if not BT_MAC:
        print("[BT] BT_MAC no configurada — editar bluetooth_manager.py")
        return False
    print(f"[BT] Conectando {BT_MAC}...")
    out = _run('bluetoothctl', 'connect', BT_MAC)
    ok  = 'Connection successful' in out or 'Connected: yes' in out
    if ok:
        time.sleep(1)   # dar tiempo al sink de PulseAudio
        print("[BT] Conectado")
    else:
        print(f"[BT] Fallo: {out.strip()}")
    return ok


def disconnect():
    if not BT_MAC:
        return
    _run('bluetoothctl', 'disconnect', BT_MAC)
    print("[BT] Desconectado")


def _find_sink(keyword):
    out = _run('pactl', 'list', 'sinks', 'short')
    for line in out.splitlines():
        if keyword.lower() in line.lower():
            parts = line.split()
            if len(parts) >= 2:
                return parts[1]
    return None


def switch_to_bluetooth():
    sink = _find_sink('bluez')
    if sink:
        _run('pactl', 'set-default-sink', sink)
        print(f"[BT] Audio → bluetooth ({sink})")
        return True
    print("[BT] Sink bluetooth no encontrado (¿está conectado?)")
    return False


def switch_to_handset():
    sink = _find_sink('usb') or _find_sink('hf-001d')
    if sink:
        _run('pactl', 'set-default-sink', sink)
        print(f"[BT] Audio → auricular ({sink})")
        return True
    print("[BT] Sink USB no encontrado")
    return False
