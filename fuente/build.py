"""Genera la web de Vivible: index.html, páginas por ciudad y distrito, sitemap.xml y robots.txt.
Uso (desde la raíz del repositorio):  python3 fuente/build.py
"""
import json, os, re, unicodedata, html
from urllib.parse import quote

BASE = "https://jrjr3333.github.io/Vivivible/"
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
F = lambda *p: os.path.join(ROOT, *p)

P = json.load(open(F("fuente", "precios.json"), encoding="utf-8"))
MAD = open(F("fuente", "data.json"), encoding="utf-8").read()
C = P["ciudades"]

# «en la Comunidad de Madrid», «en las Illes Balears»… (los nombres de precios.json van sin artículo)
ART = {"Comunidad de Madrid": "la ", "Comunitat Valenciana": "la ", "Región de Murcia": "la ", "Illes Balears": "las ", "País Vasco (Bizkaia)": "el "}
def en_ccaa(n): return "en " + ART.get(n, "") + n

def slug(s):
    s = unicodedata.normalize("NFD", s.lower())
    s = "".join(ch for ch in s if unicodedata.category(ch) != "Mn")
    return re.sub(r"[^a-z0-9]+", "-", s).strip("-")

def fmt(n): return f"{round(n):,}".replace(",", ".")
def dec(n, d=1): return f"{n:.{d}f}".replace(".", ",")
def esc(s): return html.escape(s, quote=True)

def dprice(c, d):
    s, r = c["d"][d]
    es = er = False
    if s is None: s = c["venta"] * (r / c["alquiler"]) ** 1.5; es = True
    if r is None: r = c["alquiler"] * (s / c["venta"]) ** .5; er = True
    return s, r, es, er

def hab_d(c, r):
    # habitación en un distrito: media de la ciudad ajustada por lo caro que es su alquiler (la misma fórmula en todas las páginas)
    return round(c["hab"] * (r / c["alquiler"]) ** .8 / 5) * 5

FAV = "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 32 32'%3E%3Crect width='32' height='32' rx='8' fill='%231f6f54'/%3E%3Cpath d='M8 16l8-7 8 7v8h-5v-5h-6v5H8z' fill='%23fff'/%3E%3C/svg%3E"
HEADX = f'<link rel="icon" href="{FAV}"><meta name="theme-color" content="#1f6f54"><meta property="og:type" content="website"><meta property="og:site_name" content="Vivible"><meta property="og:locale" content="es_ES"><meta name="twitter:card" content="summary_large_image"><meta property="og:image" content="{BASE}assets/og.png"><meta property="og:image:width" content="1200"><meta property="og:image:height" content="630"><meta property="og:image:alt" content="Vivible: ¿se vive bien en ese piso?">\n'

# periodo de los datos, calculado de los meses de cada ciudad (p. ej. «julio–octubre 2026»)
MESES = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"]
_ms = sorted((int(a), MESES.index(m)) for c in C.values() for m, a in re.findall(r"([a-záéíóú]+)(?:–[a-záéíóú]+)* (\d{4})", c["mes"]) if m in MESES)
_ms += sorted((int(a), MESES.index(m)) for c in C.values() for m, a in re.findall(r"–([a-záéíóú]+) (\d{4})", c["mes"]) if m in MESES)
_ms.sort()
(a0, m0), (a1, m1) = _ms[0], _ms[-1]
mes_txt = (f"{MESES[m0]} {a0}" if (a0, m0) == (a1, m1) else f"{MESES[m0]}–{MESES[m1]} {a1}" if a0 == a1 else f"{MESES[m0]} {a0}–{MESES[m1]} {a1}")

# ---------- núcleo común: assets/vivible.js, assets/vivible.css y datos.json
# Todos los formatos (web, conversación y los que vengan) cargan estos mismos ficheros.
import hashlib
rd = lambda *p: open(F(*p), encoding="utf-8").read()
PJ = json.dumps(P, ensure_ascii=False, separators=(",", ":"))
core = (rd("fuente", "nucleo", "nucleo.js").replace("__PRECIOS__", PJ).replace("__MADRID__", MAD)
        + "\n" + rd("fuente", "nucleo", "informe.js") + rd("fuente", "nucleo", "exportar.js"))
css = rd("fuente", "nucleo", "base.css")
open(F("assets", "vivible.js"), "w", encoding="utf-8").write(core)
open(F("assets", "vivible.css"), "w", encoding="utf-8").write(css)
open(F("datos.json"), "w", encoding="utf-8").write(PJ)  # los mismos precios, para apps o bots que no usen el JS
ficha = rd("fuente", "navegador", "ficha.js")  # la ficha del piso, común a los formatos de navegador
open(F("assets", "vivible-ficha.js"), "w", encoding="utf-8").write(ficha)
CAMPOS = rd("fuente", "navegador", "campos.html").rstrip("\n")
V = hashlib.md5((core + css + ficha).encode("utf-8")).hexdigest()[:8]

# ---------- formatos: cada uno es solo pantalla (fuente/formatos/<nombre>.html)
# nombre del fichero -> carpeta donde se publica ("" = portada)
FORMATOS = {"web": "", "chat": "chat"}
for nombre, carpeta in FORMATOS.items():
    pre = "../" if carpeta else ""
    t = rd("fuente", "formatos", nombre + ".html")
    links = "".join(f'<a href="{pre}{k}/">Vivir en {esc(c["n"])}</a>' for k, c in C.items()) + f'<a href="{pre}precios/">Comparar ciudades</a>'
    if pre: t = t.replace('href="assets/', f'href="{pre}assets/').replace('src="assets/', f'src="{pre}assets/')
    t = t.replace("__CAMPOS__", CAMPOS).replace("__HEADX__", HEADX).replace("__MESES__", mes_txt).replace("__CIUDADES__", links).replace("__V__", V)
    if not carpeta:  # portada: datos estructurados para que Google sepa qué es (la de /chat/ tiene canonical a la portada)
        ldw = json.dumps({"@context": "https://schema.org", "@type": "WebApplication", "name": "Vivible", "url": BASE,
            "inLanguage": "es-ES", "applicationCategory": "UtilitiesApplication", "operatingSystem": "Web",
            "description": "Valora gratis un piso en venta o alquiler, o una habitación: precio, transporte, ruido y servicios de la zona.",
            "offers": {"@type": "Offer", "price": "0", "priceCurrency": "EUR"},
            "areaServed": [{"@type": "City", "name": c["n"]} for c in C.values()]}, ensure_ascii=False).replace("</", "<\\/")
        t = t.replace("</head>", f'<script type="application/ld+json">{ldw}</script>\n</head>', 1)
    assert "__" not in t.replace("window.__viv", ""), "queda un marcador sin sustituir en " + nombre
    if carpeta: os.makedirs(F(carpeta), exist_ok=True)
    open(F(carpeta, "index.html") if carpeta else F("index.html"), "w", encoding="utf-8").write(t)

