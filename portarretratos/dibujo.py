# Ayudas de dibujo para el OLED 128x64: formas, corazones, texto con acentos, números grandes e íconos.
import framebuf, math

W, H = 128, 64
oled = None


def init(o):
    global oled
    oled = o


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


def circ(cx, cy, r, c=1):
    for dy in range(-r, r + 1):
        dx = int((r * r - dy * dy) ** 0.5 + 0.5)
        oled.hline(cx - dx, cy + dy, 2 * dx + 1, c)


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


HEARTS = {s: heart_spans(s) for s in (3, 5, 13, 15, 16, 19)}


def heart(cx, cy, s, c=1):
    for dy, x0, x1 in HEARTS[s]:
        oled.hline(cx + x0, cy + dy, x1 - x0 + 1, c)


# ---------- texto ----------
ACENTOS = {"á": "a", "é": "e", "í": "i", "ó": "o", "ú": "u",
           "Á": "A", "É": "E", "Í": "I", "Ó": "O", "Ú": "U"}
MUDOS = "¡¿"


def ancho(s):
    return sum(8 for ch in s if ch not in MUDOS)


def recortar(s, n=16):
    out, k = "", 0
    for ch in s:
        if ch not in MUDOS:
            if k == n:
                break
            k += 1
        out += ch
    return out


def grado(x, y, c=1):
    oled.rect(x, y, 3, 3, c)


def put(s, x, y, c=1):
    # texto 8x8 con acentos, ñ, ♥ y ° dibujados a mano; lo que no se puede dibujar se saltea
    for ch in s:
        if ch in ACENTOS:
            oled.text(ACENTOS[ch], x, y, c)
            oled.pixel(x + 4, y, c)
            oled.pixel(x + 5, y, c)
        elif ch in "ñÑ":
            oled.text("n" if ch == "ñ" else "N", x, y, c)
            oled.hline(x + 1, y, 2, c)
            oled.hline(x + 3, y + 1, 2, c)
        elif ch == "♥":
            heart(x + 3, y + 3, 3, c)
        elif ch == "°":
            grado(x + 1, y, c)
        elif ch in MUDOS:
            continue
        elif " " <= ch <= "~":
            oled.text(ch, x, y, c)
        else:
            continue
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
        put(l, (W - ancho(l)) // 2, y)
        y += step


_fb_buf = bytearray(8)
_fb = framebuf.FrameBuffer(_fb_buf, 8, 8, framebuf.MONO_HLSB)


def big(s, x, y, k=3, c=1):
    # texto ampliado k veces (para la hora y los números grandes)
    for ch in s:
        _fb.fill(0)
        _fb.text(ch, 0, 0, 1)
        for yy in range(8):
            for xx in range(8):
                if _fb.pixel(xx, yy):
                    oled.fill_rect(x + xx * k, y + yy * k, k, k, c)
        x += 8 * k


# ---------- íconos ----------
def _arco(cx, cy, r):
    for a in range(40, 141, 5):
        t = math.radians(a)
        oled.pixel(int(cx + r * math.cos(t) + 0.5), int(cy - r * math.sin(t) + 0.5), 1)


def wifi(x, y, nivel):
    # nivel: -1 = sin conexión, 0..3 = rayitas según la señal (ocupa 15x12)
    cx, cy = x + 7, y + 11
    oled.fill_rect(cx - 1, cy - 1, 3, 2, 1)
    for i, r in enumerate((4, 7, 10)):
        if nivel < 0 or i < nivel:
            _arco(cx, cy, r)
            _arco(cx, cy, r - 1)
    if nivel < 0:
        oled.line(x, y, x + 14, y + 11, 0)
        oled.line(x, y + 1, x + 14, y + 12, 1)


def _nube(x, y):
    circ(x + 5, y + 8, 3)
    circ(x + 9, y + 5, 4)
    circ(x + 12, y + 8, 3)
    oled.fill_rect(x + 3, y + 8, 11, 4, 1)


def _sol(cx, cy, r=3):
    circ(cx, cy, r)
    for a in range(0, 360, 45):
        t = math.radians(a)
        oled.line(int(cx + (r + 2) * math.cos(t)), int(cy + (r + 2) * math.sin(t)),
                  int(cx + (r + 4) * math.cos(t)), int(cy + (r + 4) * math.sin(t)), 1)


def _luna(cx, cy):
    circ(cx, cy, 5)
    circ(cx + 3, cy - 2, 4, 0)


def clima(x, y, code, dia=1):
    # ícono de 16x16 según el código del tiempo (WMO) que devuelve Open-Meteo
    if code == 0:
        _sol(x + 8, y + 8, 4) if dia else _luna(x + 8, y + 8)
    elif code in (1, 2):
        _sol(x + 5, y + 5, 3) if dia else _luna(x + 5, y + 5)
        _nube(x + 1, y + 4)
    elif code == 3:
        _nube(x, y + 2)
    elif code in (45, 48):
        for i in range(4):
            oled.hline(x + (i % 2) * 2, y + 3 + i * 3, 14, 1)
    elif code >= 95:
        _nube(x, y - 1)
        for dx in (0, 1):                      # rayo en zigzag
            oled.line(x + 10 + dx, y + 11, x + 7 + dx, y + 13, 1)
            oled.line(x + 7 + dx, y + 13, x + 10 + dx, y + 13, 1)
            oled.line(x + 10 + dx, y + 13, x + 7 + dx, y + 16, 1)
    elif 71 <= code <= 77 or code in (85, 86):
        _nube(x, y)
        for dx in (3, 8, 13):
            oled.pixel(x + dx, y + 14, 1)
            oled.pixel(x + dx - 1, y + 15, 1)
    else:   # llovizna y lluvia
        _nube(x, y)
        for dx in (4, 8, 12):
            oled.line(x + dx, y + 13, x + dx - 2, y + 15, 1)
