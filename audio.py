#!/usr/bin/env python3
"""
JukePhone - audio.py
Todo el audio pasa por aquí. subprocess.run (bloqueante) para evitar device busy.
"""

import subprocess
import tempfile
import os
import wave
import struct
import math

AUDIO_DEVICE_IN   = 'hw:2,0'
AUDIO_DEVICE_OUT  = 'plughw:1,0'   # default: parlante externo
DEVICE_TUBO       = 'plughw:2,0'
DEVICE_PARLANTE   = 'plughw:1,0'   # parlante externo (jack 3.5mm Pi)

def set_salida(device):
    global AUDIO_DEVICE_OUT
    AUDIO_DEVICE_OUT = device
    print(f"[AUDIO] Salida → {device}")
SAMPLE_RATE      = 44100

DTMF_FREQS = {
    '1': (697, 1209), '2': (697, 1336), '3': (697, 1477),
    '4': (770, 1209), '5': (770, 1336), '6': (770, 1477),
    '7': (852, 1209), '8': (852, 1336), '9': (852, 1477),
    '*': (941, 1209), '0': (941, 1336), '#': (941, 1477),
}

def _generar_wav(frecuencias, duracion, volumen=0.4):
    tmp = tempfile.mktemp(suffix='.wav')
    n = int(SAMPLE_RATE * duracion)
    datos = []
    for i in range(n):
        t = i / SAMPLE_RATE
        muestra = sum(math.sin(2 * math.pi * f * t) for f in frecuencias)
        muestra = int(32767 * volumen * muestra / len(frecuencias))
        datos.append(max(-32768, min(32767, muestra)))
    with wave.open(tmp, 'w') as f:
        f.setnchannels(1); f.setsampwidth(2); f.setframerate(SAMPLE_RATE)
        f.writeframes(struct.pack('<' + 'h' * len(datos), *datos))
    return tmp

def _aplay(archivo, borrar=False):
    """Siempre bloqueante — usa DEVICE_TUBO para todos los sonidos de interfaz"""
    subprocess.run(
        ['aplay', '-D', DEVICE_TUBO, archivo],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
    )
    if borrar and os.path.exists(archivo):
        os.remove(archivo)

def beep_dtmf(tecla, duracion=0.12):
    freqs = DTMF_FREQS.get(tecla, (440, 440))
    tmp = _generar_wav(freqs, duracion)
    _aplay(tmp, borrar=True)

def beep(frecuencia=440, duracion=0.2):
    tmp = _generar_wav([frecuencia], duracion)
    _aplay(tmp, borrar=True)

def beep_en(device, frecuencia=440, duracion=0.2):
    """Beep en un device ALSA específico, ignorando AUDIO_DEVICE_OUT."""
    tmp = _generar_wav([frecuencia], duracion)
    subprocess.run(
        ['aplay', '-D', device, tmp],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
    )
    if os.path.exists(tmp):
        os.remove(tmp)

def reproducir_mp3(archivo):
    """Reproduce mp3 en background (música larga)"""
    return subprocess.Popen(
        ['mpg123', '-a', AUDIO_DEVICE_OUT, archivo],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
    )

def reproducir_wav(archivo):
    """Bloqueante"""
    _aplay(archivo)

def hablar(texto):
    """Bloqueante — espeak → aplay en DEVICE_TUBO"""
    esp = subprocess.Popen(
        ['espeak', '-v', 'es', '-s', '140', '-a', '180', '--stdout', texto],
        stdout=subprocess.PIPE, stderr=subprocess.DEVNULL
    )
    subprocess.run(
        ['aplay', '-D', DEVICE_TUBO],
        stdin=esp.stdout, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
    )
    esp.wait()

def hablar_bg(texto):
    """No bloqueante — espeak → aplay en DEVICE_TUBO"""
    esp = subprocess.Popen(
        ['espeak', '-v', 'es', '-s', '140', '-a', '180', '--stdout', texto],
        stdout=subprocess.PIPE, stderr=subprocess.DEVNULL
    )
    subprocess.Popen(
        ['aplay', '-D', DEVICE_TUBO],
        stdin=esp.stdout, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
    )

def grabar(archivo=None):
    if archivo is None:
        archivo = tempfile.mktemp(suffix='.wav')
    proceso = subprocess.Popen(
        ['arecord', '-D', AUDIO_DEVICE_IN, '-f', 'S16_LE',
         '-r', str(SAMPLE_RATE), '-c', '1', archivo],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
    )
    return archivo, proceso