# ---------- static pages
CSS = """body{margin:0;background:#f6f3ee;color:#1d2321;font:16px/1.6 Inter,system-ui,sans-serif}.w{max-width:760px;margin:0 auto;padding:20px 16px 60px}
a{color:#1f6f54}h1{font:700 30px/1.15 Fraunces,Georgia,serif;margin:10px 0}.b{display:inline-block;font-size:12px;font-weight:600;color:#1f6f54;background:#e8f2ec;padding:3px 10px;border-radius:99px;text-decoration:none}
.card{background:#fff;border:1px solid #e4dfd6;border-radius:16px;padding:18px;margin-top:16px}.g{display:grid;grid-template-columns:1fr 1fr;gap:12px}.k{background:#faf8f4;border:1px solid #e4dfd6;border-radius:12px;padding:12px}
.k small{display:block;color:#5f6b66;font-size:12px}.k b{font:700 24px Fraunces,serif}.cta{display:block;text-align:center;background:#1f6f54;color:#fff;text-decoration:none;font-weight:700;padding:15px;border-radius:12px;margin-top:18px}
table{width:100%;border-collapse:collapse;font-size:14px}td,th{padding:7px 4px;border-top:1px solid #f1ede6;text-align:left}td:last-child,th:last-child{text-align:right}.m{color:#5f6b66;font-size:13px}.card.m a{display:inline-block;min-height:44px;line-height:44px;padding:0 2px}
.cmp td+td,.cmp th+th{white-space:nowrap}@media(max-width:480px){.cmp{font-size:13px}.cmp td,.cmp th{padding:7px 2px}.card:has(.cmp){padding:14px 10px}}.faq h2{font:700 21px/1.2 Fraunces,Georgia,serif;margin:0 0 4px}.faq h3{font-size:16px;margin:14px 0 2px}.faq p{margin:0}
@media(max-width:480px){.g{grid-template-columns:1fr}h1{font-size:26px}}"""

def tit_distrito(d, cn):
    t = f"{d}, {cn}: precio por m² y alquiler 2026 | Vivible"
    if len(t) > 65: t = t.replace(" | Vivible", "")
    if len(t) > 65: t = t.replace(" y alquiler", "")
    return t


def desc_corta(base, cola):
    # Google corta las descripciones de más de ~160 caracteres: la coletilla solo va si cabe
    return base + cola if len(base + cola) <= 160 else base


def faq(preguntas):
    """Bloque «Preguntas frecuentes» visible + sus datos estructurados (FAQPage). preguntas: [(pregunta, respuesta en texto)]"""
    h = '<section class="card faq"><h2>Preguntas frecuentes</h2>' + "".join(f"<h3>{esc(q)}</h3><p>{esc(a)}</p>" for q, a in preguntas) + "</section>"
    ld = json.dumps({"@context": "https://schema.org", "@type": "FAQPage", "mainEntity": [
        {"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": a}} for q, a in preguntas]},
        ensure_ascii=False).replace("</", "<\\/")
    return h, ld


def page(title, desc, path, body, crumbs, extra_ld=None):
    canon = BASE + path
    bc = " › ".join(f'<a href="{u}">{esc(n)}</a>' if u else esc(n) for n, u in crumbs)
    depth = path.count("/")
    ld = json.dumps({"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": [
        {"@type": "ListItem", "position": i + 1, "name": n,
         "item": BASE + "/".join(path.split("/")[:i]) + ("/" if i else "")} for i, (n, u) in enumerate(crumbs)]},
        ensure_ascii=False).replace("</", "<\\/")
    return f"""<!DOCTYPE html><html lang="es"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(title)}</title><meta name="description" content="{esc(desc)}"><link rel="canonical" href="{canon}">
{HEADX}<meta property="og:title" content="{esc(title)}"><meta property="og:description" content="{esc(desc)}"><meta property="og:url" content="{canon}">
<script type="application/ld+json">{ld}</script>{f'<script type="application/ld+json">{extra_ld}</script>' if extra_ld else ""}
<link rel="preconnect" href="https://fonts.googleapis.com"><link href="https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,700&family=Inter:wght@400;600;700&display=swap" rel="stylesheet">
<style>{CSS}</style></head><body><div class="w"><nav class="m" aria-label="Migas de pan">{bc}</nav><main>{body}</main>
<footer class="m" style="margin-top:28px">Datos: precios medios de idealista ({esc(mes_txt)}); habitaciones: precio medio de la ciudad. Estimaciones orientativas, no tasaciones oficiales. Hecho por <a href="{"../" * path.count("/")}">Vivible</a>.</footer></div></body></html>"""

