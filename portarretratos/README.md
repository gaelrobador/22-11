# Robotito 22·11

ESP32-C3 SuperMini + OLED 1.3" SH1106 128x64 + sensor táctil TTP223, en MicroPython.
Conexiones en `esquema.jpg`; cómo se ven las pantallas en `pantallas.png` (simulación).

## Archivos que van a la placa
`main.py`, `dibujo.py`, `red.py`, `frases.py`, `qr_data.py`, `sh1106.py` y `settings.py`.

`settings.py` no está en GitHub porque lleva contraseñas: copiá `settings_ejemplo.py` como
`settings.py` y completá el Wi-Fi y la clave del álbum.

## Cargarlo
```
mpremote cp sh1106.py main.py dibujo.py red.py frases.py qr_data.py settings.py :
mpremote reset
```

## Usarlo
- Tocar: pantalla siguiente (ojitos → hora y clima → QR → días juntos → próximas fechas → frase del día).
- Mantener: caricia. Mucho rato: se enamora. Dos toques en los ojitos: sorpresa.
- Las fechas importantes se cargan desde la página (Calendario → Fechas importantes) y el robot las baja cada 30 min.
- Para cambiar el QR: `python gen_qr.py "link"` en la PC y copiar el `qr_data.py` nuevo.
