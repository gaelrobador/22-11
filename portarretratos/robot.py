# Robotito 22·11: ESP32-C3 SuperMini + OLED 1.3" SH1106 128x64 (I2C) + sensor táctil TTP223
#
# Tocar una vez        -> pantalla siguiente: ojitos > hora y clima > QR > días juntos > próximas fechas > frase del día
# Mantener (caricia)   -> vuelve a los ojitos y se pone feliz (^ ^) con corazoncitos
# Mantener mucho       -> se derrite de amor (ojos de corazón)
# Mantener 6 s o más   -> se queda dormidito de placer y ronronea (zzz ♥)
# En los ojitos: 2 toques -> sorpresa · 3 toques -> guiño y "te quiero" · 8 toques rápidos -> se marea ("¡basta!")
# Muchas caricias      -> se pone colorado
# Sin tocarlo 30 s     -> vuelve solo a los ojitos
# Sin tocarlo un rato  -> juega solo: pelotita, mariposa, se esconde, te busca, guiña, canta, estornuda
# Sin tocarlo 20 min   -> se aburre y bosteza hasta que lo acaricien
# De noche (0 a 7 hs)  -> duerme con el brillo bajo; si lo tocás se despierta un ratito con sueño.
#                         A la mañana se despierta despacito y dice "¡Buen día!"
# A las 22:11          -> fiesta de corazones durante ese minuto
# El 22 de cada mes    -> más ojitos de corazón · Cumpleaños: gorrito y confeti todo el día
# Si falta poco para una fecha importante, cada tanto lo avisa en la pantalla de los ojitos.
#
# Cableado (ver esquema.jpg):
#   OLED  VCC -> 3V3   GND -> GND   SDA -> GPIO6   SCL -> GPIO7
#   TTP223 VCC -> 3V3  GND -> GND   I/O -> GPIO3
#
# La configuración (Wi-Fi, clave del álbum, fechas, horarios) está en settings.py.
# Este archivo se precompila a robot.mpy con ./cargar.sh (ver README): compilarlo en la placa
# le roba a la conexión segura la memoria que necesita para bajar las fechas.

from machine import Pin, I2C
import time, random, math
import dibujo as D
from dibujo import put, center, wrap, heart, rrect, big
import red as R
from frases import FRASES

cfg = R.cfg
W, H = 128, 64
HOLD_MS, LARGA_MS, ZZZ_MS, DOBLE_MS = 600, 2500, 6000, 350
MAREO_TOQUES = 8
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
# Escenas que hace solo cuando nadie lo toca (sale una al azar cada 1 a 3 minutos)
ESCENAS = ('pelota', 'pelota', 'mariposa', 'esconderse', 'buscar', 'guino', 'cantar', 'estornudo')
DUR = {'pelota': 12000, 'mariposa': 6500, 'esconderse': 6000, 'buscar': 6000, 'guino': 1800,
       'cantar': 6000, 'estornudo': 2600, 'despertar': 4000, 'mareo': 3000}


