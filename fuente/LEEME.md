# Cómo está montado Vivible

Una sola base de datos y un solo motor de cálculo; encima, tantos formatos (pantallas) como hagan falta.

```
fuente/
  precios.json        ← LA BASE DE DATOS: precios por ciudad y distrito, habitaciones, impuestos
  data.json           ← barrios y metro de Madrid
  nucleo/             ← EL MOTOR, común a todos los formatos (no toca la pantalla)
    nucleo.js           datos + leer anuncios + localizar + entorno (OpenStreetMap) + valoración + informe()
    informe.js          el informe como HTML (informeHTML) y como texto (informeTexto, para WhatsApp)
    exportar.js         permite usarlo desde Node (bots, pruebas)
    base.css            colores, tarjetas, controles y estilos del informe
  navegador/          ← piezas de pantalla que comparten los formatos de navegador
    ficha.js            la ficha del piso: campos, mapa, pegar anuncio, pedir y pintar el informe, compartir
    campos.html         los campos del piso (se insertan donde el formato pone __CAMPOS__)
  formatos/           ← LA PARTE GRÁFICA: un fichero por formato, solo pantalla e interacción
    web.html            portada por pasos            → index.html
    chat.html           conversación (para WhatsApp) → chat/index.html
  pruebas/nucleo.js   ← prueba del motor sin navegador
  build.py            ← lo genera todo
```

`python3 fuente/build.py` genera: `assets/vivible.js` (motor + datos), `assets/vivible-ficha.js`, `assets/vivible.css`, `datos.json` (los precios, para quien no use el JS), una página por formato, las páginas de ciudad y distrito, `sitemap.xml`, `robots.txt` y `404.html` (la página de «no existe» que GitHub Pages sirve en cualquier enlace roto).

## Reglas
- Un cálculo, un texto del informe o un dato se cambia **una sola vez**, en `nucleo/` o en `precios.json`. Nunca dentro de un formato.
- Un formato solo recoge datos, llama al motor y pinta. Si dos formatos necesitan lo mismo, va al núcleo.
- Todo lo que viene de fuera (OpenStreetMap, enlaces compartidos, texto pegado) se escapa con `esc()` antes de ponerlo en HTML.
- El motor no usa `document` ni `window`: así funciona igual en una web, en una app (WebView) o en un servidor.

## Cómo usa el motor un formato
```js
const f = {op:"venta", precio:320000, m2:75, hab:2};          // lo que falte se supone (completar)
const lugar = await locate(lat, lon);                          // {ck, d, auto}  — o parseAd(texto), o geocode(direccion)
const x = await informe(f, {...lugar, pt:[lat,lon]}, "Nuevos Ministerios");
if (x.error) …x.mensaje…  else  informeHTML(x)  /  informeTexto(x)  /  x.tot, x.parts, x.est…
```
`f.op`: `venta`, `alquiler` o `habitacion`. Campos de `f`: los de `completar()` en `nucleo.js`.

## Añadir un formato nuevo
- **De navegador** (otra web, app con WebView, widget): crear `fuente/formatos/<nombre>.html`, cargar `assets/vivible.css`, `assets/vivible.js` y, si usa la ficha, `assets/vivible-ficha.js` (cambiar `FORMATO.*` y llamar a `iniciarFicha()`), y apuntarlo en `FORMATOS` de `build.py`.
- **Sin navegador** (bot de WhatsApp, avisos): `const V = require("./assets/vivible.js")` en Node y responder con `V.informeTexto(x)`. Ejemplo completo: `pruebas/nucleo.js`. Necesita un servidor y una cuenta de WhatsApp Business (pendiente de Juan).
