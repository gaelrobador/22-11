# Robotito 22·11

ESP32-C3 SuperMini + OLED 1.3" SH1106 128x64 + sensor táctil TTP223, en MicroPython.
Conexiones en `esquema.jpg`; cómo se ven las pantallas en `pantallas.png` (simulación).

## Cargarlo (siempre con cargar.sh)
El código se **precompila** en la compu (archivos `.mpy`). Si la placa compila los `.py` ella misma,
se queda sin la memoria que necesita la conexión segura y no puede bajar las fechas del álbum.

1. Una sola vez: `pip install mpy-cross mpremote` (en el entorno virtual).
2. Copiá `settings_ejemplo.py` como `settings.py` y completá el Wi-Fi y la clave del álbum
   (`settings.py` no está en GitHub porque lleva contraseñas).
3. Con la placa conectada y minicom cerrado:
```
./cargar.sh
```
Compila, borra los `.py` viejos de la placa, copia `main.py`, `settings.py` y los `.mpy`, y reinicia.

Pruebas: `mpremote connect /dev/ttyACM0 run prueba_fechas.py` (arranque paso a paso con memoria) y
`prueba_https.py` (conexión segura).

## Usarlo
- Tocar: pantalla siguiente (ojitos → hora y clima → QR → días juntos → próximas fechas → frase del día).
- Mantener: caricia. Mucho rato: se enamora. Dos toques en los ojitos: sorpresa.
- Las fechas importantes se cargan desde la página (Calendario → Fechas importantes) y el robot las baja cada 30 min.
- Para cambiar el QR: `python gen_qr.py "link"` en la PC y copiar el `qr_data.py` nuevo.