urls = [BASE]
for ck, c in C.items():
    rows = sorted(((d, *dprice(c, d)) for d in c["d"]), key=lambda x: -x[1])
    n = len(rows)
    os.makedirs(F(ck), exist_ok=True)
    # city page
    tr = "".join(f'<tr><td><a href="{slug(d)}/">{esc(d)}</a></td><td>{fmt(s)} €/m²{"*" if es else ""}</td><td>{dec(r)} €/m²{"*" if er else ""}</td></tr>' for d, s, r, es, er in rows)
    nota = '<p class="m">* Estimado a partir del otro precio del distrito: idealista no publica ese dato.</p>' if any(x[3] or x[4] for x in rows) else ""
    rent_c = c["alquiler"] * 70
    bv, ba = min(rows, key=lambda x: x[1]), min(rows, key=lambda x: x[2])
    av = max(rows, key=lambda x: x[2])
    itp_t = str(c["itp"]).replace(".", ",")
    fq_html, fq_ld = faq([
        (f"¿Cuánto cuesta alquilar un piso en {c['n']}?",
         f"De media, {dec(c['alquiler'])} € por m² al mes: un piso de 70 m² ronda los {fmt(rent_c)} € al mes. "
         f"Va de unos {fmt(ba[2] * 70)} € en {ba[0]}{' (estimado)' if ba[4] else ''} a unos {fmt(av[2] * 70)} € en {av[0]}{' (estimado)' if av[4] else ''}."),
        (f"¿Cuánto cuesta una habitación en {c['n']}?",
         f"Una habitación en piso compartido cuesta de media unos {fmt(c['hab'])} € al mes en {c['n']}. En los distritos caros suele pagarse más y en los asequibles, menos."),
        (f"¿Qué impuestos se pagan al comprar un piso en {c['n']}?",
         f"Un piso de segunda mano paga el impuesto de transmisiones (ITP) {en_ccaa(c['ccaa'])}: el {itp_t} % del precio (tipo general). "
         f"Uno nuevo paga un 10 % de IVA y un {dec(c['ajd'], 2).rstrip('0').rstrip(',')} % de actos jurídicos documentados. Además, notaría, registro y gestoría suman alrededor de un 1,5 %."),
        (f"¿Cuál es el distrito más barato de {c['n']}?",
         f"Para comprar, {bv[0]}: {fmt(bv[1])} €/m²{' (estimado)' if bv[3] else ''}, frente a {fmt(c['venta'])} €/m² de media. "
         + (f"Para alquilar también es el más barato." if ba[0] == bv[0] else f"Para alquilar, {ba[0]}: {dec(ba[2])} €/m² al mes{' (estimado)' if ba[4] else ''}.")),
    ])
    body = f"""<h1>Vivir en {esc(c["n"])}: precio por distritos ({esc(c["mes"])})</h1>
<p>Comprar en {esc(c["n"])} cuesta de media <b>{fmt(c["venta"])} €/m²</b> y alquilar <b>{dec(c["alquiler"])} €/m² al mes</b>. Una habitación en piso compartido ronda los <b>{fmt(c["hab"])} € al mes</b>. Estos son los {n} distritos, del más caro al más barato.</p>
<div class="card"><table><caption class="m" style="text-align:left;padding-bottom:6px">Precio medio por m² en cada distrito de {esc(c["n"])} ({esc(c["mes"])})</caption><tr><th scope="col">Distrito</th><th scope="col">Venta</th><th scope="col">Alquiler/mes</th></tr>{tr}</table>{nota}</div>
{fq_html}
<a class="cta" href="../#c={ck}">Analiza un piso concreto en {esc(c["n"])}</a>
<div class="card m"><b>¿Vas a comprar?</b> <a href="gastos-de-compra/">Gastos e impuestos de comprar un piso en {esc(c["n"])}</a></div>
<div class="card m"><b>¿Vas a alquilar?</b> <a href="sueldo-para-alquilar/">Cuánto hay que ganar para alquilar en {esc(c["n"])}</a></div>
<div class="card m"><b>¿Buscas habitación?</b> <a href="habitacion/">Precio de una habitación en {esc(c["n"])} por distritos</a></div>
<div class="card m"><b>¿Dudas?</b> <a href="comprar-o-alquilar/">Comprar o alquilar en {esc(c["n"])}: hipoteca frente a alquiler</a></div>
<div class="card m"><b>Otras ciudades:</b> {" · ".join(f'<a href="../{k2}/">{esc(c2["n"])}</a>' for k2, c2 in C.items() if k2 != ck)} · <a href="../precios/">Comparar las 10 ciudades</a></div>"""
    open(F(ck, "index.html"), "w", encoding="utf-8").write(page(
        f"Vivir en {c['n']}: precio de la vivienda por distritos (2026) | Vivible",
        f"Precio medio de compra, alquiler y habitación en los {n} distritos de {c['n']}. Compara barrios y analiza un piso gratis.",
        f"{ck}/", body, [("Vivible", "../"), (c["n"], None)], fq_ld))
    urls.append(BASE + ck + "/")
    # district pages
    for i, (d, s, r, es, er) in enumerate(rows):
        sd = slug(d); os.makedirs(F(ck, sd), exist_ok=True)
        vs = (s / c["venta"] - 1) * 100
        tier = "de los más caros" if i < n / 3 else ("de precio medio" if i < 2 * n / 3 else "de los más asequibles")
        buy70 = s * 70; rent70 = r * 70
        room = hab_d(c, r)
        ahorro = buy70 * (.2 + c["itp"] / 100 + .015) + 400
        cuota = buy70 * .8 * (.028 / 12) / (1 - (1 + .028 / 12) ** -360)
        yld = rent70 * 12 / buy70 * 100
        consejo = {
            "de los más caros": f"Es una zona cara de {c['n']}: aquí se paga la ubicación. Fíjate en que el piso justifique el precio (ascensor, luz, estado) y compara con distritos vecinos.",
            "de precio medio": f"Está en la franja media de {c['n']}: suele haber buen equilibrio entre precio y servicios. Revisa el transporte hasta tu trabajo antes de decidir.",
            "de los más asequibles": f"Es de las zonas más asequibles de {c['n']}. Puede ser una buena oportunidad, pero revisa con calma el estado del edificio, el transporte y el ambiente de la calle de día y de noche.",
        }[tier]
        dq_html, dq_ld = faq([
            (f"¿Cuánto cuesta alquilar un piso en {d}?",
             f"Un piso de 70 m² en {d} ronda los {fmt(rent70)} € al mes ({dec(r)} €/m² al mes{', estimado' if er else ''}), frente a unos {fmt(c['alquiler'] * 70)} € de media en {c['n']}. "
             f"Para pagarlo sin apuros conviene ingresar unos {fmt(rent70 / .33)} € al mes."),
            (f"¿Cuánto cuesta una habitación en {d}?",
             f"Unos {fmt(room)} € al mes, calculado a partir de la media de {c['n']} ({fmt(c['hab'])} €) y de lo caro que es el alquiler en {d}."),
            (f"¿Cuánto dinero necesito para comprar un piso en {d}?",
             f"Un piso de 70 m² cuesta unos {fmt(buy70)} €{' (estimado)' if es else ''}. Necesitas ahorrado unos {fmt(ahorro)} €: el 20 % de entrada ({fmt(buy70 * .2)} €), "
             f"el {str(c['itp']).replace('.', ',')} % de impuesto de compra de segunda mano {en_ccaa(c['ccaa'])} ({fmt(buy70 * c['itp'] / 100)} €) y unos {fmt(buy70 * .015 + 400)} € de notaría, registro, gestoría y tasación. "
             f"La hipoteca del resto (30 años al 2,8 %) saldría por unos {fmt(cuota)} € al mes."),
        ])
        otros = " · ".join(f'<a href="../{slug(o)}/">{esc(o)}</a>' for o, *_ in rows if o != d)
        body = f"""<h1>Vivir en {esc(d)} ({esc(c["n"])}): precio, alquiler y habitación</h1>
<p>{esc(d)} es {"el <b>distrito más caro</b>" if i == 0 else ("el <b>distrito más asequible</b>" if i == n - 1 else f"el <b>{i+1}º distrito más caro</b>")} de {n} en {esc(c["n"])}{"" if i in (0, n - 1) else ": " + tier}. {"Comprar cuesta lo mismo que la media de la ciudad" if round(abs(vs)) == 0 else f'Comprar cuesta un {dec(abs(vs),0)} % {"más" if vs >= 0 else "menos"} que la media de la ciudad'}{" (dato estimado)" if es else ""}.</p>
<div class="g"><div class="k"><small>Comprar{" (estimado)" if es else ""}</small><b>{fmt(s)} €/m²</b><small>Media de {esc(c["n"])}: {fmt(c["venta"])} €/m²</small></div>
<div class="k"><small>Alquilar{" (estimado)" if er else ""}</small><b>{dec(r)} €/m²/mes</b><small>Media: {dec(c["alquiler"])} €/m²/mes</small></div>
<div class="k"><small>Piso de 70 m² en venta</small><b>≈ {fmt(buy70)} €</b><small>Ahorros necesarios: ≈ {fmt(ahorro)} €</small></div>
<div class="k"><small>Piso de 70 m² en alquiler</small><b>≈ {fmt(rent70)} €/mes</b><small>Ingresos recomendados: ≈ {fmt(rent70/.33)} €/mes</small></div>
<div class="k"><small>Habitación en piso compartido</small><b>≈ {fmt(room)} €/mes</b><small>Media de la ciudad: {fmt(c["hab"])} €/mes</small></div>
<div class="k"><small>Hipoteca de ese piso (80 %, 30 años, 2,8 %)</small><b>≈ {fmt(cuota)} €/mes</b><small>Rentabilidad bruta si se alquila: {dec(yld)} %</small></div></div>
<div class="card"><b>Lo que debes saber</b><p>{esc(consejo)} El impuesto de compra de segunda mano {esc(en_ccaa(c["ccaa"]))} es del {str(c["itp"]).replace(".", ",")} % (tipo general).</p></div>
{dq_html}
<a class="cta" href="../../#c={ck}&d={quote(d)}">¿Tienes un piso en {esc(d)}? Analízalo gratis</a>
<div class="card m"><b>¿Vas a comprar?</b> <a href="../gastos-de-compra/">Gastos e impuestos de comprar un piso en {esc(c["n"])}</a></div>
<div class="card m"><b>¿Vas a alquilar?</b> <a href="../sueldo-para-alquilar/">Cuánto hay que ganar para alquilar en {esc(c["n"])}</a></div>
<div class="card m"><b>¿Buscas habitación?</b> <a href="../habitacion/">Precio de una habitación en {esc(c["n"])} por distritos</a></div>
<div class="card m"><b>¿Dudas?</b> <a href="../comprar-o-alquilar/">Comprar o alquilar en {esc(c["n"])}: hipoteca frente a alquiler</a></div>
<div class="card m"><b>Otros distritos de {esc(c["n"])}:</b> {otros}</div>"""
        open(F(ck, sd, "index.html"), "w", encoding="utf-8").write(page(
            tit_distrito(d, c['n']),
            desc_corta(f"{d} ({c['n']}): {fmt(s)} €/m² en venta, {dec(r)} €/m² de alquiler y habitación por unos {fmt(room)} €.", " Cuánto necesitas para comprar o alquilar."),
            f"{ck}/{sd}/", body, [("Vivible", "../../"), (c["n"], "../"), (d, None)], dq_ld))
        urls.append(BASE + f"{ck}/{sd}/")

