# Robotito 22·11: ESP32-C3 SuperMini + OLED 1.3" SH1106 128x64 (I2C) + sensor táctil TTP223
#
# Tocar una vez        -> pantalla siguiente: ojitos > hora y clima > QR > días juntos > próximas fechas > frase del día
# Mantener (caricia)   -> vuelve a los ojitos y se pone feliz (^ ^) con corazoncitos
# Mantener mucho       -> se derrite de amor (ojos de corazón)
# Dos toques rápidos   -> (en los ojitos) se sorprende
# Muchas caricias      -> se pone colorado
# Sin tocarlo 30 s     -> vuelve solo a los ojitos
# Sin tocarlo 20 min   -> se aburre y bosteza hasta que lo acaricien
# De noche (0 a 7 hs)  -> duerme con el brillo bajo; si lo tocás se despierta un ratito con sueño
# Si falta poco para una fecha importante, cada tanto lo avisa en la pantalla de los ojitos.
#
# Cableado (ver esquema.jpg):
#   OLED  VCC -> 3V3   GND -> GND   SDA -> GPIO6   SCL -> GPIO7
#   TTP223 VCC -> 3V3  GND -> GND   I/O -> GPIO3
#
# La configuración (Wi-Fi, clave del álbum, fechas, horarios) está en settings.py.

from machine import Pin, I2C
import time, random
import dibujo as D
from dibujo import put, center, wrap, heart, rrect, big
import red as R
from frases import FRASES

cfg = R.cfg
W, H = 128, 64
HOLD_MS, LARGA_MS, DOBLE_MS = 600, 2500, 350
VOLVER_MS = cfg('VOLVER_S', 30) * 1000
ABURRIDO_MS = cfg('ABURRIDO_MIN', 20) * 60000
AVISO_DIAS = cfg('AVISO_DIAS', 7)
TEXTO_QR = ["Escaneá", "esto", "", "  <3"]     # el QR lleva a https://gaelrobador.github.io/22-11/
DIAS = ('lun', 'mar', 'mié', 'jue', 'vie', 'sáb', 'dom')

i2c = I2C(0, sda=Pin(cfg('SDA', 6)), scl=Pin(cfg('SCL', 7)), freq=400000)
if cfg('OLED', 'sh1106') == 'ssd1306':        # pantallas de 0.96"
    import ssd1306
    oled = ssd1306.SSD1306_I2C(W, H, i2c, addr=cfg('OLED_ADDR', 0x3C))
else:                                         # pantallas de 1.3" (SH1106)
    import sh1106
    oled = sh1106.SH1106_I2C(W, H, i2c, addr=cfg('OLED_ADDR', 0x3C), rotate=cfg('OLED_ROTAR', 0))
D.init(oled)
ACTIVO = cfg('TOUCH_ACTIVO', 1)
touch = Pin(cfg('TOUCH', 3), Pin.IN, Pin.PULL_DOWN if ACTIVO else Pin.PULL_UP)

ticks, diff, add = time.ticks_ms, time.ticks_diff, time.ticks_add


