# Configuración del robotito.
# Copiá este archivo con el nombre settings.py, completalo y pasalo a la placa.
# settings.py NO se sube a GitHub (está en .gitignore) porque tiene contraseñas.

# ---- Wi-Fi ----
WIFI_SSID = ""            # nombre de la red
WIFI_PASS = ""            # contraseña
WIFI_TXPOWER = 8.5        # la C3 SuperMini conecta mejor con potencia baja; si no engancha probá 5 o 13

# ---- Álbum ----
# La misma clave que se usa para entrar a la página. Con esto el robot lee las
# "fechas importantes" que cargan en la página (pestaña Calendario).
# Si la dejás vacía, usa solo las fechas de FECHAS (abajo).
ALBUM_CLAVE = ""

# ---- Fechas ----
INICIO = (2023, 11, 22)   # el primer 22/11: de acá salen los días juntos y el aniversario
# Fechas extra fijas, además de las de la página: ("nombre", "AAAA-MM-DD", se_repite_todos_los_años)
FECHAS = [
    # ("Examen de algo", "2026-12-10", False),
]
AVISO_DIAS = 7            # avisa en los ojitos cuando falta esta cantidad de días o menos

# ---- Lugar y hora ----
CIUDAD = "Ensenada"
LAT, LON = -34.86, -57.91
TZ_HORAS = -3             # Argentina

# ---- Comportamiento ----
NOCHE = (0, 7)            # duerme de 0 a 7 hs
NOCHE_BRILLO = 1          # brillo de noche (0 a 255)
VOLVER_S = 30             # segundos sin tocarlo para volver a los ojitos
ABURRIDO_MIN = 20         # minutos sin tocarlo para que se aburra

# ---- Pantalla ----
OLED = "sh1106"           # "sh1106" (1.3") o "ssd1306" (0.96")
OLED_ADDR = 0x3C          # si i2c.scan() da [61], poné 0x3D
OLED_ROTAR = 0            # 180 si se ve dada vuelta

# ---- Pines ----
SDA, SCL = 6, 7           # OLED (en algunas pantallas SCL dice SCK)
TOUCH = 3                 # salida I/O del TTP223
TOUCH_ACTIVO = 1          # el TTP223 da 1 al tocarlo; si está configurado al revés, poné 0