# ---------- gastos de compra por ciudad (<ciudad>/gastos-de-compra/): lo que la gente busca como
# «gastos de comprar un piso en <ciudad>» o «ITP en <comunidad>»; todo sale de precios.json
NOT, TAS = .015, 400  # notaría, registro y gestoría (≈1,5 %) y tasación: las mismas cifras que en las páginas de distrito
pct = lambda x: dec(x, 2).rstrip("0").rstrip(",")
def gastos(precio, c, nueva=False):
    imp = precio * ((10 + c["ajd"]) if nueva else c["itp"]) / 100
    otros = precio * NOT + TAS
    return imp, otros, precio * .2 + imp + otros
for ck, c in C.items():
    assert "gastos-de-compra" not in [slug(d) for d in c["d"]]
    med = c["venta"] * 70
    ejemplos = sorted({round(med / 5e4) * 5e4 or 5e4, 150000, 250000, 400000})
    def fila(precio, nueva=False):
        imp, otros, tot = gastos(precio, c, nueva)
        return f"<tr><td>{fmt(precio)} €</td><td>{fmt(imp)} €</td><td>{fmt(otros)} €</td><td><b>{fmt(tot)} €</b></td></tr>"
    cab = '<tr><th scope="col">Precio</th><th scope="col">Impuesto</th><th scope="col">Notaría y más</th><th scope="col">Ahorro total</th></tr>'
    i2, o2, t2 = gastos(med, c); i1, o1, t1 = gastos(med, c, True)
    cuota = med * .8 * (.028 / 12) / (1 - (1 + .028 / 12) ** -360)
    ccaa = en_ccaa(c["ccaa"]); itp = pct(c["itp"]); ajd = pct(c["ajd"])
    gq_html, gq_ld = faq([
        (f"¿Cuánto es el ITP {ccaa}?",
         f"El tipo general del impuesto de transmisiones patrimoniales {ccaa} es del {itp} % del precio de compra. Lo paga quien compra un piso de segunda mano. "
         "Algunas comunidades rebajan el tipo a jóvenes, familias numerosas o pisos baratos: consúltalo en la web de tu comunidad antes de firmar."),
        (f"¿Cuánto dinero necesito ahorrado para comprar un piso en {c['n']}?",
         f"Para un piso medio de 70 m² en {c['n']} (unos {fmt(med)} €) necesitas unos {fmt(t2)} €: el 20 % de entrada ({fmt(med * .2)} €), {fmt(i2)} € de ITP y unos {fmt(o2)} € de notaría, registro, gestoría y tasación. "
         f"La hipoteca del 80 % restante, a 30 años y al 2,8 %, saldría por unos {fmt(cuota)} € al mes."),
        (f"¿Qué impuestos paga un piso de obra nueva en {c['n']}?",
         f"No paga ITP: paga un 10 % de IVA y un {ajd} % de actos jurídicos documentados (AJD) {ccaa}. Para un piso de {fmt(med)} € son {fmt(i1)} € de impuestos, {fmt(i1 - i2)} € más que si fuera de segunda mano."),
        ("¿Quién paga los gastos de la hipoteca?",
         "Desde 2019 el banco paga la notaría, el registro, la gestoría y el impuesto de la escritura de la hipoteca. Tú pagas la tasación y los gastos de la escritura de compraventa."),
    ])
    body = f"""<h1>Gastos de comprar un piso en {esc(c["n"])} (2026): impuestos y cuánto ahorrar</h1>
<p>Al precio del piso hay que sumarle los impuestos y los gastos de la compra. En {esc(c["n"])}, un piso de segunda mano paga el <b>{itp} % de ITP</b> {esc(ccaa)} y uno nuevo, un <b>10 % de IVA y un {ajd} % de AJD</b>. Además, el banco suele financiar como mucho el 80 %, así que la entrada (el 20 %) también sale de tus ahorros.</p>
<div class="g"><div class="k"><small>Piso medio de 70 m² en {esc(c["n"])}</small><b>≈ {fmt(med)} €</b><small>A {fmt(c["venta"])} €/m² ({esc(c["mes"])})</small></div>
<div class="k"><small>Ahorro necesario (segunda mano)</small><b>≈ {fmt(t2)} €</b><small>Entrada, ITP y gastos</small></div>
<div class="k"><small>Ahorro necesario (obra nueva)</small><b>≈ {fmt(t1)} €</b><small>Entrada, IVA, AJD y gastos</small></div>
<div class="k"><small>Hipoteca (80 %, 30 años, 2,8 %)</small><b>≈ {fmt(cuota)} €/mes</b><small>Sin contar seguros</small></div></div>
<div class="card"><table class="cmp"><caption class="m" style="text-align:left;padding-bottom:6px">Piso de segunda mano: ITP del {itp} %, notaría, registro, gestoría y tasación, y ahorro total con el 20 % de entrada</caption>{cab}{"".join(fila(x) for x in ejemplos)}</table></div>
<div class="card"><table class="cmp"><caption class="m" style="text-align:left;padding-bottom:6px">Piso de obra nueva: 10 % de IVA y {ajd} % de AJD, gastos y ahorro total con el 20 % de entrada</caption>{cab}{"".join(fila(x, True) for x in ejemplos)}</table>
<p class="m">«Notaría y más»: notaría, registro y gestoría (≈ 1,5 % del precio) y tasación (≈ {TAS} €). Tipos generales; puede haber rebajas según tu edad o tu familia.</p></div>
{gq_html}
<a class="cta" href="../../#c={ck}">Analiza un piso concreto en {esc(c["n"])}</a>
<div class="card m"><b>Precios en {esc(c["n"])}:</b> <a href="../">Por distritos</a> · <a href="../sueldo-para-alquilar/">Sueldo para alquilar</a> · <a href="../../precios/">Comparar las 10 ciudades</a></div>"""
    os.makedirs(F(ck, "gastos-de-compra"), exist_ok=True)
    open(F(ck, "gastos-de-compra", "index.html"), "w", encoding="utf-8").write(page(
        f"Gastos de comprar un piso en {c['n']} (2026): ITP e impuestos",
        desc_corta(f"Cuánto cuesta comprar un piso en {c['n']}: ITP del {itp} %, IVA y AJD de obra nueva, notaría y registro, y cuánto ahorrar.", " Con ejemplos."),
        f"{ck}/gastos-de-compra/", body, [("Vivible", "../../"), (c["n"], "../"), ("Gastos de compra", None)], gq_ld))
    urls.append(BASE + f"{ck}/gastos-de-compra/")