# ---------- ojitos ----------
class Ojos:
    def __init__(self):
        now = ticks()
        self.lx = self.ly = 0.0
        self.tx = self.ty = 0
        self.blink = None
        self.double = False
        self.next_blink = add(now, 1500)
        self.next_look = add(now, 1000)
        self.next_mood = add(now, 9000)
        self.mood, self.until = 'normal', None
        self.hearts, self.next_heart = [], now
        self.caricias = []
        self.yawn, self.next_yawn = None, add(now, 3000)

    def set_mood(self, m, ms=None):
        self.mood = m
        self.until = add(ticks(), ms) if ms else None

    def caricia(self, now):
        self.caricias = [t for t in self.caricias if diff(now, t) < 60000] + [now]
        self.set_mood('caricia')

    def fin_caricia(self, now):
        if self.mood == 'love':
            self.set_mood('love', 2500)
        elif len(self.caricias) >= 4:
            self.caricias = []
            self.set_mood('rubor', 4000)
        else:
            self.set_mood('happy', 1800)

    def draw(self, now):
        if self.until is not None and diff(now, self.until) >= 0:
            self.mood, self.until = 'normal', None
        if self.mood == 'normal' and diff(now, self.next_mood) >= 0:
            self.set_mood(random.choice(('happy', 'happy', 'sleepy', 'love')), 2200)
            self.next_mood = add(now, random.randint(8000, 16000))
        m = self.mood

        # hacia dónde mira
        if m == 'aburrido':
            self.tx, self.ty = 0, 7
        elif m in ('dormido', 'caricia', 'rubor'):
            self.tx = self.ty = 0
        elif diff(now, self.next_look) >= 0:
            if random.random() < 0.35:
                self.tx = self.ty = 0
            else:
                self.tx, self.ty = random.randint(-12, 12), random.randint(-7, 7)
            self.next_look = add(now, random.randint(700, 2800))
        self.lx += (self.tx - self.lx) * 0.35
        self.ly += (self.ty - self.ly) * 0.35

        # parpadeo
        k = 1.0
        if m in ('normal', 'happy', 'sleepy', 'sorpresa', 'aburrido'):
            if self.blink is None and diff(now, self.next_blink) >= 0:
                self.blink = now
            if self.blink is not None:
                d = diff(now, self.blink)
                if d >= 160:
                    self.blink = None
                    if not self.double and random.random() < 0.25:
                        self.double, self.next_blink = True, add(now, 120)
                    else:
                        self.double = False
                        self.next_blink = add(now, random.randint(1800, 5000))
                else:
                    k = max(abs(d - 80) / 80, 0.06)

        # bostezo cuando está aburrido
        if m == 'aburrido':
            if self.yawn is None and diff(now, self.next_yawn) >= 0:
                self.yawn = now
            if self.yawn is not None:
                if diff(now, self.yawn) > 1400:
                    self.yawn, self.next_yawn = None, add(now, random.randint(6000, 12000))
                else:
                    k = 0.12

        # corazoncitos que suben mientras lo acarician
        if m in ('caricia', 'love') and diff(now, self.next_heart) >= 0:
            self.hearts.append([random.randint(6, 122), 68.0, random.choice((3, 5))])
            self.next_heart = add(now, 160 if m == 'love' else 320)

        oled.fill(0)
        ox, oy = int(self.lx), int(self.ly)
        for cx in (36, 92):
            x = cx + ox
            if m == 'love':
                heart(x, 32 + oy, 16 if (now // 300) % 2 else 13)
            elif m in ('caricia', 'rubor'):            # ojitos cerrados de felicidad: ^ ^
                b = (now // 250) % 2
                rrect(x - 18, 20 - b, 36, 24, 12)
                rrect(x - 13, 27 - b, 26, 24, 9, 0)
                if m == 'rubor':
                    for i in range(3):
                        oled.line(x - 11 + i * 7, 55, x - 7 + i * 7, 49, 1)
            elif m == 'dormido':
                rrect(x - 16, 34, 32, 10, 5)
                rrect(x - 16, 30, 32, 10, 5, 0)
            elif m == 'sorpresa':
                rrect(x - 22, 8 + oy, 44, 48, 22)
            else:
                w, h = 36, max(2, int(40 * k))
                ex, ey = x - w // 2, 32 - h // 2 + oy
                rrect(ex, ey, w, h, 10)
                if m == 'happy' and h > 10:
                    rrect(ex - 3, ey + h * 55 // 100, w + 6, h, 14, 0)
                elif m == 'sleepy':
                    oled.fill_rect(ex - 1, ey - 1, w + 2, h // 2 + 1, 0)
                elif m == 'aburrido':
                    oled.fill_rect(ex - 1, ey - 1, w + 2, h * 45 // 100 + 1, 0)
        if m == 'dormido':
            for i in range(3):
                f = (now // 90 + i * 25) % 75
                put('z' if i % 2 else 'Z', 100 + f // 6, 28 - f // 3)
        for p in self.hearts:
            p[1] -= 0.9
            heart(p[0], int(p[1]), p[2])
        self.hearts = [p for p in self.hearts if p[1] > -8]
        oled.show()


ojos = Ojos()


# ---------- pantallas ----------
dirty = True
t_draw = 0


def redibujar(now, ms):
    global dirty, t_draw
    if dirty or diff(now, t_draw) >= ms:
        dirty, t_draw = False, now
        return True
    return False


def sin_hora(titulo):
    if not R.configurado():
        center([titulo, '', 'Configurá el', 'Wi-Fi en', 'settings.py'], 0, H)
    else:
        center([titulo, '', 'Necesito la hora', '(conectando...)'], 0, H)


aviso_t, aviso_hasta = add(ticks(), -35000), ticks()


def aviso(now):
    # cada 45 s, si falta poco para una fecha importante, la muestra unos segundos
    global aviso_t, aviso_hasta
    if ojos.mood in ('dormido', 'caricia', 'love', 'rubor'):
        return False
    if diff(now, aviso_hasta) < 0:
        return True
    if diff(now, aviso_t) < 45000:
        return False
    aviso_t = now
    ev = R.proximas(1)
    if not ev or ev[0][0] > AVISO_DIAS:
        return False
    k, nombre = ev[0]
    oled.fill(0)
    heart(64, 6, 5)
    t = '¡HOY!' if k == 0 else '¡Mañana!' if k == 1 else 'Faltan %d días' % k
    center([t, ''] + wrap(nombre)[:3], 13, 51)
    oled.show()
    aviso_hasta = add(now, 4000)
    return True


def pant_ojos(now):
    if not aviso(now):
        ojos.draw(now)


def pant_hora(now):
    if not redibujar(now, 500):
        return
    oled.fill(0)
    D.wifi(0, 0, R.nivel())
    if R.hora_ok():
        y, mo, d, hh, mi, ss, wd = R.ahora()[:7]
        s = '%s %d/%d' % (DIAS[wd], d, mo)
        put(s, W - D.ancho(s), 2)
        big('%02d%s%02d' % (hh, ':' if ss % 2 else ' ', mi), 4, 17, 3)
    elif not R.configurado():
        center(['Configurá el', 'Wi-Fi en', 'settings.py'], 12, 36)
    else:
        center(['Sin Wi-Fi' if R.nivel() < 0 else 'Buscando hora'], 14, 28)
    c = R.clima
    if c['temp'] is not None:
        D.clima(2, 46, c['code'], c['dia'])
        t = '%d' % round(c['temp'])
        x = 24 + D.ancho(t)
        put(t, 24, 51)
        D.grado(x + 1, 51)
        put('C ' + cfg('CIUDAD', 'Ensenada'), x + 5, 51)
    oled.show()


def pant_qr(now):
    if not redibujar(now, 600000):
        return
    oled.fill(0)
    try:
        from qr_data import SIZE, ROWS
    except ImportError:
        center(["Falta", "qr_data.py"], 0, H)
        oled.show()
        return
    sc = max(1, H // (SIZE + 2))
    side = (SIZE + 2) * sc
    oy = (H - side) // 2
    oled.fill_rect(0, oy, side, side, 1)          # fondo blanco = zona de silencio
    for y, row in enumerate(ROWS):
        for x in range(SIZE):
            if (row >> (SIZE - 1 - x)) & 1:
                oled.fill_rect(sc + x * sc, oy + sc + y * sc, sc, sc, 0)
    tx = side + 4
    y = (H - len(TEXTO_QR) * 10) // 2
    for l in TEXTO_QR:
        put(l, tx + (W - tx - D.ancho(l)) // 2, y)
        y += 10
    oled.show()


def pant_juntos(now):
    if not redibujar(now, 60000):
        return
    oled.fill(0)
    if not R.hora_ok():
        sin_hora('Juntos hace...')
    else:
        y, m, d = R.ahora()[:3]
        sy, sm, sd = R.INICIO
        hoy = R.dnum(y, m, d)
        dias = hoy - R.dnum(sy, sm, sd)
        anios = y - sy - (1 if (m, d) < (sm, sd) else 0)
        resto = hoy - R.dnum(sy + anios, sm, sd)
        put('Juntos hace', (W - 88) // 2, 0)
        s = str(dias)
        big(s, (W - len(s) * 24) // 2, 11, 3)
        put('días ♥', (W - 48) // 2, 38)
        a = 'año' if anios == 1 else 'años'
        t = ('¡Hoy son %d %s!' % (anios, a)) if resto == 0 and anios else '%d %s y %dd' % (anios, a, resto)
        put(t, (W - D.ancho(t)) // 2, 54)
    oled.show()


def pant_prox(now):
    if not redibujar(now, 60000):
        return
    oled.fill(0)
    ev = R.proximas(3)
    if not R.hora_ok():
        sin_hora('Próximas fechas')
    elif not ev:
        center(['Próximas fechas', '', 'No hay ninguna'], 0, H)
    else:
        k, nombre = ev[0]
        nombre = D.recortar(nombre)
        put(nombre, (W - D.ancho(nombre)) // 2, 0)
        if k == 0:
            big('HOY', (W - 72) // 2, 12, 3)
        else:
            s, u = str(k), 'día' if k == 1 else 'días'
            x = (W - (len(s) * 24 + 4 + D.ancho(u))) // 2
            big(s, x, 12, 3)
            put(u, x + len(s) * 24 + 4, 28)
        y = 42
        for k2, n2 in ev[1:]:
            put(D.recortar(('hoy ' if k2 == 0 else '%dd ' % k2) + n2), 0, y)
            y += 11
    oled.show()


def pant_frase(now):
    if not redibujar(now, 60000):
        return
    i = R.hoy() % len(FRASES) if R.hora_ok() else 0
    oled.fill(0)
    heart(64, 6, 5)
    center(wrap(FRASES[i])[:5], 13, 51)
    oled.show()


PANTALLAS = (pant_ojos, pant_hora, pant_qr, pant_juntos, pant_prox, pant_frase)


# ---------- sensor táctil ----------
class Touch:
    # Eventos: 'tap', 'double', 'hold' (empezó la caricia), 'hold_long', 'release' (terminó la caricia)
    def __init__(self, pin, activo):
        self.pin, self.on = pin, activo
        self.t0, self.hold, self.larga = None, False, False
        self.tap_t, self.doble, self.down = None, True, False

    def poll(self, now):
        self.down = self.pin.value() == self.on
        if self.down:
            if self.t0 is None:
                self.t0, self.hold, self.larga = now, False, False
            d = diff(now, self.t0)
            if not self.hold and d >= HOLD_MS:
                self.hold, self.tap_t = True, None
                return 'hold'
            if self.hold and not self.larga and d >= LARGA_MS:
                self.larga = True
                return 'hold_long'
            return None
        if self.t0 is not None:
            d, hold, self.t0 = diff(now, self.t0), self.hold, None
            if hold:
                return 'release'
            if d < 25:
                return None
            if not self.doble:
                return 'tap'
            if self.tap_t is not None and diff(now, self.tap_t) <= DOBLE_MS:
                self.tap_t = None
                return 'double'
            self.tap_t = now
            return None
        if self.tap_t is not None and diff(now, self.tap_t) > DOBLE_MS:
            self.tap_t = None
            return 'tap'
        return None


# ---------- loop ----------
modo = 0
brillo = None


def set_brillo(v):
    global brillo
    if v != brillo:
        brillo = v
        oled.contrast(v)


def main():
    global modo, dirty
    oled.fill(0)
    center(['Hola ♥'], 0, H)
    oled.show()
    R.iniciar()
    t = Touch(touch, ACTIVO)
    last_touch = despierto = ticks()
    while True:
        now = ticks()
        t.doble = modo == 0           # el doble toque solo se usa en los ojitos (en las otras pantallas responde al toque)
        ev = t.poll(now)
        dormido = R.es_noche() and diff(now, despierto) >= 0
        if ev or t.down:
            last_touch = now
        if ev and dormido:            # lo despertaron: se queda un rato con sueño
            despierto = add(now, 20000)
            ojos.set_mood('sleepy', 20000)
            modo, dirty, ev = 0, True, None
        elif ev and ojos.mood == 'aburrido':
            ojos.set_mood('happy', 2000)

        if ev == 'tap':
            modo, dirty = (modo + 1) % len(PANTALLAS), True
            if modo == 0:
                ojos.set_mood('happy', 1200)
        elif ev == 'double':
            ojos.set_mood('sorpresa', 1500)
        elif ev == 'hold':
            modo, dirty = 0, True
            ojos.caricia(now)
        elif ev == 'hold_long':
            ojos.set_mood('love')
        elif ev == 'release':
            ojos.fin_caricia(now)

        if R.es_noche() and diff(now, despierto) >= 0:
            modo = 0
            if ojos.mood != 'dormido':
                ojos.set_mood('dormido')
            set_brillo(cfg('NOCHE_BRILLO', 1))
        else:
            if ojos.mood == 'dormido':
                ojos.set_mood('happy', 1500)          # buen día
            set_brillo(255)
            if modo and diff(now, last_touch) > VOLVER_MS:
                modo, dirty = 0, True
            if modo == 0 and ojos.mood == 'normal' and diff(now, last_touch) > ABURRIDO_MS:
                ojos.set_mood('aburrido')

        PANTALLAS[modo](now)
        if not t.down:
            R.tarea(now)
        time.sleep_ms(25)


if __name__ == '__main__':
    main()