def _lim(v, a):
    return -a if v < -a else a if v > a else v


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
        self.parts, self.next_part = [], now      # corazones, notas y confeti: [tipo, x, y, vx, vy]
        self.caricias = []
        self.yawn, self.next_yawn = None, add(now, 3000)
        self.escena = None                        # [nombre, inicio, estado]
        self.fiesta = self.cumple = self.dia22 = False

    def set_mood(self, m, ms=None):
        self.mood = m
        self.until = add(ticks(), ms) if ms else None

    def jugar(self, nombre, now, txt=None):
        s = {'txt': txt}
        if nombre == 'pelota':
            s.update(x=-6.0, y=20.0, vx=2.3, vy=0.0, golpe=-99999)
        elif nombre == 'mariposa':
            s.update(corazon=random.random() < 0.35, dir=random.choice((1, -1)))
        self.escena = [nombre, now, s]

    def caricia(self, now):
        self.caricias = [t for t in self.caricias if diff(now, t) < 60000] + [now]
        self.set_mood('caricia')

    def fin_caricia(self, now):
        if self.mood in ('love', 'ronrone'):
            self.set_mood(self.mood, 2500)
        elif len(self.caricias) >= 4:
            self.caricias = []
            self.set_mood('rubor', 4000)
        else:
            self.set_mood('happy', 1800)

    def _part(self, *p):
        if len(self.parts) < 30:
            self.parts.append(list(p))

    # Devuelve (cara, corrimiento x, mirar x, mirar y, texto, apertura) o None cuando la escena terminó
    def _escena(self, now):
        nombre, t0, s = self.escena
        t = diff(now, t0)
        if t > DUR[nombre]:
            return None
        if nombre == 'pelota':
            s['vy'] += 0.35
            py = s['y']
            s['x'] += s['vx']
            s['y'] += s['vy']
            if s['y'] > 59:                               # rebota en el piso
                s['y'], s['vy'] = 59, -6.2
            if t < 8000 and ((s['x'] < 3 and s['vx'] < 0) or (s['x'] > 124 and s['vx'] > 0)):
                s['vx'] = -s['vx']                        # rebota en las paredes
            if t > 8000 and not -10 < s['x'] < 138:
                return None
            for cx in (36, 92):                           # a veces le cae en un ojo
                if py < 12 <= s['y'] and abs(s['x'] - cx - self.lx) < 16 and diff(now, s['golpe']) > 1500 and random.random() < 0.6:
                    s['vy'], s['golpe'] = -5.0, now
            g = diff(now, s['golpe'])
            cara = 'sorpresa' if g < 350 else 'happy' if g < 1500 else 'normal'
            return cara, 0, _lim((s['x'] - 64) / 5, 13), _lim((s['y'] - 32) / 4, 7), 'jiji' if 350 <= g < 1500 else None, None
        if nombre == 'mariposa':
            p = t / 6000
            x = -8 + p * 144 if s['dir'] > 0 else 136 - p * 144
            y = 30 + 15 * math.sin(t / 350)
            s['x'], s['y'] = x, y
            return ('happy' if s['corazon'] else 'normal'), 0, _lim((x - 64) / 5, 13), _lim((y - 32) / 4, 7), None, None
        if nombre == 'esconderse':
            if t < 800:
                sx = 116 * t // 800
            elif t < 2300:
                sx = 116                                     # escondido del todo
            elif t < 3300:
                sx = 116 - 22 * (t - 2300) // 1000           # asoma por el costado
            elif t < 4000:
                sx = 94
            elif t < 4800:
                sx = 94 - 94 * (t - 4000) // 800
            else:
                return 'happy', 0, 0, 0, None, None
            return 'normal', sx, -12 if t >= 2300 else 0, 0, None, None
        if nombre == 'buscar':
            fases = ((1200, -14, 0), (2400, 14, 0), (3200, -14, -5))
            for hasta, mx, my in fases:
                if t < hasta:
                    return 'normal', 0, mx, my, None, None
            if t < 3900:
                return 'sorpresa', 0, 0, 0, None, None
            return 'happy', 0, 0, 0, '¡ahí estás!', None
        if nombre == 'guino':
            return 'guino', 0, 0, 0, s['txt'], None
        if nombre == 'mareo':
            return 'mareo', (2 if (now // 80) % 2 else -2), 0, 0, '¡basta!', None
        if nombre == 'cantar':
            if diff(now, self.next_part) >= 0:
                self._part('nota', random.randint(8, 116), 58.0, random.random() - 0.5, -0.7)
                self.next_part = add(now, 450)
            return 'happy', 0, int(6 * math.sin(t / 300)), int(3 * math.sin(t / 150)), None, None
        if nombre == 'estornudo':
            if t < 900:
                return 'normal', 0, 0, -3, 'a' * (1 + t // 300) + '...', 1 - 0.75 * t / 900
            if t < 1300:
                return 'apretados', random.randint(-3, 3), 0, 0, '¡ACHÍS!', None
            return 'normal', 0, 0, 0, None, None
        if nombre == 'despertar':
            if t < 2000:
                return 'normal', 0, 0, 0, None, 0.06 + 0.94 * t / 2000
            return 'happy', 0, 0, -3, '¡Buen día!', None
        return None

    def _ojo(self, lado, x, oy, c, k, now):
        if c == 'love':
            heart(x, 32 + oy, 16 if (now // 300) % 2 else 13)
        elif c in ('caricia', 'rubor', 'cerrado'):        # ojito cerrado de felicidad: ^
            b = (now // 250) % 2 if c != 'cerrado' else 0
            rrect(x - 18, 20 - b + oy, 36, 24, 12)
            rrect(x - 13, 27 - b + oy, 26, 24, 9, 0)
            if c == 'rubor':
                for i in range(3):
                    oled.line(x - 11 + i * 7, 55, x - 7 + i * 7, 49, 1)
        elif c in ('dormido', 'ronrone'):
            rrect(x - 16, 34, 32, 10, 5)
            rrect(x - 16, 30, 32, 10, 5, 0)
        elif c == 'sorpresa':
            rrect(x - 22, 8 + oy, 44, 48, 22)
        elif c == 'mareo':                                # espiral que gira
            ph, px = now / 150, None
            for i in range(44):
                a = i * 0.25
                r = 1.5 + a * 1.45
                qx, qy = int(x + r * math.cos(a + ph)), int(32 + r * math.sin(a + ph))
                if px is not None:
                    oled.line(px, py, qx, qy, 1)
                px, py = qx, qy
        elif c == 'apretados':                            # > <  (estornudo)
            d = 1 if lado == 0 else -1
            for e in range(3):
                oled.line(x - 12 * d, 21 + e, x + 10 * d, 32, 1)
                oled.line(x + 10 * d, 32, x - 12 * d, 43 - e, 1)
        else:
            w, h = 36, max(2, int(40 * k))
            ex, ey = x - w // 2, 32 - h // 2 + oy
            rrect(ex, ey, w, h, 10)
            if c == 'happy' and h > 10:
                rrect(ex - 3, ey + h * 55 // 100, w + 6, h, 14, 0)
            elif c == 'sleepy':
                oled.fill_rect(ex - 1, ey - 1, w + 2, h // 2 + 1, 0)
            elif c == 'aburrido':
                oled.fill_rect(ex - 1, ey - 1, w + 2, h * 45 // 100 + 1, 0)

    def draw(self, now):
        if self.until is not None and diff(now, self.until) >= 0:
            self.mood, self.until = 'normal', None
        if self.mood == 'normal' and self.escena is None and not self.fiesta and diff(now, self.next_mood) >= 0:
            op = ('happy', 'sleepy', 'love', 'love', 'love') if self.dia22 or self.cumple else ('happy', 'happy', 'sleepy', 'love')
            self.set_mood(random.choice(op), 2200)
            self.next_mood = add(now, random.randint(8000, 16000))

        cara, sx, mx, my, txt, k = self.mood, 0, None, None, None, None
        if self.fiesta and cara in ('normal', 'aburrido'):        # 22:11
            cara, txt = 'love', ('22:11 ♥' if (now // 700) % 2 else None)
        if self.escena:
            r = self._escena(now)
            if r is None:
                self.escena = None
            else:
                cara, sx, mx, my, t2, k = r
                txt = t2 or txt
        if self.cumple and txt is None and cara not in ('dormido',) and (now // 1000) % 12 < 3:
            txt = '¡Feliz cumple!'

        # hacia dónde mira
        if mx is not None:
            self.tx, self.ty = mx, my
        elif cara == 'aburrido':
            self.tx, self.ty = 0, 7
        elif cara in ('dormido', 'ronrone', 'caricia', 'rubor', 'mareo'):
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
        if k is None:
            k = 1.0
            if cara in ('normal', 'happy', 'sleepy', 'sorpresa', 'aburrido'):
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
            if cara == 'aburrido':                       # bostezo
                if self.yawn is None and diff(now, self.next_yawn) >= 0:
                    self.yawn = now
                if self.yawn is not None:
                    if diff(now, self.yawn) > 1400:
                        self.yawn, self.next_yawn = None, add(now, random.randint(6000, 12000))
                    else:
                        k = 0.12

        # partículas nuevas
        if (cara in ('caricia', 'love', 'ronrone') or self.fiesta) and diff(now, self.next_part) >= 0:
            self._part('h', random.randint(6, 122), 68.0, 0, -0.9, random.choice((3, 5)))
            self.next_part = add(now, 160 if cara == 'love' or self.fiesta else 320)
        elif self.cumple and cara not in ('dormido',) and diff(now, self.next_part) >= 0:
            self._part('c', random.randint(0, 126), -2.0, random.random() * 0.6 - 0.3, 0.8)
            self.next_part = add(now, 250)

        # dibujo
        oled.fill(0)
        ox, oy = int(self.lx) + sx, int(self.ly)
        for lado, cx in ((0, 36), (1, 92)):
            c = 'cerrado' if cara == 'guino' and lado == 1 else 'normal' if cara == 'guino' else cara
            self._ojo(lado, cx + ox, oy, c, k, now)
        if self.cumple and cara != 'dormido':            # gorrito de cumpleaños
            gx, gy = 98 + ox, 11 + oy
            for i in range(12):
                w = 1 + i * 15 // 11
                oled.hline(gx - w // 2, gy - 11 + i, w, 0 if i % 4 == 3 else 1)
            D.circ(gx, gy - 13, 2)
        if self.escena:
            s = self.escena[2]
            if self.escena[0] == 'pelota':
                bx, by = int(s['x']), int(s['y'])
                D.circ(bx, by, 4, 0)
                D.circ(bx, by, 3, 1)
            elif self.escena[0] == 'mariposa' and 'x' in s:
                bx, by = int(s['x']), int(s['y'])
                D.circ(bx, by, 7, 0)
                if s['corazon']:
                    heart(bx, by, 5)
                else:
                    a = 3 if (now // 120) % 2 else 1
                    oled.fill_rect(bx - 1 - a * 2, by - 4, a * 2, 5, 1)
                    oled.fill_rect(bx + 2, by - 4, a * 2, 5, 1)
                    oled.fill_rect(bx - a, by + 1, a, 3, 1)
                    oled.fill_rect(bx + 2, by + 1, a, 3, 1)
                    oled.vline(bx, by - 4, 8, 1)
        for p in self.parts:
            p[1] += p[3]
            p[2] += p[4]
            x, y = int(p[1]), int(p[2])
            if p[0] == 'h':
                heart(x, y, p[5])
            elif p[0] == 'nota':
                D.circ(x, y, 2)
                oled.vline(x + 2, y - 7, 8, 1)
                oled.line(x + 2, y - 7, x + 5, y - 4, 1)
            else:
                oled.fill_rect(x, y, 2, 2, 1)
        self.parts = [p for p in self.parts if -9 < p[2] < 70 and -6 < p[1] < 134]
        if cara in ('dormido', 'ronrone'):
            for i in range(3):
                f = (now // 90 + i * 25) % 75
                put('z' if i % 2 else 'Z', 100 + f // 6, 28 - f // 3)
        if txt:
            oled.fill_rect(0, 55, W, 9, 0)
            put(txt, (W - D.ancho(txt)) // 2, 56)
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
    if ojos.mood in ('dormido', 'caricia', 'love', 'rubor', 'ronrone') or ojos.escena or ojos.fiesta:
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
    # Eventos: 'tap', 'double', 'triple', 'mareo' (muchos toques), 'hold' (empezó la caricia),
    # 'hold_long', 'hold_zzz' (caricia larguísima), 'release' (terminó la caricia)
    def __init__(self, pin, activo):
        self.pin, self.on = pin, activo
        self.t0, self.hold = None, 0
        self.n, self.tap_t, self.doble, self.down = 0, None, True, False
        self.calma = ticks()            # después de marearse ignora los toques que sobran

    def poll(self, now):
        self.down = self.pin.value() == self.on
        if self.down:
            if self.t0 is None:
                self.t0, self.hold = now, 0
            d = diff(now, self.t0)
            if self.hold == 0 and d >= HOLD_MS:
                self.hold, self.n = 1, 0
                return 'hold'
            if self.hold == 1 and d >= LARGA_MS:
                self.hold = 2
                return 'hold_long'
            if self.hold == 2 and d >= ZZZ_MS:
                self.hold = 3
                return 'hold_zzz'
            return None
        if self.t0 is not None:
            d, h, self.t0 = diff(now, self.t0), self.hold, None
            if h:
                return 'release'
            if d < 25:
                return None
            if diff(now, self.calma) < 0:
                return None
            if not self.doble:
                return 'tap'
            self.n, self.tap_t = self.n + 1, now
            if self.n >= MAREO_TOQUES:
                self.n, self.calma = 0, add(now, 1500)
                return 'mareo'
            return None
        if self.n and diff(now, self.tap_t) > DOBLE_MS:
            n, self.n = self.n, 0
            return 'tap' if n == 1 else 'double' if n == 2 else 'triple'
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
    if R.configurado():
        oled.fill(0)
        center(['Hola ♥', '', 'conectando...'], 0, H)
        oled.show()
        R.arranque()
    t = Touch(touch, ACTIVO)
    last_touch = despierto = t_seg = ticks()
    t_dia = add(t_seg, -60000)
    prox_escena = add(t_seg, 30000)
    while True:
        now = ticks()
        t.doble = modo == 0           # 2, 3 y muchos toques solo en los ojitos (en las otras pantallas responde al toque)
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
        if ev and ev != 'release':
            ojos.escena = None        # si estaba jugando solo, deja de jugar para atenderla

        if ev == 'tap':
            modo, dirty = (modo + 1) % len(PANTALLAS), True
            if modo == 0:
                ojos.set_mood('happy', 1200)
        elif ev == 'double':
            ojos.set_mood('sorpresa', 1500)
        elif ev == 'triple':
            ojos.jugar('guino', now, 'te quiero ♥')
            ojos.escena[1] = add(now, -DUR['guino'] + 2600)     # dura un poco más que el guiño solo
        elif ev == 'mareo':
            ojos.jugar('mareo', now)
        elif ev == 'hold':
            modo, dirty = 0, True
            ojos.caricia(now)
        elif ev == 'hold_long':
            ojos.set_mood('love')
        elif ev == 'hold_zzz':
            ojos.set_mood('ronrone')
        elif ev == 'release':
            ojos.fin_caricia(now)

        # una vez por segundo: 22:11, y una vez por minuto: ¿hoy es 22 o un cumple?
        if diff(now, t_seg) >= 1000:
            t_seg = now
            if R.hora_ok():
                y, mo, d, hh, mi = R.ahora()[:5]
                ojos.fiesta = (hh, mi) == (22, 11)
                if ojos.fiesta and modo and diff(now, last_touch) > 5000:
                    modo, dirty = 0, True
                if diff(now, t_dia) >= 60000:
                    t_dia = now
                    hoy = [n for k, n in R.proximas(8) if k == 0]
                    ojos.cumple = any('cumple' in n.lower() for n in hoy)
                    ojos.dia22 = d == R.INICIO[2]

        if R.es_noche() and diff(now, despierto) >= 0:
            modo = 0
            ojos.escena = None
            if ojos.mood != 'dormido':
                ojos.set_mood('dormido')
            set_brillo(cfg('NOCHE_BRILLO', 1))
        else:
            if ojos.mood == 'dormido':                # buen día
                ojos.set_mood('normal')
                ojos.jugar('despertar', now)
            set_brillo(255)
            if modo and diff(now, last_touch) > VOLVER_MS:
                modo, dirty = 0, True
            if modo == 0 and ojos.mood == 'normal' and ojos.escena is None and diff(now, last_touch) > ABURRIDO_MS:
                ojos.set_mood('aburrido')
            if (modo == 0 and ojos.escena is None and not ojos.fiesta and ojos.mood in ('normal', 'aburrido')
                    and diff(now, last_touch) > 15000 and diff(now, prox_escena) >= 0):
                ojos.jugar(random.choice(ESCENAS), now)
                prox_escena = add(now, random.randint(60000, 180000))

        PANTALLAS[modo](now)
        if not t.down:
            R.tarea(now)
        time.sleep_ms(25)

