# 22·11 — Álbum de fotos (regalo)

Página web de regalo para mi pareja: un lobby con título "22·11", un mensaje y la playlist de Spotify embebida, y debajo un álbum de fotos privado donde ella sube fotos, crea álbumes y las ordena.

Se complementa con un robotito físico (ESP32-C3 SuperMini + OLED) que muestra un QR que lleva a esta página. Ese firmware está en otro repo/carpeta (`portarretratos/`, MicroPython).

## Stack

- Un solo archivo: `index.html` (HTML + CSS + JS inline, sin build, sin bundler, sin framework).
- Hosting: GitHub Pages, repo `gaelrobador/22-11`, rama `main`, raíz → `https://gaelrobador.github.io/22-11/`.
- Backend: Supabase (proyecto "22-11", región Américas).
  - URL: `https://gewoffntwuofryqruskd.supabase.co`
  - Key: publishable (`sb_publishable_...`) está en `CFG` dentro de `index.html`. Es pública, está bien que esté en el repo.
  - **Nunca** poner la `sb_secret_...` en el front.
- Librería: `@supabase/supabase-js@2` vía jsDelivr UMD (`supabase.createClient`).
- Fuentes: Google Fonts (Playfair Display italic 600, Nunito 400/700, Caveat 500).

## Configuración (`CFG` en `index.html`)

```js
SUPABASE_URL, SUPABASE_KEY, EMAIL, SPOTIFY
```

- `EMAIL` = `nosotros@2211.com`: usuario compartido de Supabase Auth. Ella nunca lo ve; solo escribe la clave. La sesión queda guardada en localStorage.
- `SPOTIFY`: link de playlist; se convierte a `open.spotify.com/embed/playlist/<id>`. No hay autoplay (los navegadores no lo permiten).

## Modelo de datos (ver `setup.sql`)

- `albums(id uuid pk, name text, created_at)`
- `photos(id uuid pk, path text, album_id uuid → albums.id ON DELETE SET NULL, caption text, created_at)`
  - `album_id IS NULL` = la foto está en la bandeja de entrada.
  - Borrar un álbum NO borra fotos: vuelven a la bandeja.
- Storage: bucket privado `fotos`. Las imágenes se muestran con `createSignedUrls` (7 días), se regeneran al recargar.
- RLS activado en todo; policies `for all to authenticated using (true)`. El rol `anon` no ve nada.
- Sign-ups públicos desactivados en Supabase Auth (solo existe el usuario compartido).

## Funcionalidades actuales

- Lobby: corazoncitos flotando (desactivados con `prefers-reduced-motion`), título, mensaje, Spotify, botón "Entrar ♥".
- Login con solo contraseña.
- Pestañas Bandeja (n) / Álbumes.
- Subida múltiple: se achica en el cliente a 1600px de lado mayor, JPEG 0.85. Si estás dentro de un álbum, sube ahí; si no, a la bandeja.
- Selección múltiple (circulito en cada polaroid) → barra inferior: mover a bandeja/álbum/"+ Nuevo álbum…", borrar.
- Álbum: renombrar, borrar.
- Visor (lightbox): flechas, swipe, Esc, epígrafe editable por foto (se guarda en `caption` al perder foco).
- Estética: fondo rosa claro `#fbeef0`, tinta bordó `#3b1522`, acento `#d9466f`; fotos tipo polaroid levemente rotadas (rotación derivada del id).

## Convenciones

- Todo el texto de la UI en español rioplatense (vos, "subí", "armá"), tono cariñoso y simple.
- Mantener el proyecto en un solo `index.html` salvo que haya una razón fuerte.
- Escapar todo texto de usuario con `esc()` antes de meterlo en `innerHTML`.
- Mobile first: ella lo va a usar desde el celu. Targets ≥ 44px, inputs a 16px (evita zoom en iOS).
- Cambios de esquema: agregarlos a `setup.sql` de forma idempotente (`if not exists`, `drop policy if exists` antes de `create policy`) y correrlos en Supabase → SQL Editor en una query nueva.

## Cómo probar

- Local: `python3 -m http.server` en la carpeta y abrir `http://localhost:8000` (Supabase acepta requests desde cualquier origen con la publishable key).
- Deploy: commit + push a `main`; GitHub Pages tarda 1–2 min.
- Errores: consola del navegador (F12).

## Ideas pendientes / posibles

- Personalizar más el lobby (foto de fondo, colores, texto final).
- Ordenar fotos dentro de un álbum (drag & drop) y elegir portada.
- Fecha por foto / agrupar por fecha.
- Soporte HEIC si alguna foto de iPhone no se puede leer (hoy si `resize` falla se sube el archivo original).
- Contador "días juntos" desde el 22/11.
