# Instrucciones del ciclo de mejoras (auditor → desarrollador → verificador)

Vivible es una web estática en español de España que ayuda a quien busca piso o habitación en 10 ciudades. Repositorio JRJR3333/Vivivible, rama master, publicada en https://jrjr3333.github.io/Vivivible/ . Proyecto «Ganar Dinero» de Juan: la web es gratis por ahora.

## Reglas (por encima de todo)
- Que la web siga funcionando es lo primero. Ante la duda, no cambies nada.
- No borres datos (fuente/precios.json, fuente/data.json, historial), no subas claves ni secretos, no crees cuentas en ningún servicio, no actives anuncios ni afiliados y no toques otros repositorios ni la configuración de GitHub.
- Nunca edites a mano lo generado (index.html, carpetas de ciudad, sitemap.xml, robots.txt): cambia fuente/template.html, fuente/build.py o fuente/*.json y regenera con `python3 fuente/build.py`.
- No cambies .github/workflows/ ni este fichero.
- Textos en español de España, tuteando, claros y sin tecnicismos.
- Nada de force push ni reescribir historia.

## Tiempo
El ciclo dura como máximo 45 minutos desde el inicio. Comprueba la hora con `date -u` antes de cada vuelta y no empieces una vuelta nueva si quedan menos de 10 minutos.

## Bucle (repite mientras haya tiempo)
1. **Auditor** (subagente con la herramienta Task): lee CLAUDE.md, las últimas 40 líneas de .ciclo/historial.md y el código. Propón 1–3 mejoras PEQUEÑAS y seguras, terminables en unos 10 minutos, cada una con un criterio de aceptación comprobable, sin repetir lo que ya está en el historial. Prioridad: errores visibles → uso en móvil → claridad y confianza de los resultados → SEO de las páginas de ciudad y distrito → velocidad y accesibilidad → captar usuarios (compartir, volver) → preparar la monetización sin activarla.
2. **Desarrollador** (otro subagente): aplica solo esas mejoras. Obligatorio: JSON válidos (`python3 -m json.tool`), `python3 fuente/build.py` sin errores y `node --check` del script de index.html (extráelo a un .js temporal en /tmp).
3. **Verificador** (un tercer subagente, distinto): comprueba cada mejora contra su criterio y que nada se rompe. Prueba en navegador con Playwright para Python (ya instalado con Chromium): portada, una página de ciudad y una de distrito, en ancho de móvil (400 px) y de escritorio, simulando Nominatim y Overpass con `page.route` y bloqueando tile.openstreetmap.org y fonts.googleapis.com; los tres modos (Comprar, Alquilar piso, Habitación) deben dar informe sin errores de página. Sirve la web con `python3 -m http.server` desde la raíz. Lo que no pase se revierte.
4. Si queda algo aprobado: un commit en master con un mensaje en español que diga qué mejora y por qué, terminado en `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`. En el mismo commit, añade una línea a .ciclo/historial.md: `- AAAA-MM-DD HH:MM UTC · mejora · resultado`. Haz `git push origin master` (si hay conflicto: `git pull --rebase origin master` y reintenta).

## Cierre
- Si en todo el ciclo no hubo ninguna mejora aprobada, añade una línea al historial explicando por qué, haz commit y push.
- Lo que solo pueda hacer Juan (cuentas, dominios, Search Console, pagos, decisiones de negocio) se apunta al final de .ciclo/historial.md con el prefijo «PENDIENTE DE JUAN:», sin repetir lo ya apuntado.
- Termina con un resumen breve en español: qué se mejoró, qué se revirtió y por qué.
