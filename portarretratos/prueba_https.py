# Diagnóstico de HTTPS en la placa (no hace falta subirla: se corre con mpremote run).
#   mpremote connect /dev/ttyACM0 run prueba_https.py
import network, time, gc
import settings as S
try:
    import esp32
except ImportError:
    esp32 = None


def memoria(t):
    gc.collect()
    s = 'memoria python libre: %d' % gc.mem_free()
    if esp32:
        try:
            info = esp32.idf_heap_info(esp32.HEAP_DATA)
            s += ' | sistema libre: %d, bloque más grande: %d' % (sum(i[1] for i in info), max(i[2] for i in info))
        except Exception:
            pass
    print(t, s)


w = network.WLAN(network.STA_IF)
w.active(True)
try:
    w.config(txpower=getattr(S, 'WIFI_TXPOWER', 8.5))
except Exception:
    pass
if not w.isconnected():
    w.connect(S.WIFI_SSID, S.WIFI_PASS)
for _ in range(30):
    if w.isconnected():
        break
    time.sleep(1)
print('wifi conectado:', w.isconnected())
memoria('antes:')

import requests
KEY = 'sb_publishable_Riz900X7Qp4cgaC5QdUaEA_75SVyhiX'
for nombre, url in (('open-meteo (https)', 'https://api.open-meteo.com/v1/forecast?latitude=-34.86&longitude=-57.91&current=temperature_2m'),
                    ('supabase   (https)', 'https://gewoffntwuofryqruskd.supabase.co/auth/v1/health')):
    try:
        r = requests.get(url, headers={'apikey': KEY})
        print(nombre, '->', r.status_code, r.text[:60])
        r.close()
    except Exception as e:
        print(nombre, '-> ERROR', repr(e))
    memoria('después:')
