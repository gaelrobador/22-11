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
- **Tocar:** pantalla siguiente (ojitos → hora y clima → QR → días juntos → próximas fechas → frase del día).
- **En los ojitos:** 2 toques = sorpresa · 3 toques = guiño y "te quiero" · 8 toques rápidos = se marea ("¡basta!").
- **Mantener:** caricia (^ ^). Más de 2,5 s: se enamora. Más de 6 s: se duerme de placer y ronronea.
- **Solo, cuando nadie lo toca:** juega con una pelotita, persigue una mariposa, se esconde, te busca, guiña,
  canta o estornuda (cada 1 a 3 minutos). A los 20 minutos se aburre.
- **Momentos especiales:** a las 22:11 fiesta de corazones; el 22 de cada mes más ojitos de corazón;
  en los cumples gorrito y confeti; a las 7 se despierta y dice "¡Buen día!".
- Las fechas importantes se cargan desde la página (Calendario → Fechas importantes) y el robot las baja al arrancar y cada 30 min.
- Para cambiar el QR: `python gen_qr.py "link"` en la PC y copiar el `qr_data.py` nuevo.

Cómo se ven: `pantallas.png` y `escenas.png` (simulación).
