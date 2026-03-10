# JukePhone — Contexto del Proyecto

## Concepto
Teléfono Siemens S30058-S5592 (fabricado en Argentina, militar/institucional, años 70-80) convertido en instalación artística. Controlado por una Raspberry Pi (hostname: `jukephone`).

**Flujo de uso:**
1. Apretar botón negro para seleccionar modo
2. Levantar auricular (hook switch — pendiente de integrar)
3. Interactuar según el modo activo
4. Cambiar de modo apretando otro botón negro

---

## Hardware

### Raspberry Pi
- Hostname: `jukephone`
- SSH: `ssh joaquin@jukephone.local`
- Deploy: `ssh joaquin@jukephone.local "~/update.sh"` (hace git pull)
- Repo: `~/jukephone` en la Raspberry
- Low voltage warning — necesita cargador 5V/3A mínimo

### Audio
- Sound card USB: HF-001D
- Device entrada (micrófono): `hw:2,0`
- Device salida (parlante auricular): `plughw:2,0`
- Reproducir WAV: `aplay -D plughw:2,0 archivo.wav`
- Reproducir MP3: `mpg123 -a plughw:2,0 archivo.mp3`
- Grabar: `arecord -D hw:2,0 -f S16_LE -r 44100 -c 1 archivo.wav`
- **IMPORTANTE:** Solo un proceso puede usar el device a la vez. Todos los beeps usan `subprocess.run` (bloqueante). Solo `reproducir_mp3` usa `Popen`.

### Teclado matricial (chip AMI8129)
Matriz no-estándar — se configura dinámicamente un pin como OUTPUT LOW y el otro como INPUT con pull-up.

| Cable | GPIO BCM | Pin físico |
|-------|----------|------------|
| Amarillo | GPIO 5 | 29 |
| Marrón | GPIO 6 | 31 |
| Gris | GPIO 12 | 32 |
| Azul | GPIO 13 | 33 |
| Rojo | GPIO 19 | 35 |
| Verde | GPIO 16 | 36 |
| Violeta | GPIO 20 | 38 |
| Naranja | GPIO 21 | 40 |
| Negro | GPIO 25 | 22 |

Mapa de teclas:
```python
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
```

### Botones negros (4 modos)
Switches momentáneos — enclavamiento por software.
Común gris → GND físico 20

| Botón | Cable | GPIO BCM | Pin físico | Modo |
|-------|-------|----------|------------|------|
| 1 | Rojo1 | GPIO 23 | 16 | Música |
| 2 | Rojo2 | GPIO 24 | 18 | Debug |
| 3 | Naranja | GPIO 26 | 37 | Loro |
| 4 | Blanco | GPIO 9 | 21 | Misc |

### Botones amarillos (2 botones)
Común azul → GND físico 9

| Botón | Cable | GPIO BCM | Pin físico |
|-------|-------|----------|------------|
| Amarillo 1 | Blanco | GPIO 17 | 11 |
| Amarillo 2 | Verde | GPIO 27 | 13 |

Las lámparas integradas son **incandescencia** (~160Ω), necesitan 9V mínimo.
Control futuro: transistor BC547 + resistencia 1kΩ desde GPIO + fuente 9V externa.

### Hook switch (colgar/descolgar)
- Cable verde → GPIO 4, pin físico 7
- Cable negro → GND, pin físico 6
- **Actualmente comentado en el código** — pendiente de integrar

### Bobina R374
- Número de parte: Y 38027 / X-5912-X-1 (Siemens)
- Función: timbre/señal de llamada
- Pendiente de integrar

---

## Estructura de archivos

```
jukephone/
├── CLAUDE.md
├── main.py           → loop principal
├── hardware.py       → toda la lógica GPIO
├── audio.py          → grabación, reproducción, beeps, TTS
├── database.json     → mapa números (7 dígitos) → artistas
├── Seminare.mp3      → canción de prueba para modo 4
└── modes/
    ├── __init__.py
    ├── music.py      → modo 1: música
    ├── debug_mode.py → modo 2: debug con voz
    ├── parrot.py     → modo 3: loro
    └── misc.py       → modo 4: reproduce Seminare.mp3
```

---

## Lógica principal (main.py)

- Botones de modo tienen **máxima prioridad** — interrumpen cualquier modo activo
- Cambiar de modo llama `on_modo_desactivado()` del modo anterior y `on_modo_activado()` del nuevo
- Todos los bloques están en try/except — un error vuelve a `modo_actual = None`
- El teclado usa debounce de 0.3s

---

## Modos

### Modo 1 — Música
- Marcá 7 dígitos → busca en `database.json` → reproduce artista
- `*` borra último dígito
- `#` ignorado
- Al llegar a 7 dígitos busca automáticamente y limpia el número
- **TODO:** integrar Spotify con spotipy (código comentado en music.py)

### Modo 2 — Debug
- Cada tecla es anunciada por voz (espeak en español) y logueada en CLI
- Útil para verificar que todos los inputs funcionan

### Modo 3 — Loro
- `*` inicia grabación
- `#` reproduce lo grabado
- Podés grabar y reproducir múltiples veces

### Modo 4 — Misc
- Al activarse reproduce `~/Seminare.mp3`
- Al cambiar de modo para la música
- Botones amarillos: beep simple (Do y Mi)

---

## Audio — reglas importantes

```python
# BIEN — bloqueante, espera que termine
subprocess.run(['aplay', '-D', 'plughw:2,0', archivo])

# MAL para beeps — deja el device ocupado
subprocess.Popen(['aplay', '-D', 'plughw:2,0', archivo])

# OK para música larga (mp3)
subprocess.Popen(['mpg123', '-a', 'plughw:2,0', archivo])
```

Tonos DTMF reales implementados en `audio.py` — dos frecuencias mezcladas por tecla.
TTS usa `espeak -v es` directamente (pyttsx3 no funciona bien en Raspberry).

---

## Dependencias

```bash
sudo apt install espeak mpg123 -y
pip install RPi.GPIO --break-system-packages
```

---

## Pendientes

- [ ] Integrar hook switch (colgar/descolgar auricular)
- [ ] Integrar Spotify (spotipy) en music.py
- [ ] Control de lámparas amarillas con transistor BC547 + 9V
- [ ] Integrar bobina R374 para timbre
- [ ] Implementar modos reales para amarillo 1 (Bluetooth) y amarillo 2 (manos libres)
- [ ] Resolver low voltage warning (conseguir cargador 5V/3A)

