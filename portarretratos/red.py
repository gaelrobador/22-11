# Wi-Fi, hora (NTP), clima de Open-Meteo y fechas importantes cargadas en la página (Supabase).
# Todo es "de a una cosa por vez" para que los ojitos no se traben: tarea() se llama en cada vuelta
# del loop y como mucho hace un pedido a internet.
import network, time, json, gc
try:
    import requests
except ImportError:
    import urequests as requests
try:
    import settings as S
except ImportError:
    class S:
        pass


def cfg(n, d):
    return getattr(S, n, d)


ticks, diff, add = time.ticks_ms, time.ticks_diff, time.ticks_add

SB_URL = 'https://gewoffntwuofryqruskd.supabase.co'
SB_KEY = 'sb_publishable_Riz900X7Qp4cgaC5QdUaEA_75SVyhiX'   # pública, la misma que usa la página
SB_EMAIL = 'nosotros@2211.com'
SSID, PASS = cfg('WIFI_SSID', ''), cfg('WIFI_PASS', '')
CLAVE = cfg('ALBUM_CLAVE', '')
TZ = cfg('TZ_HORAS', -3)
INICIO = cfg('INICIO', (2023, 11, 22))

HORA_MS, CLIMA_MS, FECHAS_MS = 6 * 3600000, 15 * 60000, 30 * 60000
TIMEOUT = 10          # segundos: si internet no contesta, se corta y reintenta más tarde (el robot nunca se cuelga)

wlan = network.WLAN(network.STA_IF)
clima = {'temp': None, 'code': 0, 'dia': 1}
fechas = []          # [(nombre, 'AAAA-MM-DD', se_repite)] — se guardan en fechas.json para cuando no hay Wi-Fi
_t = {'conn': None, 'hora': None, 'clima': None, 'fechas': None}


# ---------- Wi-Fi ----------
def iniciar():
    _cargar_fechas()
    if not SSID:
        return
    wlan.active(True)
    try:
        wlan.config(txpower=cfg('WIFI_TXPOWER', 8.5))   # la C3 SuperMini conecta mejor con potencia baja
    except Exception:
        pass
    if wlan.isconnected():                          # ya estaba conectado (ej. después de un Ctrl+D): no lo corto
        _t['conn'] = ticks()
    else:
        _conectar(ticks())


def _conectar(now):
    _t['conn'] = now
    try:
        wlan.connect(SSID, PASS)
    except OSError as e:
        print('wifi:', e)


def configurado():
    return bool(SSID)


def nivel():
    # -1 sin conexión, 0..3 rayitas
    if not SSID or not wlan.isconnected():
        return -1
    try:
        r = wlan.status('rssi')
    except Exception:
        return 3
    return 3 if r > -60 else 2 if r > -70 else 1 if r > -80 else 0


def _vence(k, now, ms):
    return _t[k] is None or diff(now, _t[k]) >= ms


def tarea(now):
    if not SSID:
        return
    if not wlan.isconnected():
        if diff(now, _t['conn']) > 30000:
            _conectar(now)
        return
    try:
        if _vence('hora', now, HORA_MS):
            _hora(now)
        elif CLAVE and _vence('fechas', now, FECHAS_MS):
            _fechas(now)
        elif _vence('clima', now, CLIMA_MS):
            _clima(now)
    except Exception as e:
        print('red:', repr(e))


def arranque(espera_ms=15000):
    # Al prender: espera el Wi-Fi y baja hora, fechas y clima ANTES de que arranquen las animaciones,
    # cuando la memoria está más ordenada (la conexión segura con el álbum necesita un bloque grande).
    if not SSID:
        return
    t0 = ticks()
    while not wlan.isconnected() and diff(ticks(), t0) < espera_ms:
        time.sleep_ms(200)
    if not wlan.isconnected():
        print('red: sin Wi-Fi al arrancar')
        return
    for paso in (_hora, _fechas, _clima):
        if paso is _fechas and not CLAVE:
            continue
        try:
            paso(ticks())
        except Exception as e:
            print('red:', paso.__name__, repr(e))