# ---------- sueldo para alquilar por ciudad (<ciudad>/sueldo-para-alquilar/): «cuánto hay que ganar para alquilar en <ciudad>»;
# misma regla que el informe (alquiler + gastos ≤ 33 % de los ingresos netos; habitación con unos 55 € de gastos)
ESF, GHAB, M2A = .33, 55, 70
for ck, c in C.items():
    assert "sueldo-para-alquilar" not in [slug(d) for d in c["d"]]
    rows = sorted(((d, dprice(c, d)[1] * M2A, dprice(c, d)[3]) for d in c["d"]), key=lambda x: x[1])
    rc, hab = c["alquiler"] * M2A, c["hab"]
    sc, sh = rc / ESF, (hab + GHAB) / ESF
    bar, car = rows[0], rows[-1]
    tr = "".join(f'<tr><td><a href="../{slug(d)}/">{esc(d)}</a></td><td>{fmt(r)} €{"*" if e else ""}</td><td><b>{fmt(r / ESF)} €</b></td></tr>' for d, r, e in rows)
    nota = '<p class="m">* Alquiler estimado a partir del precio de venta del distrito: idealista no publica ese dato.</p>' if any(e for _, _, e in rows) else ""
    sq_html, sq_ld = faq([
        (f"¿Cuánto hay que ganar para alquilar un piso en {c['n']}?",
         f"Un piso medio de {M2A} m² en {c['n']} cuesta unos {fmt(rc)} € al mes ({dec(c['alquiler'])} €/m², {c['mes']}). Para que el alquiler no pase del 33 % de lo que ganas, necesitas unos {fmt(sc)} € netos al mes. "
         f"Si lo pagáis entre dos, basta con unos {fmt(sc / 2)} € netos cada uno."),
        (f"¿Cuánto hay que ganar para alquilar una habitación en {c['n']}?",
         f"Una habitación cuesta de media unos {fmt(hab)} € al mes en {c['n']}. Sumando unos {GHAB} € de gastos (luz, agua, internet), lo recomendable es ganar unos {fmt(sh)} € netos al mes."),
        (f"¿Cuál es el distrito más barato para alquilar en {c['n']}?",
         f"{bar[0]}: un piso de {M2A} m² sale por unos {fmt(bar[1])} € al mes y basta con ganar unos {fmt(bar[1] / ESF)} € netos. El más caro es {car[0]}, con unos {fmt(car[1])} € al mes ({fmt(car[1] / ESF)} € netos recomendados)."),
        (f"¿Cuánto dinero necesito para entrar a vivir de alquiler en {c['n']}?",
         f"Para el piso medio ({fmt(rc)} €/mes): el primer mes, la fianza legal de un mes y, si te la piden, una garantía adicional de hasta dos meses más. En total, entre {fmt(rc * 2)} € y {fmt(rc * 4)} €. "
         "Los honorarios de la inmobiliaria los paga el propietario (Ley 12/2023), no tú."),
    ])
    body = f"""<h1>¿Cuánto hay que ganar para alquilar en {esc(c["n"])}? (2026)</h1>
<p>La regla más usada (y la que piden muchos propietarios) es que el alquiler no pase de un tercio de lo que ganas. Con el precio medio de {esc(c["n"])} ({dec(c["alquiler"])} €/m² al mes, {esc(c["mes"])}), esto es lo que necesitas ganar en neto al mes en cada distrito.</p>
<div class="g"><div class="k"><small>Piso medio de {M2A} m² en {esc(c["n"])}</small><b>≈ {fmt(rc)} €/mes</b><small>Necesitas ganar ≈ {fmt(sc)} € netos</small></div>
<div class="k"><small>Habitación en {esc(c["n"])}</small><b>≈ {fmt(hab)} €/mes</b><small>Necesitas ganar ≈ {fmt(sh)} € netos</small></div>
<div class="k"><small>Piso medio entre dos</small><b>≈ {fmt(sc / 2)} €</b><small>Netos al mes cada uno</small></div>
<div class="k"><small>Para entrar (piso medio)</small><b>{fmt(rc * 2)}–{fmt(rc * 4)} €</b><small>Primer mes, fianza y garantía</small></div></div>
<div class="card"><table class="cmp"><caption class="m" style="text-align:left;padding-bottom:6px">Piso de {M2A} m² por distritos, del más barato al más caro: alquiler al mes y sueldo neto recomendado (alquiler ≤ 33 %)</caption><tr><th scope="col">Distrito</th><th scope="col">Alquiler</th><th scope="col">Sueldo neto</th></tr>{tr}</table>{nota}</div>
{sq_html}
<a class="cta" href="../../#c={ck}&op=alquiler">¿Has visto un piso? Comprueba si te lo puedes permitir</a>
<div class="card m"><b>Más sobre {esc(c["n"])}:</b> <a href="../">Precios por distritos</a> · <a href="../gastos-de-compra/">Gastos de comprar</a> · <a href="../comprar-o-alquilar/">Comprar o alquilar</a> · <a href="../habitacion/">Habitación</a> · <a href="../../precios/">Comparar las 10 ciudades</a></div>"""
    os.makedirs(F(ck, "sueldo-para-alquilar"), exist_ok=True)
    open(F(ck, "sueldo-para-alquilar", "index.html"), "w", encoding="utf-8").write(page(
        f"Cuánto hay que ganar para alquilar en {c['n']} (2026)",
        desc_corta(f"Sueldo neto para alquilar en {c['n']}: piso medio ≈ {fmt(rc)} €/mes (ganar ≈ {fmt(sc)} €), habitación ≈ {fmt(hab)} € (≈ {fmt(sh)} €).", " Por distritos."),
        f"{ck}/sueldo-para-alquilar/", body, [("Vivible", "../../"), (c["n"], "../"), ("Sueldo para alquilar", None)], sq_ld))
    urls.append(BASE + f"{ck}/sueldo-para-alquilar/")

