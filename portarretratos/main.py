# Regalito: ESP32-C3 SuperMini + OLED SSD1306 128x64 (I2C) + 1 pulsador
#
# Pulsación corta -> siguiente pantalla: ojitos > mensajes > corazón > QR
# Pulsación larga -> ojitos enamorados (desde cualquier pantalla)
#
# Cableado:
#   OLED VCC -> 3V3   GND -> GND   SDA -> GPIO6   SCL -> GPIO7
#   Pulsador entre GPIO3 y GND (usa el pull-up interno)
#   (Si querés probar sin cablear el botón, poné BTN = 9 y usá el BOOT de la placa)

from machine import Pin, I2C
import ssd1306, time, random

SDA, SCL, BTN = 6, 7, 3
W, H = 128, 64
LONG_MS = 700        # cuánto hay que mantener para la pulsación larga
MSG_MS = 6000        # cada cuánto rota el mensaje

# Editá estos. Acentos y ñ andan (se dibujan a mano). Máx ~5 renglones de 16 letras.
MENSAJES = [
    "Sos lo más lindo que me pasó",
    "Gracias por elegirme todos los días",
    "Te quiero más que a un firmware que compila de una",
    "Cada día con vos es mi favorito",
    "Vale por un abrazo de oso. Canjeable siempre",
    "Sos mi lugar seguro",
]
TEXTO_CORAZON = "te quiero"
TEXTO_QR = ["Escaneá", "esto", "", "  <3"]   # el QR lleva a https://gaelrobador.github.io/22-11/

i2c = I2C(0, sda=Pin(SDA), scl=Pin(SCL), freq=400000)
oled = ssd1306.SSD1306_I2C(W, H, i2c)
btn = Pin(BTN, Pin.IN, Pin.PULL_UP)

ticks, diff, add = time.ticks_ms, time.ticks_diff, time.ticks_add


