# Vivible — instrucciones para Claude

Web estática publicada con GitHub Pages desde la rama `master` (raíz): https://jrjr3333.github.io/Vivivible/ . Proyecto «Ganar Dinero» de Juan. Gratis por ahora (sin anuncios ni afiliados).

## Cómo se monta
- Todo se genera con `python3 fuente/build.py` desde la raíz: `index.html`, una página por ciudad (`<ciudad>/`), una por distrito (`<ciudad>/<distrito>/`), `sitemap.xml` y `robots.txt`.
- Nunca se editan a mano los ficheros generados: se cambia `fuente/template.html` o `fuente/precios.json` y se vuelve a generar.
- `fuente/precios.json`: por ciudad, venta €/m² y alquiler €/m²/mes por distrito (idealista), precio medio de habitación, ITP/AJD de la comunidad y centro del mapa. `null` = sin dato (la web lo estima).
- `fuente/data.json`: barrios de Madrid (polígonos, para saber el distrito exacto) y estaciones de metro de Madrid (respaldo si OpenStreetMap no responde). `fuente/prep.py` lo genera.
- `assets/leaflet/`: mapa (Leaflet 1.9.4, BSD-2). En el navegador se usan Nominatim (direcciones) y Overpass (transporte, comercios, colegios, parques, ruido).

## Datos que hay que mantener al día (tarea mensual)
- Venta y alquiler por distrito: páginas de idealista «valoracion-de-inmuebles/<ciudad>» (venta y alquiler en una tabla) o «sala-de-prensa/informes-precio-vivienda». Actualizar `venta`, `alquiler`, `mes` y `d` de cada ciudad y `actualizado`.
- Habitación (`hab`): cada trimestre, informe de habitaciones de idealista.
- ITP/AJD: revisar si alguna comunidad cambia el tipo general.

## Ciclo automático de mejoras
- `.github/workflows/ciclo.yml` ejecuta Claude Code en GitHub Actions cada 6 horas (y a mano desde la pestaña Actions) siguiendo `.ciclo/INSTRUCCIONES.md`. Lo hecho queda en `.ciclo/historial.md`.
- Necesita el secreto del repositorio `CLAUDE_CODE_OAUTH_TOKEN` (o `ANTHROPIC_API_KEY`).

## Antes de publicar
- `python3 fuente/build.py` sin errores y `node --check` del script de `index.html`.
- Probar en un navegador (simulando Nominatim y Overpass): los tres modos, pegar anuncio, búsqueda por dirección en al menos dos ciudades, informe, enlace para compartir y una página de distrito.
- Textos en español de España, tuteando, claros y sin tecnicismos.
- Comprobar que «pages build and deployment» del último commit acaba en verde.
