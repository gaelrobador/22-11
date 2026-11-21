# Se corre en la PC, no en el ESP:
#   pip install qrcode
#   python gen_qr.py "https://tu-link-o-un-mensaje"
# Genera qr_data.py para copiar a la placa.
import sys
import qrcode

if len(sys.argv) < 2:
    sys.exit('uso: python gen_qr.py "texto o link"')

q = qrcode.QRCode(border=0, error_correction=qrcode.constants.ERROR_CORRECT_L)
q.add_data(sys.argv[1])
q.make(fit=True)
m = q.get_matrix()
n = len(m)
if n > 29:
    print(f"Ojo: el QR quedó de {n}x{n}, en 64px va a salir muy chico. Usá un link más corto (acortador).")

rows = [int("".join("1" if c else "0" for c in r), 2) for r in m]
with open("qr_data.py", "w") as f:
    f.write(f"SIZE = {n}\nROWS = (\n")
    for r in rows:
        f.write(f"    0x{r:x},\n")
    f.write(")\n")
print(f"qr_data.py listo ({n}x{n})")