# ---------- hora ----------
def _hora(now):
    _t['hora'] = add(now, 60000 - HORA_MS)       # si falla, reintenta en 1 minuto
    gc.collect()
    import ntptime
    ntptime.host = 'pool.ntp.org'
    ntptime.settime()
    _t['hora'] = now


def hora_ok():
    return time.localtime()[0] >= 2025


def ahora():
    # (año, mes, día, hora, min, seg, día_semana 0=lunes, ...) en hora de Argentina
    return time.localtime(time.time() + TZ * 3600)


def dnum(y, m, d):
    # número de día, para restar fechas
    return time.mktime((y, m, d, 12, 0, 0, 0, 0)) // 86400


def hoy():
    return dnum(*ahora()[:3])


def es_noche():
    if not hora_ok():
        return False
    a, b = cfg('NOCHE', (0, 7))
    h = ahora()[3]
    return a <= h < b if a < b else (h >= a or h < b)


# ---------- clima ----------
def _clima(now):
    _t['clima'] = add(now, 60000 - CLIMA_MS)
    gc.collect()
    url =('http://api.open-meteo.com/v1/forecast?latitude=%s&longitude=%s'
           '&current=temperature_2m,weather_code,is_day') % (cfg('LAT', -34.86), cfg('LON', -57.91))
    r = requests.get(url, timeout=TIMEOUT)
    try:
        c = r.json()['current']
    finally:
        r.close()
    clima.update(temp=c['temperature_2m'], code=c['weather_code'], dia=c['is_day'])
    _t['clima'] = now


# ---------- fechas de la página ----------
def _fechas(now):
    global fechas
    _t['fechas'] = add(now, 120000 - FECHAS_MS)
    gc.collect()                                  # la conexión segura necesita un bloque de memoria grande
    h = {'apikey': SB_KEY, 'Content-Type': 'application/json'}
    r = requests.post(SB_URL + '/auth/v1/token?grant_type=password', headers=h,
                      data=json.dumps({'email': SB_EMAIL, 'password': CLAVE}), timeout=TIMEOUT)
    try:
        j = r.json()
    finally:
        r.close()
    if 'access_token' not in j:
        raise Exception('no pude entrar al álbum: revisá ALBUM_CLAVE en settings.py')
    h['Authorization'] = 'Bearer ' + j['access_token']
    j = None
    gc.collect()
    r = requests.get(SB_URL + '/rest/v1/fechas?select=nombre,fecha,anual', headers=h, timeout=TIMEOUT)
    try:
        data = r.json()
    finally:
        r.close()
    fechas = [(f['nombre'], f['fecha'], f['anual']) for f in data]
    try:
        with open('fechas.json', 'w') as f:
            json.dump(fechas, f)
    except OSError:
        pass
    _t['fechas'] = now


def _cargar_fechas():
    global fechas
    try:
        with open('fechas.json') as f:
            fechas = [tuple(x) for x in json.load(f)]
    except (OSError, ValueError):
        fechas = []


def proximas(n=3):
    # [(días que faltan, nombre)] ordenadas, empezando por la más cercana
    if not hora_ok():
        return []
    y, m, d = ahora()[:3]
    h = dnum(y, m, d)
    ev = []

    def anual(mm, dd, nombre):
        for yy in (y, y + 1):
            k = dnum(yy, mm, dd) - h
            if k >= 0:
                ev.append((k, nombre(yy) if callable(nombre) else nombre))
                return

    sy, sm, sd = INICIO
    anual(sm, sd, lambda yy: '%d %s juntos ♥' % (yy - sy, 'año' if yy - sy == 1 else 'años'))
    # el 22 de cada mes (menos el del aniversario, que ya está)
    mm, yy = (m, y) if d <= sd else (m % 12 + 1, y + (m == 12))
    if mm != sm:
        ev.append((dnum(yy, mm, sd) - h, 'Nuestro %d ♥' % sd))
    for nombre, f, rep in fechas + list(cfg('FECHAS', [])):
        fy, fm, fd = int(f[:4]), int(f[5:7]), int(f[8:10])
        if rep:
            anual(fm, fd, nombre)
        else:
            k = dnum(fy, fm, fd) - h
            if k >= 0:
                ev.append((k, nombre))
    ev.sort(key=lambda e: e[0])
    return ev[:n]
