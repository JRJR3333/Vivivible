// Prueba del núcleo sin navegador: node fuente/pruebas/nucleo.js  (después de python3 fuente/build.py)
// También sirve de ejemplo de cómo lo usaría otro formato (un bot de WhatsApp, una app…).
const assert = require("assert");
const V = require("../../assets/vivible.js");
// Sin internet: OpenStreetMap simulado
global.fetch = async (url, o) => {
  if (String(url).includes("nominatim") && String(url).includes("/search")) return { ok: true, json: async () => [{ lat: "40.4465", lon: "-3.6920" }] };
  if (String(url).includes("nominatim")) return { ok: true, json: async () => ({ address: { city_district: "Eixample" } }) };
  return { ok: true, json: async () => ({ elements: [
    { type: "node", lat: 40.4204, lon: -3.7050, tags: { railway: "station", station: "subway", name: "Gran Vía", line: "1;5" } },
    { type: "node", lat: 40.4201, lon: -3.7050, tags: { shop: "supermarket", name: "Súper" } } ] }) };
};
(async () => {
  // 1. todas las ciudades y distritos dan precio
  for (const [ck, c] of Object.entries(V.C)) for (const d of ["", ...Object.keys(c.d)]) {
    const p = V.dPrice(ck, d); assert(p.s > 300 && p.s < 20000 && p.r > 3 && p.r < 60, `precio raro en ${ck}/${d}`);
    assert(V.roomBase(ck, d) > 150, `habitación rara en ${ck}/${d}`);
  }
  // 2. leer un anuncio
  const { out } = V.parseAd("Piso en venta en calle de Fuencarral, 120, Madrid · 320.000 € · 75 m² construidos · 2 hab. · 1 baño · Planta 3ª exterior con ascensor");
  assert.deepStrictEqual([out.op, out.precio, out.m2, out.hab, out.planta, out.asc, out.ck], ["venta", 320000, 75, 2, 3, 1, "madrid"]);
  assert.strictEqual(V.parseAd("Habitación en piso compartido en Gràcia, Barcelona. 450 € al mes, 12 m2").out.op, "habitacion");
  // 2b. anuncios difíciles (auditoría del 2026-11-11): [texto, lo que debe salir]
  const AN = [
    ["Piso en venta en calle de Alcalá, 200, Salamanca, Madrid\n320.000 € 350.000 € 9%\n75 m² 2 hab.", { op: "venta", precio: 320000, d: "Salamanca" }],
    ["Piso en alquiler en Ruzafa, Valencia. Renta 1.300 €/mes. Gastos de comunidad 180 € a cargo del inquilino. 80 m²", { op: "alquiler", precio: 1300, m2: 80 }],
    ["Venta piso Eixample Barcelona 450.000,00 € 85 m2 3 dormitorios", { precio: 450000, hab: 3 }],
    ["Piso en alquiler en Nervión, Sevilla. 70 m2. Comunidad 60 € incluida. Precio a consultar.", { op: "alquiler", precio: undefined }],
    ["Comprar Alquilar Obra nueva\nPiso de alquiler en Calle Larios, Centro, Málaga\n1.100 € /mes\n2 habs. 65 m² 4ª Planta", { op: "alquiler", precio: 1100, estado: undefined, planta: 4 }],
    ["Alquiler de piso de 4 habitaciones en Moncloa, Madrid, ideal para estudiantes o compañeros de piso. 2.000 €/mes, 110 m²", { op: "alquiler", precio: 2000, m2: 110, hab: 4 }],
    ["Alquilo habitación luminosa para chica en Indautxu, Bilbao. 420 euros/mes. Habitación de 12 m2", { op: "habitacion", precio: 420, rm2: 12 }],
    ["Se vende piso de 90m2 situado en calle tranquila de Deusto, Bilbao. Precio: 410.000€", { dir: undefined, d: "Deusto", m2: 90 }],
    ["Piso en calle Fuencarral, 320.000 €, 2 habitaciones, 70 m², Madrid", { dir: "calle Fuencarral", precio: 320000 }],
    ["Ático en venta con terraza de 25 m². Vivienda de 95 m², 3 habitaciones. 600.000 €. Retiro, Madrid", { m2: 95, planta: 99 }],
    ["Se alquila piso de 1 habitación en Triana, Sevilla. 55 metros cuadrados. 850 euros al mes. No necesita reforma. Edificio de 5 plantas, no tiene ascensor.", { hab: 1, m2: 55, planta: undefined, asc: 0, estado: undefined }],
    ["Piso en venta en avenida de Madrid, 150, Delicias, Zaragoza. 150.000 € 70 m² 3 hab", { ck: "zaragoza", d: "Delicias" }],
    ["Piso en venta en La Latina, Madrid. 60 m², 380.000 €. Bajo cubierta con mucho encanto", { d: "Centro", planta: undefined }],
    ["Habitación en piso compartido en Benimaclet, Valencia. 9 m², 350 €/mes", { op: "habitacion", rm2: 9 }],
    ["Piso en alquiler en Gran Vía, Madrid. 1.500 €/mes. 60 m². 1 habitación. Sin ascensor, 4º piso", { planta: 4, asc: 0 }],
    ["Venta piso 3 habitaciones en Ruzafa, Valencia, 250.000 €", { planta: undefined, hab: 3 }],
    ["Habitación en piso compartido en Lavapiés, Madrid, 450 €/mes. 3 personas en el piso, 2 baños", { op: "habitacion", rban: "2", pers: 3 }],
    ["Habitación con baño privado en piso de 4 personas, 2 baños. Málaga 500 €/mes", { op: "habitacion", rban: "priv" }],
    ["Alquiler piso 3 dormitorios Bilbao Indautxu 1.250€/mes 95 m2 baño", { ban: undefined, hab: 3, m2: 95 }],
    ["Venta piso 80 m2 dormitorio principal con vestidor, 2 baños. Sevilla 200.000 €", { hab: undefined, ban: 2 }],
    ["Piso en venta en Madrid, 300.000 €, 80 m², portero automático, 3ª planta", { planta: 3 }],
    ["Piso en venta Madrid 300.000 € 80 m² sistema climático, 1ª planta", { planta: 1 }],
    ["Piso en venta Madrid 300.000 € 80 m² bajo consumo, 2ª planta", { planta: 2 }],
    ["Piso en alquiler en Madrid, 1.200 €/mes, 70 m2, a bajo precio, 3ª planta", { planta: 3 }],
    ["Piso en venta en Madrid, 250.000 €, 70 m². Planta: 2ª. Ascensor: No", { planta: 2, asc: 0 }],
    ["Ático en venta con terraza en Madrid, 400.000 €, 90 m²", { planta: 99 }],
    ["Sobreático en venta en Madrid, 890.000 €, 120 m²", { planta: 99 }],
    ["Piso en venta en Salamanca, Madrid, 1,2 millones de euros, 180 m²", { op: "venta", precio: 1200000 }],
    ["Ático en venta en Sarrià, Barcelona. 2.5 M€. 220 m2", { op: "venta", precio: 2500000 }],
    ["Piso bajo exterior en venta en Madrid, 200.000 €, 60 m²", { planta: 0 }],
  ];
  for (const [t, esp] of AN) { const o = V.parseAd(t).out; for (const [k, v] of Object.entries(esp)) assert.strictEqual(o[k], v, `«${t.slice(0, 40)}…» ${k}: ${o[k]} ≠ ${v}`); }
  assert.strictEqual(V.matchDistrict("malaga", ["Oeste"]), ""); assert.strictEqual(V.matchDistrict("barcelona", ["!!!"]), "");
  // 2c. lo que viene de fuera se escapa en el informe
  const xs = await V.informe({ op: "venta", m2: 80 }, { ck: "madrid", d: "Centro", pt: null, auto: "<img src=x onerror=1>" }, "");
  assert(!V.informeHTML(xs).includes("<img"));
  // 3. dónde cae un punto
  assert.deepStrictEqual((await V.locate(40.4200, -3.7050)).ck, "madrid");
  assert.strictEqual((await V.locate(41.39, 2.16)).d, "Eixample");
  assert.strictEqual(await V.locate(48.85, 2.35), null);
  // 4. informe completo en los tres modos, con y sin punto exacto
  const lugar = { ck: "madrid", d: "Centro", pt: [40.42, -3.705], auto: "Sol" };
  for (const f of [{ op: "venta", precio: 320000, m2: 75 }, { op: "alquiler", precio: 1400 }, { op: "habitacion", precio: 550 }])
    for (const l of [lugar, { ck: "sevilla", d: "Pino Montano", pt: null }]) {
      const x = await V.informe(f, l, l.pt ? "Nuevos Ministerios" : "");
      assert(!x.error, x.mensaje); assert(x.tot >= 1 && x.tot <= 10); assert(x.est > 0);
      assert(V.informeHTML(x).includes("<section")); assert(V.informeTexto(x).includes("/10"));
      if (l.pt) assert(x.work && x.work.min > 0 && x.env.st.length === 1);
    }
  // 5. datos que no cuadran
  assert.strictEqual((await V.informe({ op: "venta", precio: 900, m2: 75 }, lugar)).error, "precioBajo");
  assert.strictEqual((await V.informe({ op: "venta" }, { ck: "madrid", d: "", pt: null })).error, "lugar");
  assert(!(await V.informe({ op: "venta" }, { ck: "murcia", d: "", pt: null, media: true })).error);
  // sin punto exacto no se puntúan transporte ni servicios (antes salía «Transporte 3» y hundía la nota)
  const sp = await V.informe({ op: "alquiler", precio: 1400, m2: 70, hab: 2 }, { ck: "madrid", d: "Salamanca", pt: null });
  assert(!sp.parts.some(p => p[0] === "Transporte" || p[0] === "Servicios y verde") && sp.tot >= 6, "sin punto: " + sp.tot);
  assert.strictEqual(V.modoPorPrecio("venta", 1300), "alquiler");
  // el texto para WhatsApp no lleva códigos HTML (&#39;) y la horquilla de alquiler va con /mes
  const fe = global.fetch;
  global.fetch = async () => ({ ok: true, json: async () => ({ elements: [{ type: "way", center: { lat: 41.392, lon: 2.16 }, tags: { highway: "primary", name: "Carrer d'Aragó" } }] }) });
  const tb = V.informeTexto(await V.informe({ op: "alquiler", precio: 1300, m2: 70 }, { ck: "barcelona", d: "Eixample", pt: [41.392, 2.16] }, ""));
  global.fetch = fe;
  assert(tb.includes("Carrer d'Aragó") && !/&#39;|&amp;/.test(tb), tb);
  assert(/entre [\d.]+ €\/mes y [\d.]+ €\/mes/.test(tb), tb);
  console.log("núcleo OK");
})().catch(e => { console.error(e); process.exit(1); });
