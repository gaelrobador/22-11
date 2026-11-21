# Prueba paso a paso (con robot.mpy ya cargado en la placa) del arranque del robot, para ver dónde falla o se traba.
#   mpremote connect /dev/ttyACM0 run prueba_fechas.py
# Cada línea muestra los segundos desde el inicio. Si se queda trabada, la última línea dice en qué paso.
import gc, time
try:
    import esp32
except ImportError:
    esp32 = None
T0 = time.ticks_ms()


def paso(msg):
    gc.collect()
    s = ''
    if esp32:
        try:
            info = esp32.idf_heap_info(esp32.HEAP_DATA)
            s = ' | sistema: %d (bloque %d)' % (sum(i[1] for i in info), max(i[2] for i in info))
        except Exception:
            pass
    print('%5.1fs  %-28s python: %d%s' % (time.ticks_diff(time.ticks_ms(), T0) / 1000, msg, gc.mem_free(), s))


paso('inicio')
import red as R
paso('red cargado')
R.iniciar()
for _ in range(75):
    if R.wlan.isconnected():
        break
    time.sleep_ms(200)
paso('wifi conectado: %s' % R.wlan.isconnected())

for nombre, f in (('hora', R._hora), ('fechas (sin pantalla)', R._fechas)):
    paso('-> ' + nombre)
    try:
        f(time.ticks_ms())
        paso('   ok')
    except Exception as e:
        paso('   ERROR ' + repr(e))

import robot as M                     # ahora carga el robot completo y prende la pantalla
paso('robot cargado')
for i in range(200):
    M.ojos.draw(time.ticks_ms())
paso('animaciones')
paso('-> fechas (con el robot)')
try:
    R._fechas(time.ticks_ms())
    paso('   ok')
except Exception as e:
    paso('   ERROR ' + repr(e))
print('fechas:', R.fechas)
print('próximas:', R.proximas(5))
