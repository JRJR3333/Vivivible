# Vivible Madrid — instrucciones para Claude

Web estática publicada con GitHub Pages desde la rama `master` (raíz). Proyecto «Ganar Dinero» de Juan.

## Cómo se monta
- La página publicada es `index.html`, generada desde `fuente/template.html` sustituyendo `__DATA__` por `fuente/data.json`:
  `python3 -c "t=open('fuente/template.html').read();open('index.html','w').write(t.replace('__DATA__',open('fuente/data.json').read()))"`
- Nunca se edita `index.html` a mano: se cambia la plantilla y se vuelve a generar.
- `fuente/data.json` (barrios y estaciones) se genera con `fuente/prep.py` desde el geojson de barrios de Code for Germany y el CSV de paradas del CRTM.

## Datos que hay que mantener al día
- `PRICE` (venta €/m² y alquiler €/m²/mes por distrito, idealista): cada mes. Cambiar también el mes en el pie.
- `ROOM` (precio medio de una habitación en Madrid, idealista): cada trimestre.

## Antes de publicar
- Probar en un navegador sin errores: los tres modos (Comprar, Alquilar piso, Habitación), el mapa, la búsqueda por dirección y el selector de barrio.
- Textos en español de España, tuteando, claros y sin tecnicismos.
- Comprobar que el workflow «pages build and deployment» del último commit acaba en verde.
