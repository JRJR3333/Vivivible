# Vivible — instrucciones para Claude

Web estática publicada con GitHub Pages desde la rama `master` (raíz): https://jrjr3333.github.io/Vivivible/ . Proyecto «Ganar Dinero» de Juan. Gratis por ahora (sin anuncios ni afiliados).

## Cómo se monta
- Todo se genera con `python3 fuente/build.py` desde la raíz: `index.html`, `chat/index.html`, una página por ciudad (`<ciudad>/`), una por distrito (`<ciudad>/<distrito>/`), `sitemap.xml` y `robots.txt`.
- Nunca se editan a mano los ficheros generados (`index.html`, `chat/`, carpetas de ciudad, `assets/vivible.js`, `assets/vivible.css`, `datos.json`, `sitemap.xml`, `robots.txt`): se cambia algo de `fuente/` y se vuelve a generar.
- `fuente/precios.json`: por ciudad, venta €/m² y alquiler €/m²/mes por distrito (idealista), precio medio de habitación, ITP/AJD de la comunidad y centro del mapa. `null` = sin dato (la web lo estima).
- `fuente/data.json`: barrios de Madrid (polígonos, para saber el distrito exacto) y estaciones de metro de Madrid (respaldo si OpenStreetMap no responde). `fuente/prep.py` lo genera.
- `assets/leaflet/`: mapa (Leaflet 1.9.4, BSD-2). En el navegador se usan Nominatim (direcciones) y Overpass (transporte, comercios, colegios, parques, ruido).

## Un motor, varios formatos (lo pidió Juan, 2026-11-11)
- Juan quiere varios formatos (web, conversación, app, WhatsApp…) con la parte gráfica separada y **la misma información y base de datos**. Está explicado en `fuente/LEEME.md`.
- `fuente/nucleo/` es el motor común (datos, leer anuncios, localizar, entorno, valoración, `informe()`, `informeHTML()`, `informeTexto()`); no usa `document` ni `window` y funciona también en Node.
- `fuente/formatos/<nombre>.html` es solo pantalla e interacción. Un cálculo, un texto del informe o un dato **nunca** se cambia dentro de un formato: va al núcleo o a `precios.json`, una sola vez.
- Formato nuevo: fichero en `fuente/formatos/` y una línea en `FORMATOS` de `build.py`.

## Datos que hay que mantener al día (tarea mensual)
- Venta y alquiler por distrito: páginas de idealista «valoracion-de-inmuebles/<ciudad>» (venta y alquiler en una tabla) o «sala-de-prensa/informes-precio-vivienda». Actualizar `venta`, `alquiler`, `mes` y `d` de cada ciudad y `actualizado`.
- Habitación (`hab`): cada trimestre, informe de habitaciones de idealista.
- ITP/AJD: revisar si alguna comunidad cambia el tipo general.

## Ciclo automático de mejoras
- La tarea programada de Claude «Vivible: ciclo auditor-desarrollador» se lanza cada 6 horas y sigue `.ciclo/INSTRUCCIONES.md`. Lo hecho queda en `.ciclo/historial.md`.
- Alternativa manual: `.github/workflows/ciclo.yml` (solo a mano; necesita el secreto `CLAUDE_CODE_OAUTH_TOKEN` o `ANTHROPIC_API_KEY`).

## Principio de diseño (lo pidió Juan, 2026-11-11)
- Que el usuario rellene lo menos posible y que todo sea intuitivo y automático. Solo es obligatorio decir dónde está el piso; lo demás se deduce del anuncio pegado, se supone con valores razonables (avisándolo en el informe) o va plegado en «Más detalles (opcional)».
- Dos formatos (decisión de Juan, 2026-11-11): la portada por pasos (`fuente/formatos/web.html` → `index.html`), que Juan prefiere para web y app, y la conversación (`fuente/formatos/chat.html` → `chat/index.html`), que se guarda como enlace para enviar por WhatsApp. No se cambia uno por otro.
- Pegar el anuncio genera el informe solo, y tras el primer informe cualquier cambio lo actualiza al momento. No añadir campos obligatorios ni pasos extra.

## Antes de publicar
- `python3 fuente/build.py` sin errores, `node fuente/pruebas/nucleo.js` (el motor, sin navegador), y `node --check` de `assets/vivible.js` y del script de cada formato (`index.html`, `chat/index.html`).
- Probar en un navegador **cada formato** (simulando Nominatim y Overpass): los tres modos, pegar anuncio, búsqueda por dirección en al menos dos ciudades, informe, enlace para compartir y una página de distrito.
- Textos en español de España, tuteando, claros y sin tecnicismos.
- Comprobar que «pages build and deployment» del último commit acaba en verde.
