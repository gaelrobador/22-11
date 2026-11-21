# Prueba el arranque real del robot (carga todo y baja las fechas), sin entrar al loop de las animaciones.
#   mpremote connect /dev/ttyACM0 run prueba_fechas.py
import gc, time
import main as M          # carga el robot completo y prende la pantalla (no arranca el loop)
import red as R

gc.collect()
print('memoria python libre con el robot cargado:', gc.mem_free())
R.iniciar()
R.arranque()
print('hora ok:', R.hora_ok(), '| clima:', R.clima)
print('fechas del álbum:', R.fechas)
print('próximas:', R.proximas(5))

# además, una actualización "en caliente" como las que hace cada 30 min
for i in range(300):
    M.ojos.draw(time.ticks_ms())
try:
    R._fechas(time.ticks_ms())
    print('actualización durante las animaciones: ok')
except Exception as e:
    print('actualización durante las animaciones: ERROR', repr(e))
