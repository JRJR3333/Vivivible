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
  assert.strictEqual(V.modoPorPrecio("venta", 1300), "alquiler");
  console.log("núcleo OK");
})().catch(e => { console.error(e); process.exit(1); });
