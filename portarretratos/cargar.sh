#!/usr/bin/env bash
# Precompila el robotito y lo carga en la placa.
#   ./cargar.sh                (usa /dev/ttyACM0)
#   ./cargar.sh /dev/ttyACM1
# Necesita mpy-cross y mpremote:  pip install mpy-cross mpremote
set -e
P=${1:-/dev/ttyACM0}
cd "$(dirname "$0")"
MODS="robot dibujo red frases qr_data sh1106"
echo "== compilando"
for m in $MODS; do mpy-cross "$m.py"; done
echo "== borrando los .py viejos de la placa (si quedan, la placa los usa en vez de los .mpy)"
mpremote connect "$P" exec "import os
for f in ('robot.py','dibujo.py','red.py','frases.py','qr_data.py','sh1106.py','ssd1306.py'):
    try:
        os.remove(f)
    except OSError:
        pass"
echo "== copiando"
mpremote connect "$P" cp main.py settings.py $(for m in $MODS; do printf '%s.mpy ' "$m"; done) :
echo "== reiniciando"
mpremote connect "$P" reset
echo "listo ♥"
