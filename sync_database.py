#!/usr/bin/env python3
"""
JukePhone - sync_database.py

Descarga la agenda de artistas desde Google Sheets y actualiza database.json.
Correr manualmente o via cron cada hora:
  0 * * * * /usr/bin/python3 /home/joaquin/jukephone/sync_database.py
"""

import csv
import json
import os
import urllib.request

CSV_URL  = 'https://docs.google.com/spreadsheets/d/1JE9yUDGILIR8YZlaOYGm5l-Ay8wsqpnEun01Qg34qJs/export?format=csv&gid=0'
DB_PATH  = os.path.join(os.path.dirname(__file__), 'database.json')


def sync():
    print('[SYNC] Descargando agenda desde Google Sheets...')
    try:
        with urllib.request.urlopen(CSV_URL, timeout=15) as resp:
            contenido = resp.read().decode('utf-8')
    except Exception as e:
        print(f'[SYNC] Error descargando: {e}')
        return False

    artists = {}
    reader = csv.DictReader(contenido.splitlines())
    for fila in reader:
        codigo  = str(fila.get('codigo', '')).strip()
        artista = str(fila.get('artista', '')).strip()
        if codigo and artista:
            artists[codigo] = artista

    if not artists:
        print('[SYNC] Hoja vacía o sin columnas "codigo"/"artista" — no se actualiza')
        return False

    with open(DB_PATH, 'w') as f:
        json.dump({'artists': artists}, f, ensure_ascii=False, indent=2)

    print(f'[SYNC] {len(artists)} artistas guardados en database.json')
    for codigo, artista in artists.items():
        print(f'  {codigo} → {artista}')
    return True


if __name__ == '__main__':
    sync()