# ---------- habitación por ciudad (<ciudad>/habitacion/): «precio habitación en <ciudad>», «compartir piso o vivir solo»;
# habitación por distrito con hab_d (la misma cifra que la página del distrito) frente a un estudio de 40 m² a precio de m² del distrito
M2E = 40
for ck, c in C.items():
    assert "habitacion" not in [slug(d) for d in c["d"]]
    rows = []
    for d in c["d"]:
        _, r, _, er = dprice(c, d)
        rows.append((d, hab_d(c, r), r * M2E, er))
    rows.sort(key=lambda x: x[1])
    hab, est = c["hab"], c["alquiler"] * M2E
    sh = (hab + GHAB) / ESF
    bar, car = rows[0], rows[-1]
    tr = "".join(f'<tr><td><a href="../{slug(d)}/">{esc(d)}</a></td><td><b>{fmt(h)} €</b></td><td>{fmt(e)} €{"*" if x else ""}</td></tr>' for d, h, e, x in rows)
    nota = '<p class="m">* Alquiler del distrito estimado a partir de su precio de venta: idealista no publica ese dato.</p>' if any(x for *_, x in rows) else ""
    hq_html, hq_ld = faq([
        (f"¿Cuánto cuesta una habitación en {c['n']}?",
         f"De media, unos {fmt(hab)} € al mes en piso compartido ({c['mes']}). Según el distrito, va de unos {fmt(bar[1])} € en {bar[0]} a unos {fmt(car[1])} € en {car[0]} (estimado a partir de lo caro que es el alquiler en cada uno)."),
        (f"¿Cuál es el distrito más barato para alquilar una habitación en {c['n']}?",
         f"{bar[0]}, con habitaciones por unos {fmt(bar[1])} € al mes, {fmt(hab - bar[1])} € menos que la media de {c['n']}."),
        (f"¿Compensa compartir piso o vivir solo en {c['n']}?",
         f"Un estudio de {M2E} m² cuesta de media unos {fmt(est)} € al mes en {c['n']}, frente a {fmt(hab)} € de una habitación: compartir ahorra unos {fmt(est - hab)} € al mes ({fmt((est - hab) * 12)} € al año), "
         "y además los gastos de luz, agua e internet se reparten. Vivir solo da más intimidad; los estudios pequeños suelen costar algo más por m² que la media."),
        (f"¿Cuánto hay que ganar para alquilar una habitación en {c['n']}?",
         f"Con unos {GHAB} € de gastos (luz, agua, internet), lo recomendable es que la habitación no pase del 33 % de lo que ganas: unos {fmt(sh)} € netos al mes. "
         f"Para entrar, cuenta con el primer mes y la fianza que suele pedirse (normalmente un mes): unos {fmt(hab * 2)} €."),
    ])
    body = f"""<h1>Precio de una habitación en {esc(c["n"])} por distritos (2026)</h1>
<p>Alquilar una habitación en piso compartido cuesta de media <b>{fmt(hab)} € al mes</b> en {esc(c["n"])} ({esc(c["mes"])}). En los distritos donde el alquiler es más caro, la habitación también lo es. Esta tabla estima el precio en cada distrito y lo compara con vivir solo en un estudio de {M2E} m².</p>
<div class="g"><div class="k"><small>Habitación en {esc(c["n"])}</small><b>≈ {fmt(hab)} €/mes</b><small>Media de la ciudad</small></div>
<div class="k"><small>Estudio de {M2E} m² para ti solo</small><b>≈ {fmt(est)} €/mes</b><small>{dec(c["alquiler"])} €/m² × {M2E} m²</small></div>
<div class="k"><small>Lo que ahorras compartiendo</small><b>≈ {fmt(est - hab)} €/mes</b><small>≈ {fmt((est - hab) * 12)} € al año</small></div>
<div class="k"><small>Sueldo recomendado</small><b>≈ {fmt(sh)} € netos</b><small>Habitación y gastos ≤ 33 %</small></div></div>
<div class="card"><table class="cmp"><caption class="m" style="text-align:left;padding-bottom:6px">Habitación al mes por distritos, de la más barata a la más cara, frente a un estudio de {M2E} m² en el mismo distrito</caption><tr><th scope="col">Distrito</th><th scope="col">Habitación</th><th scope="col">Estudio {M2E} m²</th></tr>{tr}</table>{nota}
<p class="m">Habitación estimada a partir de la media de {esc(c["n"])} y del alquiler de cada distrito. Precios sin gastos. Cifras orientativas.</p></div>
{hq_html}
<a class="cta" href="../../#c={ck}&op=habitacion">¿Has visto una habitación? Analízala gratis</a>
<div class="card m"><b>Más sobre {esc(c["n"])}:</b> <a href="../">Precios por distritos</a> · <a href="../sueldo-para-alquilar/">Sueldo para alquilar</a> · <a href="../comprar-o-alquilar/">Comprar o alquilar</a> · <a href="../../precios/">Comparar las 10 ciudades</a></div>"""
    os.makedirs(F(ck, "habitacion"), exist_ok=True)
    open(F(ck, "habitacion", "index.html"), "w", encoding="utf-8").write(page(
        f"Precio de una habitación en {c['n']} por distritos (2026)",
        desc_corta(f"Una habitación en {c['n']} cuesta ≈ {fmt(hab)} €/mes: de {fmt(bar[1])} € en {bar[0]} a {fmt(car[1])} € en {car[0]}.", " Compartir o vivir solo."),
        f"{ck}/habitacion/", body, [("Vivible", "../../"), (c["n"], "../"), ("Habitación", None)], hq_ld))
    urls.append(BASE + f"{ck}/habitacion/")