# ---------- dibujo ----------
def rrect(x, y, w, h, r, c=1):
    r = min(r, w // 2, h // 2)
    if r < 1:
        oled.fill_rect(x, y, w, h, c)
        return
    oled.fill_rect(x, y + r, w, h - 2 * r, c)
    for i in range(r):
        dy = r - i - 0.5
        dx = r - int((r * r - dy * dy) ** 0.5 + 0.5)
        oled.hline(x + dx, y + i, w - 2 * dx, c)
        oled.hline(x + dx, y + h - 1 - i, w - 2 * dx, c)


def heart_spans(s):
    out = []
    for j in range(-s, s + 1):
        v = -j * 1.3 / s + 0.12
        start = None
        for i in range(-s, s + 2):
            u = i * 1.3 / s
            inside = i <= s and (u * u + v * v - 1) ** 3 - u * u * v ** 3 <= 0
            if inside and start is None:
                start = i
            elif not inside and start is not None:
                out.append((j, start, i - 1))   # puede haber 2 tramos por fila (la muesca)
                start = None
    return out


HEARTS = {s: heart_spans(s) for s in (5, 13, 15, 16, 19)}


def heart(cx, cy, s, c=1):
    for dy, x0, x1 in HEARTS[s]:
        oled.hline(cx + x0, cy + dy, x1 - x0 + 1, c)


ACENTOS = {"á": "a", "é": "e", "í": "i", "ó": "o", "ú": "u",
           "Á": "A", "É": "E", "Í": "I", "Ó": "O", "Ú": "U"}


def put(s, x, y):
    # texto 8x8 con acentos y ñ dibujados a mano
    for ch in s:
        if ch in ACENTOS:
            oled.text(ACENTOS[ch], x, y)
            oled.pixel(x + 4, y, 1)
            oled.pixel(x + 5, y, 1)
        elif ch in "ñÑ":
            oled.text("n" if ch == "ñ" else "N", x, y)
            oled.hline(x + 1, y, 2, 1)
            oled.hline(x + 3, y + 1, 2, 1)
        elif ch in "¡¿":
            pass
        else:
            oled.text(ch, x, y)
        if ch not in "¡¿":
            x += 8


def wrap(t, n=16):
    lines, cur = [], ""
    for w in t.split():
        if not cur:
            cur = w
        elif len(cur) + 1 + len(w) <= n:
            cur += " " + w
        else:
            lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


def center(lines, y0, h, step=10):
    y = y0 + (h - len(lines) * step) // 2 + 1
    for l in lines:
        put(l, (W - len(l) * 8) // 2, y)
        y += step


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
        self.mood, self.mood_until = "normal", now

    def set_mood(self, m, ms):
        self.mood = m
        self.mood_until = add(ticks(), ms)

    def draw(self, now):
        if diff(now, self.next_look) >= 0:
            if random.random() < 0.35:
                self.tx = self.ty = 0
            else:
                self.tx, self.ty = random.randint(-12, 12), random.randint(-7, 7)
            self.next_look = add(now, random.randint(700, 2800))
        self.lx += (self.tx - self.lx) * 0.35
        self.ly += (self.ty - self.ly) * 0.35

        k = 1.0
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

        if self.mood != "normal" and diff(now, self.mood_until) >= 0:
            self.mood = "normal"
        if diff(now, self.next_mood) >= 0:
            self.set_mood(random.choice(("happy", "happy", "sleepy", "love")), 2200)
            self.next_mood = add(now, random.randint(8000, 16000))

        oled.fill(0)
        ox, oy = int(self.lx), int(self.ly)
        if self.mood == "love":
            s = 16 if (now // 300) % 2 else 13
            heart(36 + ox, 32 + oy, s)
            heart(92 + ox, 32 + oy, s)
        else:
            for cx in (36, 92):
                w, h = 36, max(2, int(40 * k))
                x, y = cx - w // 2 + ox, 32 - h // 2 + oy
                rrect(x, y, w, h, 10)
                if self.mood == "happy" and h > 10:
                    rrect(x - 3, y + h * 55 // 100, w + 6, h, 14, 0)
                elif self.mood == "sleepy":
                    oled.fill_rect(x - 1, y - 1, w + 2, h // 2 + 1, 0)
        oled.show()


# ---------- pantallas ----------
ojos = Ojos()
msg_i = 0
msg_t = ticks()
dirty = True


def pant_ojos(now):
    ojos.draw(now)


def pant_mensajes(now):
    global msg_i, msg_t, dirty
    if diff(now, msg_t) >= MSG_MS:
        msg_i = (msg_i + 1) % len(MENSAJES)
        msg_t, dirty = now, True
    if not dirty:
        return
    oled.fill(0)
    heart(64, 6, 5)
    center(wrap(MENSAJES[msg_i]), 13, 51)
    oled.show()
    dirty = False


def pant_corazon(now):
    oled.fill(0)
    f = (now // 120) % 8
    s = 19 if f in (0, 2) else 15        # latido doble: pum-pum ... pausa
    heart(64, 26, s)
    put(TEXTO_CORAZON, (W - len(TEXTO_CORAZON) * 8) // 2, 55)
    oled.show()


def pant_qr(now):
    global dirty
    if not dirty:
        return
    oled.fill(0)
    try:
        from qr_data import SIZE, ROWS
    except ImportError:
        center(["Falta", "qr_data.py"], 0, H)
        oled.show()
        dirty = False
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
        put(l, tx + (W - tx - len(l) * 8) // 2, y)
        y += 10
    oled.show()
    dirty = False


PANTALLAS = (pant_ojos, pant_mensajes, pant_corazon, pant_qr)
modo = 0


# ---------- botón ----------
class Boton:
    def __init__(self, pin):
        self.pin, self.t0, self.fired = pin, None, False

    def poll(self, now):
        down = self.pin.value() == 0
        if down and self.t0 is None:
            self.t0, self.fired = now, False
        elif down and not self.fired and diff(now, self.t0) >= LONG_MS:
            self.fired = True
            return "long"
        elif not down and self.t0 is not None:
            short = not self.fired and diff(now, self.t0) >= 30
            self.t0 = None
            if short:
                return "short"
        return None


def main():
    global modo, dirty, msg_t
    b = Boton(btn)
    while True:
        now = ticks()
        ev = b.poll(now)
        if ev == "short":
            modo = (modo + 1) % len(PANTALLAS)
            dirty, msg_t = True, now
            if modo == 0:
                ojos.set_mood("happy", 1200)   # se pone contento cuando vuelve
        elif ev == "long":
            modo, dirty = 0, True
            ojos.set_mood("love", 3500)
        PANTALLAS[modo](now)
        time.sleep_ms(25)


if __name__ == "__main__":
    main()