# ---------- comprar o alquilar por ciudad (<ciudad>/comprar-o-alquilar/): hipoteca frente a alquiler y rentabilidad bruta por distrito;
# mismas cifras que gastos de compra (80 %, 30 años, 2,8 %; piso de 70 m²)
TIN, ANOS = .028, 30
def cuota(precio): i = TIN / 12; return precio * .8 * i / (1 - (1 + i) ** -(ANOS * 12))
for ck, c in C.items():
    assert "comprar-o-alquilar" not in [slug(d) for d in c["d"]]
    rows = []
    for d in c["d"]:
        v, r, es, er = dprice(c, d)
        rows.append((d, v * M2A, r * M2A, es or er))
    rows.sort(key=lambda x: -(x[2] * 12 / x[1]))
    med, alq = c["venta"] * M2A, c["alquiler"] * M2A
    cm = cuota(med); ah = gastos(med, c)[2]; rb = alq * 12 / med * 100
    gana = [x for x in rows if cuota(x[1]) < x[2]]
    tr = "".join(f'<tr><td><a href="../{slug(d)}/">{esc(d)}</a></td><td>{fmt(r)} €{"*" if e else ""}</td><td>{fmt(cuota(v))} €</td><td>{dec(r * 12 / v * 100)} %</td></tr>' for d, v, r, e in rows)
    nota = '<p class="m">* Uno de los dos precios del distrito está estimado a partir del otro: idealista no lo publica.</p>' if any(e for *_, e in rows) else ""
    cmp_txt = (f"la hipoteca ({fmt(cm)} €) sale más barata que el alquiler ({fmt(alq)} €)" if cm < alq else f"la hipoteca ({fmt(cm)} €) sale más cara que el alquiler ({fmt(alq)} €)")
    oq_html, oq_ld = faq([
        (f"¿Compensa comprar o alquilar en {c['n']}?",
         f"Para un piso medio de {M2A} m² en {c['n']}, {cmp_txt} al mes, pero comprar exige tener ahorrados unos {fmt(ah)} € (20 % de entrada, impuesto y gastos). "
         "Además, el propietario paga el IBI, la comunidad y las reparaciones. Comprar suele compensar si piensas quedarte muchos años y tienes ese ahorro."),
        (f"¿En qué distritos de {c['n']} la hipoteca es más barata que el alquiler?",
         ((f"En todos ({len(rows)}): " if len(gana) == len(rows) else f"En {len(gana)} de {len(rows)}: ") + ", ".join(x[0] for x in gana) + "." if gana else f"En ninguno: con un 2,8 % a {ANOS} años, la hipoteca del 80 % sale más cara que el alquiler en todos los distritos.")
         + f" Cálculo para un piso de {M2A} m² con hipoteca del 80 % a {ANOS} años al 2,8 %."),
        (f"¿Dónde es más rentable comprar para alquilar en {c['n']}?",
         f"Por rentabilidad bruta (alquiler de un año entre el precio de compra), en {rows[0][0]} ({dec(rows[0][2] * 12 / rows[0][1] * 100)} %) y la más baja en {rows[-1][0]} ({dec(rows[-1][2] * 12 / rows[-1][1] * 100)} %). "
         f"La media de {c['n']} es del {dec(rb)} %. A esa cifra hay que restarle impuestos, IBI, comunidad, seguros y meses vacío."),
    ])
    body = f"""<h1>¿Comprar o alquilar en {esc(c["n"])}? Hipoteca frente a alquiler (2026)</h1>
<p>Comparamos lo que pagarías al mes por un piso de {M2A} m² en cada distrito de {esc(c["n"])}: de alquiler o de hipoteca (80 % del precio, {ANOS} años, 2,8 %). Con precios medios de {esc(c["mes"])}.</p>
<div class="g"><div class="k"><small>Alquiler del piso medio</small><b>≈ {fmt(alq)} €/mes</b><small>{dec(c["alquiler"])} €/m² × {M2A} m²</small></div>
<div class="k"><small>Hipoteca del piso medio</small><b>≈ {fmt(cm)} €/mes</b><small>Piso de ≈ {fmt(med)} €</small></div>
<div class="k"><small>Ahorro para comprar</small><b>≈ {fmt(ah)} €</b><small>Entrada, impuesto y gastos</small></div>
<div class="k"><small>Rentabilidad bruta media</small><b>{dec(rb)} %</b><small>Alquiler de un año / precio</small></div></div>
<div class="card"><table class="cmp"><caption class="m" style="text-align:left;padding-bottom:6px">Piso de {M2A} m² por distritos, de mayor a menor rentabilidad: alquiler al mes, hipoteca al mes y rentabilidad bruta</caption><tr><th scope="col">Distrito</th><th scope="col">Alquiler</th><th scope="col">Hipoteca</th><th scope="col">Rentab.</th></tr>{tr}</table>{nota}
<p class="m">La hipoteca no incluye seguros, IBI ni comunidad; el alquiler, tampoco gastos. Cifras orientativas, no una recomendación de inversión.</p></div>
{oq_html}
<a class="cta" href="../../#c={ck}">¿Has visto un piso? Analízalo gratis</a>
<div class="card m"><b>Más sobre {esc(c["n"])}:</b> <a href="../">Precios por distritos</a> · <a href="../gastos-de-compra/">Gastos de comprar</a> · <a href="../sueldo-para-alquilar/">Sueldo para alquilar</a></div>"""
    os.makedirs(F(ck, "comprar-o-alquilar"), exist_ok=True)
    open(F(ck, "comprar-o-alquilar", "index.html"), "w", encoding="utf-8").write(page(
        f"¿Comprar o alquilar en {c['n']}? Hipoteca vs alquiler 2026",
        desc_corta(f"Piso medio en {c['n']}: alquiler ≈ {fmt(alq)} €/mes, hipoteca ≈ {fmt(cm)} €/mes y ahorro de {fmt(ah)} € para comprar.", " Por distritos."),
        f"{ck}/comprar-o-alquilar/", body, [("Vivible", "../../"), (c["n"], "../"), ("Comprar o alquilar", None)], oq_ld))
    urls.append(BASE + f"{ck}/comprar-o-alquilar/")

# ---------- comparativa de ciudades (precios/): venta, alquiler, habitación e impuesto de compra
cs = sorted(C.items(), key=lambda kc: -kc[1]["venta"])
tr = "".join(f'<tr><td><a href="../{k}/">{esc(c["n"])}</a></td><td>{fmt(c["venta"])} €</td><td>{dec(c["alquiler"])} €</td><td>{fmt(c["hab"])} €</td><td>{str(c["itp"]).replace(".", ",")} %</td></tr>' for k, c in cs)
car, bar = cs[0][1], cs[-1][1]
hb = min(C.values(), key=lambda c: c["hab"]); hc = max(C.values(), key=lambda c: c["hab"])
q_html, q_ld = faq([
    ("¿Cuál es la ciudad más cara para comprar piso?",
     f"De estas 10, {car['n']}: {fmt(car['venta'])} €/m² de media, unos {fmt(car['venta'] * 70)} € por un piso de 70 m². La más barata es {bar['n']}, con {fmt(bar['venta'])} €/m² (unos {fmt(bar['venta'] * 70)} €)."),
    ("¿Dónde es más barato alquilar una habitación?",
     f"En {hb['n']}, por unos {fmt(hb['hab'])} € al mes de media. La más cara es {hc['n']}, con unos {fmt(hc['hab'])} € al mes."),
    ("¿Qué impuesto se paga al comprar un piso de segunda mano?",
     "El impuesto de transmisiones patrimoniales (ITP), que fija cada comunidad: " + ", ".join(f"{cc} {str(t).replace('.', ',')} %" for cc, t in sorted({c["ccaa"]: c["itp"] for c in C.values()}.items(), key=lambda x: x[1])) + " (tipo general; hay rebajas para jóvenes y familias en algunas comunidades)."),
])
body = f"""<h1>Precio de la vivienda en 10 ciudades de España ({esc(mes_txt)})</h1>
<p>Comprar, alquilar o compartir piso no cuesta lo mismo en {esc(car["n"])} que en {esc(bar["n"])}. Esta tabla compara el precio medio de las 10 ciudades de Vivible, de la más cara a la más barata para comprar.</p>
<div class="card"><table class="cmp"><caption class="m" style="text-align:left;padding-bottom:6px">Precio medio: venta y alquiler por m², habitación al mes e impuesto de compra de segunda mano</caption><tr><th scope="col">Ciudad</th><th scope="col">Venta m²</th><th scope="col">Alquiler m²</th><th scope="col">Habitación</th><th scope="col">ITP</th></tr>{tr}</table></div>
{q_html}
<a class="cta" href="../">Analiza un piso concreto gratis</a>"""
os.makedirs(F("precios"), exist_ok=True)
open(F("precios", "index.html"), "w", encoding="utf-8").write(page(
    "Precio de la vivienda por ciudad (2026): compra, alquiler y habitación",
    desc_corta(f"Compara el precio medio de compra, alquiler y habitación en {', '.join(c['n'] for c in list(C.values())[:-1])} y {list(C.values())[-1]['n']}.", " Y el impuesto de compra de cada comunidad."),
    "precios/", body, [("Vivible", "../"), ("Precios por ciudad", None)], q_ld))
urls.insert(1, BASE + "precios/")

# ---------- 404: GitHub Pages la sirve en cualquier ruta que no exista (enlaces absolutos; fuera del sitemap)
ciud = " · ".join(f'<a href="{BASE}{k}/">{esc(c["n"])}</a>' for k, c in C.items())
open(F("404.html"), "w", encoding="utf-8").write(f"""<!DOCTYPE html><html lang="es"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Página no encontrada | Vivible</title><meta name="robots" content="noindex"><link rel="icon" href="{FAV}"><meta name="theme-color" content="#1f6f54">
<style>{CSS}</style></head><body><div class="w"><main><h1>Esta página no existe</h1>
<p>Puede que el enlace esté mal copiado o que la página haya cambiado de dirección.</p>
<a class="cta" href="{BASE}">Analiza un piso gratis</a>
<div class="card m" style="margin-top:20px"><b>Precios por ciudad:</b> {ciud} · <a href="{BASE}precios/">Comparar las 10</a></div></main></div></body></html>""")

open(F("sitemap.xml"), "w").write('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' +
    "".join(f"<url><loc>{u}</loc><lastmod>{P['actualizado']}</lastmod></url>\n" for u in urls) + "</urlset>\n")
open(F("robots.txt"), "w").write(f"User-agent: *\nAllow: /\nSitemap: {BASE}sitemap.xml\n")
print(len(urls), "páginas")
