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

# barrios administrativos de Madrid por distrito (de data.json; Vicálvaro y Villa de Vallecas vienen agrupados allí, aquí van los oficiales)
BARRIOS = {}
for _b in json.loads(MAD)["barrios"]:
    BARRIOS.setdefault(_b["d"], []).append({"Fuentelareina": "Fuentelarreina"}.get(_b["n"], _b["n"]))
BARRIOS["Vicálvaro"] = ["Casco Histórico de Vicálvaro", "Valdebernardo", "Valderrivas", "El Cañaveral"]
BARRIOS["Villa de Vallecas"] = ["Casco Histórico de Vallecas", "Santa Eugenia", "Ensanche de Vallecas"]
assert sum(map(len, BARRIOS.values())) == 131 and set(BARRIOS) == set(C["madrid"]["d"]), "barrios de Madrid: faltan o sobran"
# los 73 barrios oficiales de Barcelona (Ajuntament de Barcelona, división de 2006), por distrito
BARRIOS_BCN = {
    "Ciutat Vella": ["El Raval", "Barri Gòtic", "La Barceloneta", "Sant Pere, Santa Caterina i la Ribera"],
    "Eixample": ["Fort Pienc", "Sagrada Família", "Dreta de l'Eixample", "Antiga Esquerra de l'Eixample", "Nova Esquerra de l'Eixample", "Sant Antoni"],
    "Sants-Montjuïc": ["El Poble-sec", "La Marina del Prat Vermell", "La Marina de Port", "La Font de la Guatlla", "Hostafrancs", "La Bordeta", "Sants-Badal", "Sants"],
    "Les Corts": ["Les Corts", "La Maternitat i Sant Ramon", "Pedralbes"],
    "Sarrià-Sant Gervasi": ["Vallvidrera, el Tibidabo i les Planes", "Sarrià", "Les Tres Torres", "Sant Gervasi-la Bonanova", "Sant Gervasi-Galvany", "El Putxet i el Farró"],
    "Gràcia": ["Vallcarca i els Penitents", "El Coll", "La Salut", "Vila de Gràcia", "Camp d'en Grassot i Gràcia Nova"],
    "Horta-Guinardó": ["El Baix Guinardó", "Can Baró", "El Guinardó", "La Font d'en Fargues", "El Carmel", "La Teixonera", "Sant Genís dels Agudells", "Montbau", "La Vall d'Hebron", "La Clota", "Horta"],
    "Nou Barris": ["Vilapicina i la Torre Llobeta", "Porta", "El Turó de la Peira", "Can Peguera", "La Guineueta", "Canyelles", "Les Roquetes", "Verdun", "La Prosperitat", "La Trinitat Nova", "Torre Baró", "Ciutat Meridiana", "Vallbona"],
    "Sant Andreu": ["La Trinitat Vella", "Baró de Viver", "El Bon Pastor", "Sant Andreu", "La Sagrera", "El Congrés i els Indians", "Navas"],
    "Sant Martí": ["El Camp de l'Arpa del Clot", "El Clot", "El Parc i la Llacuna del Poblenou", "La Vila Olímpica del Poblenou", "El Poblenou", "Diagonal Mar i el Front Marítim del Poblenou", "El Besòs i el Maresme", "Provençals del Poblenou", "Sant Martí de Provençals", "La Verneda i la Pau"],
}
assert sum(map(len, BARRIOS_BCN.values())) == 73 and set(BARRIOS_BCN) == set(C["barcelona"]["d"]), "barrios de Barcelona: faltan o sobran"
# barrios oficiales de València (Ajuntament, 87 en 19 distritos) de los 16 distritos urbanos que hay en precios.json;
# los «Pobles del Nord / de l'Oest / del Sud» (17 barrios) no tienen página porque idealista no publica su precio
BARRIOS_VLC = {
    "Ciutat Vella": ["La Seu", "La Xerea", "El Carme", "El Pilar", "El Mercat", "Sant Francesc"],
    "L'Eixample": ["Russafa", "El Pla del Remei", "Gran Via"],
    "Extramurs": ["El Botànic", "La Roqueta", "La Petxina", "Arrancapins"],
    "Campanar": ["Campanar", "Les Tendetes", "El Calvari", "Sant Pau"],
    "La Saïdia": ["Marxalenes", "Morvedre", "Trinitat", "Tormos", "Sant Antoni"],
    "El Pla del Real": ["Exposició", "Mestalla", "Jaume Roig", "Ciutat Universitària"],
    "L'Olivereta": ["Nou Moles", "Soternes", "Tres Forques", "La Fontsanta", "La Llum"],
    "Patraix": ["Patraix", "Sant Isidre", "Vara de Quart", "Safranar", "Favara"],
    "Jesús": ["La Raiosa", "L'Hort de Senabre", "La Creu Coberta", "Sant Marcel·lí", "Camí Reial"],
    "Quatre Carreres": ["Montolivet", "En Corts", "Malilla", "La Font de Sant Lluís", "Na Rovella", "La Punta", "Ciutat de les Arts i de les Ciències"],
    "Poblats Marítims": ["El Grau", "El Cabanyal-El Canyamelar", "La Malva-rosa", "Beteró", "Natzaret"],
    "Camins al Grau": ["Aiora", "Albors", "La Creu del Grau", "Camí Fondo", "Penya-roja"],
    "Algirós": ["L'Illa Perduda", "Ciutat Jardí", "L'Amistat", "La Bega Baixa", "La Carrasca"],
    "Benimaclet": ["Benimaclet", "Camí de Vera"],
    "Rascanya": ["Orriols", "Torrefiel", "Sant Llorenç"],
    "Benicalap": ["Benicalap", "Ciutat Fallera"],
}
assert sum(map(len, BARRIOS_VLC.values())) == 70 and set(BARRIOS_VLC) == set(C["valencia"]["d"]), "barrios de València: faltan o sobran"
BAR = {"madrid": BARRIOS, "barcelona": BARRIOS_BCN, "valencia": BARRIOS_VLC}  # ciudades con barrios oficiales en la web
# comparar dos ciudades (comparar/<a>-o-<b>/): el orden de los nombres es el de precios.json, así hay una sola página por pareja
def par(a, b):
    ks = list(C); a, b = sorted((a, b), key=ks.index); return f"{a}-o-{b}"
def coma(xs): return any("," in re.sub(r"\(.*?\)", "", x) for x in xs)  # algún nombre lleva coma («Sant Pere, Santa Caterina i la Ribera»)
def y_lista(xs):  # con «;» si algún nombre lleva coma
    sep = "; " if coma(xs) else ", "
    return xs[0] if len(xs) == 1 else sep.join(xs[:-1]) + " y " + xs[-1]

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
    links = "".join(f'<a href="{pre}{k}/">Vivir en {esc(c["n"])}</a>' for k, c in C.items()) + f'<a href="{pre}precios/">Comparar ciudades</a><a href="{pre}sueldo/">Qué piso puedo pagar</a><a href="{pre}hipoteca/">Cuota de la hipoteca</a><a href="{pre}gastos-de-alquiler/">Dinero para alquilar</a><a href="{pre}gastos-de-compra/">Gastos de comprar</a>'
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
<div class="card m"><b>¿Vas a comprar?</b> <a href="venta/">Precio de la vivienda en {esc(c["n"])} por tamaño</a> · <a href="gastos-de-compra/">Gastos e impuestos de comprar un piso en {esc(c["n"])}</a> · <a href="sueldo-para-comprar/">Cuánto hay que ganar para comprar</a></div>
<div class="card m"><b>¿Vas a alquilar?</b> <a href="alquiler/">Precio del alquiler en {esc(c["n"])} por distritos</a> · <a href="sueldo-para-alquilar/">Cuánto hay que ganar para alquilar en {esc(c["n"])}</a></div>
<div class="card m"><b>¿Buscas habitación?</b> <a href="habitacion/">Precio de una habitación en {esc(c["n"])} por distritos</a></div>
<div class="card m"><b>¿Dudas?</b> <a href="comprar-o-alquilar/">Comprar o alquilar en {esc(c["n"])}: hipoteca frente a alquiler</a></div>
<div class="card m"><b>Otras ciudades:</b> {" · ".join(f'<a href="../{k2}/">{esc(c2["n"])}</a>' for k2, c2 in C.items() if k2 != ck)} · <a href="../precios/">Comparar las 10 ciudades</a></div>
<div class="card m"><b>¿Dudas entre {esc(c["n"])} y otra ciudad?</b> {" · ".join(f'<a href="../comparar/{par(ck, k2)}/">{esc(c["n"])} o {esc(c2["n"])}</a>' for k2, c2 in C.items() if k2 != ck)}</div>"""
    if ck in BAR:  # «en qué distrito está <barrio>»: muchos anuncios dicen el barrio y no el distrito
        BB = BAR[ck]
        body = body.replace("\n" + fq_html, "\n" + f'<div class="card"><h2 style="font:700 21px/1.2 Fraunces,Georgia,serif;margin:0 0 4px">Barrios de {esc(c["n"])} por distrito</h2><p class="m" style="margin:0 0 6px">Los anuncios suelen decir el barrio: búscalo aquí para saber en qué distrito está, o usa el <a href="../barrios/">buscador de barrios</a>.</p><table>'
            + "".join(f'<tr><td><a href="{slug(d)}/">{esc(d)}</a></td><td style="text-align:left">{esc(("; " if coma(BB[d]) else ", ").join(BB[d]))}</td></tr>' for d, *_ in rows) + "</table></div>\n" + fq_html, 1)
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
        ] + ([(f"¿Qué barrios hay en {d}?", f"{d} tiene {len(BAR[ck][d])} barrios: {y_lista(BAR[ck][d])}.")] if ck in BAR else []))
        bar_html = ""
        if ck in BAR:
            bs = BAR[ck][d]
            bar_html = f'<div class="card"><b>Barrios de {esc(d)}</b><p>{esc(d)} tiene {len(bs)} barrios: {esc(y_lista(bs))}. Si el anuncio dice uno de ellos, el piso está en este distrito.</p></div>\n'
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
{bar_html}{dq_html}
<a class="cta" href="../../#c={ck}&d={quote(d)}">¿Tienes un piso en {esc(d)}? Analízalo gratis</a>
<div class="card m"><b>¿Vas a comprar?</b> <a href="../venta/">Precio de la vivienda por tamaño</a> · <a href="../gastos-de-compra/">Gastos e impuestos de comprar un piso en {esc(c["n"])}</a> · <a href="../sueldo-para-comprar/">Cuánto hay que ganar para comprar</a></div>
<div class="card m"><b>¿Vas a alquilar?</b> <a href="../alquiler/">Precio del alquiler en {esc(c["n"])}</a> · <a href="../sueldo-para-alquilar/">Cuánto hay que ganar para alquilar en {esc(c["n"])}</a></div>
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
<div class="card m"><b>Precios en {esc(c["n"])}:</b> <a href="../">Por distritos</a> · <a href="../venta/">Precio por tamaño</a> · <a href="../sueldo-para-comprar/">Sueldo para comprar</a> · <a href="../sueldo-para-alquilar/">Sueldo para alquilar</a> · <a href="../../hipoteca/">Cuota de la hipoteca</a> · <a href="../../gastos-de-compra/">Calculadora de gastos</a> · <a href="../../precios/">Comparar las 10 ciudades</a></div>"""
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
<div class="card m"><b>Más sobre {esc(c["n"])}:</b> <a href="../">Precios por distritos</a> · <a href="../alquiler/">Alquiler por tamaño</a> · <a href="../gastos-de-compra/">Gastos de comprar</a> · <a href="../comprar-o-alquilar/">Comprar o alquilar</a> · <a href="../habitacion/">Habitación</a> · <a href="../../gastos-de-alquiler/">Dinero para entrar de alquiler</a> · <a href="../../sueldo/">Qué piso puedo pagar con mi sueldo</a> · <a href="../../hipoteca/">Cuota de la hipoteca</a> · <a href="../../precios/">Comparar las 10 ciudades</a></div>"""
    os.makedirs(F(ck, "sueldo-para-alquilar"), exist_ok=True)
    open(F(ck, "sueldo-para-alquilar", "index.html"), "w", encoding="utf-8").write(page(
        f"Cuánto hay que ganar para alquilar en {c['n']} (2026)",
        desc_corta(f"Sueldo neto para alquilar en {c['n']}: piso medio ≈ {fmt(rc)} €/mes (ganar ≈ {fmt(sc)} €), habitación ≈ {fmt(hab)} € (≈ {fmt(sh)} €).", " Por distritos."),
        f"{ck}/sueldo-para-alquilar/", body, [("Vivible", "../../"), (c["n"], "../"), ("Sueldo para alquilar", None)], sq_ld))
    urls.append(BASE + f"{ck}/sueldo-para-alquilar/")

# ---------- precio del alquiler por ciudad (<ciudad>/alquiler/): «precio alquiler <ciudad>», «alquiler piso 2 habitaciones <ciudad>»;
# alquiler al mes de un estudio (40 m²), un piso de 2 dormitorios (70 m², el mismo de las otras guías) y uno de 3 (90 m²) con el €/m² de cada distrito
TAM = [(40, "Estudio o 1 dormitorio"), (M2A, "2 dormitorios"), (90, "3 dormitorios")]
for ck, c in C.items():
    assert "alquiler" not in [slug(d) for d in c["d"]]
    rows = sorted(((d, dprice(c, d)[1], dprice(c, d)[3]) for d in c["d"]), key=lambda x: x[1])
    r = c["alquiler"]
    bar, car = rows[0], rows[-1]
    est = lambda e: " (estimado)" if e else ""
    tr = "".join(f'<tr><td><a href="../{slug(d)}/">{esc(d)}</a></td>' + "".join(f"<td>{fmt(m * x)} €{'*' if e else ''}</td>" for m, _ in TAM) + "</tr>" for d, x, e in rows)
    nota = '<p class="m">* Alquiler estimado a partir del precio de venta del distrito: idealista no publica ese dato.</p>' if any(e for *_, e in rows) else ""
    aq_html, aq_ld = faq([
        (f"¿Cuánto cuesta alquilar un piso en {c['n']}?",
         f"De media, {dec(r)} € por m² al mes ({c['mes']}): unos {fmt(r * 40)} € un estudio de 40 m², unos {fmt(r * M2A)} € un piso de 2 dormitorios ({M2A} m²) y unos {fmt(r * 90)} € uno de 3 dormitorios (90 m²)."),
        (f"¿Cuál es el distrito más barato para alquilar en {c['n']}?",
         f"{bar[0]}{est(bar[2])}: {dec(bar[1])} €/m² al mes, unos {fmt(bar[1] * M2A)} € por un piso de {M2A} m². El más caro es {car[0]}{est(car[2])}, con {dec(car[1])} €/m² (unos {fmt(car[1] * M2A)} €)."),
        (f"¿Cuánto cuesta alquilar un piso de 2 habitaciones en {c['n']}?",
         f"Un piso de 2 dormitorios suele tener unos {M2A} m²: cuesta unos {fmt(r * M2A)} € al mes de media, entre {fmt(bar[1] * M2A)} € en {bar[0]} y {fmt(car[1] * M2A)} € en {car[0]}. "
         f"Para pagarlo sin apuros conviene ganar unos {fmt(r * M2A / ESF)} € netos al mes."),
        (f"¿Sale más barato compartir piso en {c['n']}?",
         f"Sí: una habitación cuesta de media unos {fmt(c['hab'])} € al mes, frente a unos {fmt(r * 40)} € de un estudio de 40 m². Eso sí, compartes cocina, baño y salón."),
    ])
    body = f"""<h1>Precio del alquiler en {esc(c["n"])} por distritos (2026)</h1>
<p>Alquilar en {esc(c["n"])} cuesta de media <b>{dec(r)} € por m² al mes</b> ({esc(c["mes"])}). Esto es lo que se paga al mes en cada distrito según el tamaño del piso, del distrito más barato al más caro.</p>
<div class="g">""" + "".join(f'<div class="k"><small>{t} ({m} m²)</small><b>≈ {fmt(r * m)} €/mes</b><small>De {fmt(bar[1] * m)} € a {fmt(car[1] * m)} € según el distrito</small></div>' for m, t in TAM) + f"""
<div class="k"><small>Habitación en piso compartido</small><b>≈ {fmt(c["hab"])} €/mes</b><small><a href="../habitacion/">Por distritos</a></small></div></div>
<div class="card"><table class="cmp"><caption class="m" style="text-align:left;padding-bottom:6px">Alquiler al mes en {esc(c["n"])} por distritos, del más barato al más caro: estudio (40 m²), 2 dormitorios ({M2A} m²) y 3 dormitorios (90 m²)</caption><tr><th scope="col">Distrito</th><th scope="col">40 m²</th><th scope="col">{M2A} m²</th><th scope="col">90 m²</th></tr>{tr}</table>{nota}
<p class="m">Precio medio por m² de cada distrito multiplicado por los metros. Un piso concreto puede costar más o menos según su estado, planta y calle.</p></div>
{aq_html}
<a class="cta" href="../../#c={ck}&op=alquiler">¿Has visto un piso de alquiler? Comprueba si su precio es justo</a>
<div class="card m"><b>Más sobre {esc(c["n"])}:</b> <a href="../">Precios por distritos</a> · <a href="../venta/">Precio de compra</a> · <a href="../sueldo-para-alquilar/">Sueldo para alquilar</a> · <a href="../habitacion/">Habitación</a> · <a href="../comprar-o-alquilar/">Comprar o alquilar</a> · <a href="../../barrios-baratos/">Barrios más baratos de España</a> · <a href="../../barrios-caros/">Barrios más caros</a> · <a href="../../precios/">Comparar las 10 ciudades</a></div>"""
    os.makedirs(F(ck, "alquiler"), exist_ok=True)
    open(F(ck, "alquiler", "index.html"), "w", encoding="utf-8").write(page(
        f"Precio del alquiler en {c['n']} por distritos (2026)",
        desc_corta(f"Alquiler en {c['n']}: {dec(r)} €/m² al mes. Estudio ≈ {fmt(r * 40)} €, 2 dormitorios ≈ {fmt(r * M2A)} € y 3 ≈ {fmt(r * 90)} €.", " Por distritos, del más barato al más caro."),
        f"{ck}/alquiler/", body, [("Vivible", "../../"), (c["n"], "../"), ("Alquiler", None)], aq_ld))
    urls.append(BASE + f"{ck}/alquiler/")

# ---------- precio de venta por ciudad (<ciudad>/venta/): «precio vivienda <ciudad> por distritos», «cuánto cuesta un piso en <ciudad>»;
# precio de un estudio (40 m²), un piso de 2 dormitorios (70 m²) y uno de 3 (90 m²) con el €/m² de venta de cada distrito; gastos con gastos()
for ck, c in C.items():
    assert "venta" not in [slug(d) for d in c["d"]]
    rows = sorted(((d, dprice(c, d)[0], dprice(c, d)[2]) for d in c["d"]), key=lambda x: x[1])
    v = c["venta"]
    bar, car = rows[0], rows[-1]
    est = lambda e: " (estimado)" if e else ""
    tr = "".join(f'<tr><td><a href="../{slug(d)}/">{esc(d)}</a></td>' + "".join(f"<td>{fmt(m * x)} €{'*' if e else ''}</td>" for m, _ in TAM) + "</tr>" for d, x, e in rows)
    nota = '<p class="m">* Precio de venta estimado a partir del alquiler del distrito: idealista no publica ese dato.</p>' if any(e for *_, e in rows) else ""
    med = v * M2A
    imp, otros, tot = gastos(med, c)
    vq_html, vq_ld = faq([
        (f"¿Cuánto cuesta un piso en {c['n']}?",
         f"De media, {fmt(v)} € por m² ({c['mes']}): unos {fmt(v * 40)} € un estudio de 40 m², unos {fmt(med)} € un piso de 2 dormitorios ({M2A} m²) y unos {fmt(v * 90)} € uno de 3 dormitorios (90 m²)."),
        (f"¿Cuál es el distrito más barato para comprar en {c['n']}?",
         f"{bar[0]}{est(bar[2])}: {fmt(bar[1])} €/m², unos {fmt(bar[1] * M2A)} € por un piso de {M2A} m². El más caro es {car[0]}{est(car[2])}, con {fmt(car[1])} €/m² (unos {fmt(car[1] * M2A)} €)."),
        (f"¿Cuánto cuesta un piso de 2 habitaciones en {c['n']}?",
         f"Un piso de 2 dormitorios suele tener unos {M2A} m²: cuesta unos {fmt(med)} € de media, entre {fmt(bar[1] * M2A)} € en {bar[0]} y {fmt(car[1] * M2A)} € en {car[0]}."),
        (f"¿Cuánto dinero hay que tener ahorrado para comprar un piso en {c['n']}?",
         f"Para el piso medio de {M2A} m² ({fmt(med)} €), unos {fmt(tot)} €: el 20 % de entrada ({fmt(med * .2)} €), el {pct(c['itp'])} % de impuesto de compra de segunda mano {en_ccaa(c['ccaa'])} ({fmt(imp)} €) "
         f"y unos {fmt(otros)} € de notaría, registro, gestoría y tasación."),
    ])
    body = f"""<h1>Precio de la vivienda en {esc(c["n"])} por distritos (2026)</h1>
<p>Comprar un piso en {esc(c["n"])} cuesta de media <b>{fmt(v)} € por m²</b> ({esc(c["mes"])}). Esto es lo que cuesta en cada distrito según el tamaño del piso, del distrito más barato al más caro.</p>
<div class="g">""" + "".join(f'<div class="k"><small>{t} ({m} m²)</small><b>≈ {fmt(v * m)} €</b><small>De {fmt(bar[1] * m)} € a {fmt(car[1] * m)} € según el distrito</small></div>' for m, t in TAM) + f"""
<div class="k"><small>Ahorros para el piso de {M2A} m²</small><b>≈ {fmt(tot)} €</b><small><a href="../gastos-de-compra/">Entrada, impuesto y gastos</a></small></div></div>
<div class="card"><table class="cmp"><caption class="m" style="text-align:left;padding-bottom:6px">Precio de compra en {esc(c["n"])} por distritos, del más barato al más caro: estudio (40 m²), 2 dormitorios ({M2A} m²) y 3 dormitorios (90 m²)</caption><tr><th scope="col">Distrito</th><th scope="col">40 m²</th><th scope="col">{M2A} m²</th><th scope="col">90 m²</th></tr>{tr}</table>{nota}
<p class="m">Precio medio por m² de cada distrito multiplicado por los metros. Un piso concreto puede costar más o menos según su estado, planta y calle.</p></div>
{vq_html}
<a class="cta" href="../../#c={ck}&op=venta">¿Has visto un piso en venta? Comprueba si su precio es justo</a>
<div class="card m"><b>Más sobre {esc(c["n"])}:</b> <a href="../">Precios por distritos</a> · <a href="../gastos-de-compra/">Gastos de comprar</a> · <a href="../sueldo-para-comprar/">Sueldo para comprar</a> · <a href="../comprar-o-alquilar/">Comprar o alquilar</a> · <a href="../alquiler/">Alquiler por tamaño</a> · <a href="../../barrios-baratos/">Barrios más baratos de España</a> · <a href="../../barrios-caros/">Barrios más caros</a> · <a href="../../precios/">Comparar las 10 ciudades</a></div>"""
    os.makedirs(F(ck, "venta"), exist_ok=True)
    open(F(ck, "venta", "index.html"), "w", encoding="utf-8").write(page(
        f"Precio de la vivienda en {c['n']} por distritos (2026)",
        desc_corta(f"Comprar en {c['n']}: {fmt(v)} €/m². Estudio ≈ {fmt(v * 40)} €, 2 dormitorios ≈ {fmt(med)} € y 3 ≈ {fmt(v * 90)} €.", " Por distritos, del más barato al más caro."),
        f"{ck}/venta/", body, [("Vivible", "../../"), (c["n"], "../"), ("Venta", None)], vq_ld))
    urls.append(BASE + f"{ck}/venta/")

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
<div class="card m"><b>Más sobre {esc(c["n"])}:</b> <a href="../">Precios por distritos</a> · <a href="../venta/">Precio de compra</a> · <a href="../gastos-de-compra/">Gastos de comprar</a> · <a href="../sueldo-para-comprar/">Sueldo para comprar</a> · <a href="../sueldo-para-alquilar/">Sueldo para alquilar</a> · <a href="../../hipoteca/">Cuota de la hipoteca</a> · <a href="../../rentabilidad/">Rentabilidad del alquiler en 10 ciudades</a></div>"""
    os.makedirs(F(ck, "comprar-o-alquilar"), exist_ok=True)
    open(F(ck, "comprar-o-alquilar", "index.html"), "w", encoding="utf-8").write(page(
        f"¿Comprar o alquilar en {c['n']}? Hipoteca vs alquiler 2026",
        desc_corta(f"Piso medio en {c['n']}: alquiler ≈ {fmt(alq)} €/mes, hipoteca ≈ {fmt(cm)} €/mes y ahorro de {fmt(ah)} € para comprar.", " Por distritos."),
        f"{ck}/comprar-o-alquilar/", body, [("Vivible", "../../"), (c["n"], "../"), ("Comprar o alquilar", None)], oq_ld))
    urls.append(BASE + f"{ck}/comprar-o-alquilar/")

# ---------- sueldo para comprar por ciudad (<ciudad>/sueldo-para-comprar/): «cuánto hay que ganar para comprar un piso en <ciudad>»;
# la cuota (80 %, 30 años, 2,8 %, como en comprar o alquilar) no debe pasar del 30 % de los ingresos netos; muchos bancos llegan al 35 %
ESC, ESC2 = .30, .35
for ck, c in C.items():
    assert "sueldo-para-comprar" not in [slug(d) for d in c["d"]]
    rows = sorted(((d, dprice(c, d)[0] * M2A, dprice(c, d)[2]) for d in c["d"]), key=lambda x: x[1])
    med = c["venta"] * M2A
    cm, ah = cuota(med), gastos(med, c)[2]
    sc, sc2 = cm / ESC, cm / ESC2
    anos = ah / (sc * .2 * 12)
    bar, car = rows[0], rows[-1]
    tr = "".join(f'<tr><td><a href="../{slug(d)}/">{esc(d)}</a></td><td>{fmt(v)} €{"*" if e else ""}</td><td>{fmt(gastos(v, c)[2])} €</td><td><b>{fmt(cuota(v) / ESC)} €</b></td></tr>' for d, v, e in rows)
    nota = '<p class="m">* Precio de venta estimado a partir del alquiler del distrito: idealista no publica ese dato.</p>' if any(e for *_, e in rows) else ""
    pq_html, pq_ld = faq([
        (f"¿Cuánto hay que ganar para comprar un piso en {c['n']}?",
         f"Un piso medio de {M2A} m² en {c['n']} cuesta unos {fmt(med)} € ({fmt(c['venta'])} €/m², {c['mes']}). Con una hipoteca del 80 % a {ANOS} años al 2,8 %, la cuota ronda los {fmt(cm)} € al mes. "
         f"Para que no pase del 30 % de lo que ganas, necesitas unos {fmt(sc)} € netos al mes (unos {fmt(sc2)} € si el banco acepta el 35 %). Entre dos, unos {fmt(sc / 2)} € netos cada uno."),
        (f"¿Cuántos ahorros necesito para comprar en {c['n']}?",
         f"Para el piso medio, unos {fmt(ah)} €: el 20 % de entrada que no financia el banco, el impuesto de compra ({pct(c['itp'])} % de ITP {en_ccaa(c['ccaa'])} si es de segunda mano), notaría, registro, gestoría y tasación. "
         f"Ahorrando el 20 % de un sueldo de {fmt(sc)} €, tardarías unos {dec(anos, 0) if anos >= 10 else dec(anos)} años en juntarlo."),
        (f"¿En qué distrito de {c['n']} se necesita ganar menos para comprar?",
         f"En {bar[0]}: un piso de {M2A} m² cuesta unos {fmt(bar[1])} € y basta con ganar unos {fmt(cuota(bar[1]) / ESC)} € netos al mes. "
         f"En {car[0]}, el más caro, harían falta unos {fmt(cuota(car[1]) / ESC)} € netos ({fmt(car[1])} € el piso)."),
        ("¿Cuánto me presta el banco?",
         "Normalmente hasta el 80 % del precio de compra o del valor de tasación (el menor de los dos), y siempre que la cuota no pase del 30–35 % de tus ingresos netos. "
         "Para la primera vivienda de jóvenes hay avales públicos que permiten financiar hasta el 95 %: pregúntalo en tu banco o en tu comunidad."),
    ])
    body = f"""<h1>¿Cuánto hay que ganar para comprar un piso en {esc(c["n"])}? (2026)</h1>
<p>Para darte una hipoteca, el banco mira dos cosas: que tengas ahorrado el 20 % del precio más los impuestos y gastos, y que la cuota no pase de un 30–35 % de lo que ganas. Con el precio medio de {esc(c["n"])} ({fmt(c["venta"])} €/m², {esc(c["mes"])}), esto es lo que necesitas en cada distrito.</p>
<div class="g"><div class="k"><small>Piso medio de {M2A} m² en {esc(c["n"])}</small><b>≈ {fmt(med)} €</b><small>Hipoteca ≈ {fmt(cm)} €/mes</small></div>
<div class="k"><small>Sueldo neto recomendado</small><b>≈ {fmt(sc)} €/mes</b><small>Cuota ≤ 30 % (≈ {fmt(sc2)} € con el 35 %)</small></div>
<div class="k"><small>Ahorros necesarios</small><b>≈ {fmt(ah)} €</b><small>Entrada, impuesto y gastos</small></div>
<div class="k"><small>Entre dos</small><b>≈ {fmt(sc / 2)} €</b><small>Netos al mes cada uno</small></div></div>
<div class="card"><table class="cmp"><caption class="m" style="text-align:left;padding-bottom:6px">Piso de {M2A} m² de segunda mano por distritos, del más barato al más caro: precio, ahorros necesarios y sueldo neto recomendado (hipoteca del 80 % a {ANOS} años al 2,8 %; cuota ≤ 30 %)</caption><tr><th scope="col">Distrito</th><th scope="col">Precio</th><th scope="col">Ahorros</th><th scope="col">Sueldo neto</th></tr>{tr}</table>{nota}
<p class="m">Cuota sin seguros. Si ya pagas otros préstamos, el banco los suma a la cuota. Cifras orientativas.</p></div>
{pq_html}
<a class="cta" href="../../#c={ck}&op=venta">¿Has visto un piso? Comprueba si te lo puedes permitir</a>
<div class="card m"><b>Más sobre {esc(c["n"])}:</b> <a href="../">Precios por distritos</a> · <a href="../venta/">Precio de compra</a> · <a href="../gastos-de-compra/">Gastos de comprar</a> · <a href="../comprar-o-alquilar/">Comprar o alquilar</a> · <a href="../sueldo-para-alquilar/">Sueldo para alquilar</a> · <a href="../../sueldo/">Qué piso puedo pagar con mi sueldo</a> · <a href="../../hipoteca/">Cuota de la hipoteca</a> · <a href="../../precios/">Comparar las 10 ciudades</a></div>"""
    os.makedirs(F(ck, "sueldo-para-comprar"), exist_ok=True)
    open(F(ck, "sueldo-para-comprar", "index.html"), "w", encoding="utf-8").write(page(
        f"Cuánto hay que ganar para comprar un piso en {c['n']} (2026)",
        desc_corta(f"Sueldo neto para comprar en {c['n']}: piso medio ≈ {fmt(med)} €, hipoteca ≈ {fmt(cm)} €/mes, ganar ≈ {fmt(sc)} € y ahorrar {fmt(ah)} €.", " Por distritos."),
        f"{ck}/sueldo-para-comprar/", body, [("Vivible", "../../"), (c["n"], "../"), ("Sueldo para comprar", None)], pq_ld))
    urls.append(BASE + f"{ck}/sueldo-para-comprar/")

# ---------- comparativa de ciudades (precios/): venta, alquiler, habitación e impuesto de compra
cs = sorted(C.items(), key=lambda kc: -kc[1]["venta"])
tr = "".join(f'<tr><td><a href="../{k}/">{esc(c["n"])}</a></td><td>{fmt(c["venta"])} €</td><td>{dec(c["alquiler"])} €</td><td>{fmt(c["hab"])} €</td><td>{str(c["itp"]).replace(".", ",")} %</td></tr>' for k, c in cs)
car, bar = cs[0][1], cs[-1][1]
hb = min(C.values(), key=lambda c: c["hab"]); hc = max(C.values(), key=lambda c: c["hab"])
# sueldo neto recomendado por ciudad, con las mismas reglas que sus guías (alquiler ≤ 33 %, habitación + gastos ≤ 33 %, cuota ≤ 30 %)
def sueldos(c):
    med = c["venta"] * M2A
    return c["alquiler"] * M2A / ESF, (c["hab"] + GHAB) / ESF, cuota(med) / ESC, gastos(med, c)[2]
ss = sorted(C.items(), key=lambda kc: sueldos(kc[1])[0])
tr2 = "".join(f'<tr><td><a href="../{k}/">{esc(c["n"])}</a></td>' + "".join(f"<td>{fmt(x)} €</td>" for x in sueldos(c)) + "</tr>" for k, c in ss)
sa_b, sa_c = ss[0][1], ss[-1][1]
sc_b = min(C.values(), key=lambda c: sueldos(c)[2]); sc_c = max(C.values(), key=lambda c: sueldos(c)[2])
GUIAS = [("venta", "Venta"), ("alquiler", "Alquiler"), ("gastos-de-compra", "Gastos de compra"), ("sueldo-para-comprar", "Sueldo para comprar"), ("sueldo-para-alquilar", "Sueldo para alquilar"), ("comprar-o-alquilar", "Comprar o alquilar"), ("habitacion", "Habitación")]
guias = "".join(f'<p style="margin:0"><b>{esc(c["n"])}:</b> ' + " · ".join(f'<a href="../{k}/{g}/">{t}</a>' for g, t in GUIAS) + "</p>" for k, c in C.items())
q_html, q_ld = faq([
    ("¿Cuál es la ciudad más cara para comprar piso?",
     f"De estas 10, {car['n']}: {fmt(car['venta'])} €/m² de media, unos {fmt(car['venta'] * 70)} € por un piso de 70 m². La más barata es {bar['n']}, con {fmt(bar['venta'])} €/m² (unos {fmt(bar['venta'] * 70)} €)."),
    ("¿Dónde es más barato alquilar una habitación?",
     f"En {hb['n']}, por unos {fmt(hb['hab'])} € al mes de media. La más cara es {hc['n']}, con unos {fmt(hc['hab'])} € al mes."),
    ("¿Qué impuesto se paga al comprar un piso de segunda mano?",
     "El impuesto de transmisiones patrimoniales (ITP), que fija cada comunidad: " + ", ".join(f"{cc} {str(t).replace('.', ',')} %" for cc, t in sorted({c["ccaa"]: c["itp"] for c in C.values()}.items(), key=lambda x: x[1])) + " (tipo general; hay rebajas para jóvenes y familias en algunas comunidades)."),
    ("¿En qué ciudad hay que ganar menos para alquilar un piso?",
     f"En {sa_b['n']}: para un piso de {M2A} m² basta con unos {fmt(sueldos(sa_b)[0])} € netos al mes (alquiler ≤ 33 % del sueldo). En {sa_c['n']} hacen falta unos {fmt(sueldos(sa_c)[0])} €."),
    ("¿En qué ciudad hay que ganar menos para comprar un piso?",
     f"En {sc_b['n']}: con una hipoteca del 80 % a {ANOS} años al 2,8 %, unos {fmt(sueldos(sc_b)[2])} € netos al mes para un piso de {M2A} m² (cuota ≤ 30 %) y unos {fmt(sueldos(sc_b)[3])} € ahorrados. "
     f"En {sc_c['n']} hacen falta unos {fmt(sueldos(sc_c)[2])} € al mes y {fmt(sueldos(sc_c)[3])} € de ahorros."),
])
body = f"""<h1>Precio de la vivienda en 10 ciudades de España ({esc(mes_txt)})</h1>
<p>Comprar, alquilar o compartir piso no cuesta lo mismo en {esc(car["n"])} que en {esc(bar["n"])}. Esta tabla compara el precio medio de las 10 ciudades de Vivible, de la más cara a la más barata para comprar.</p>
<div class="card"><table class="cmp"><caption class="m" style="text-align:left;padding-bottom:6px">Precio medio: venta y alquiler por m², habitación al mes e impuesto de compra de segunda mano</caption><tr><th scope="col">Ciudad</th><th scope="col">Venta m²</th><th scope="col">Alquiler m²</th><th scope="col">Habitación</th><th scope="col">ITP</th></tr>{tr}</table></div>
<h2 style="font:700 21px/1.2 Fraunces,Georgia,serif;margin:24px 0 0">¿Cuánto hay que ganar en cada ciudad?</h2>
<div class="card"><table class="cmp"><caption class="m" style="text-align:left;padding-bottom:6px">Sueldo neto al mes recomendado para alquilar un piso de {M2A} m² (alquiler ≤ 33 %), una habitación (con gastos, ≤ 33 %) o comprarlo (hipoteca del 80 % a {ANOS} años al 2,8 %, cuota ≤ 30 %), y ahorros para comprar; de la ciudad más barata a la más cara para alquilar</caption><tr><th scope="col">Ciudad</th><th scope="col">Alquilar</th><th scope="col">Habitación</th><th scope="col">Comprar</th><th scope="col">Ahorros</th></tr>{tr2}</table>
<p class="m">Cifras orientativas con precios medios. El detalle por distritos está en la guía de cada ciudad.</p></div>
{q_html}
<a class="cta" href="../">Analiza un piso concreto gratis</a>
<div class="card m"><b>¿Qué piso puedo pagar con mi sueldo?</b> <a href="../sueldo/">Alquiler e hipoteca según lo que ganas</a> · <a href="../hipoteca/">Cuota de la hipoteca</a> · <a href="../gastos-de-alquiler/">Dinero para entrar de alquiler</a> · <a href="../gastos-de-compra/">Calculadora de gastos de compra</a> · <a href="../rentabilidad/">Rentabilidad del alquiler</a> · <a href="../barrios-baratos/">Barrios más baratos</a> · <a href="../barrios-caros/">Barrios más caros</a></div>
<div class="card m"><b>Comparar dos ciudades:</b> <a href="../comparar/">Madrid o Barcelona, Valencia o Málaga… las 45 parejas lado a lado</a></div>
<div class="card m"><b>Guías por ciudad</b>{guias}</div>"""
os.makedirs(F("precios"), exist_ok=True)
open(F("precios", "index.html"), "w", encoding="utf-8").write(page(
    "Precio de la vivienda por ciudad (2026): compra, alquiler y habitación",
    desc_corta(f"Compara el precio medio de compra, alquiler y habitación en {', '.join(c['n'] for c in list(C.values())[:-1])} y {list(C.values())[-1]['n']}.", " Y el impuesto de compra de cada comunidad."),
    "precios/", body, [("Vivible", "../"), ("Precios por ciudad", None)], q_ld))
urls.insert(1, BASE + "precios/")

# ---------- ¿qué piso puedo pagar con mi sueldo? (sueldo/): «cuánto puedo pagar de alquiler si gano 1.500», «qué hipoteca puedo pagar con 2.000 euros»;
# las mismas reglas que las guías (alquiler ≤ 33 %, cuota ≤ 30 %, hipoteca del 80 % a ANOS años al TIN) aplicadas al revés: del sueldo al piso
SUELDOS = [1000, 1200, 1500, 1800, 2000, 2500, 3000]
def precio_max(sueldo):  # precio del piso cuya cuota (80 % financiado) es el 30 % del sueldo
    return sueldo * ESC / cuota(1)
SB = [1200, 1500, 2000, 2500]
tr = "".join(f"<tr><td>{fmt(s)} €</td><td>{fmt(s * ESF)} €</td><td>{fmt(s * ESC)} €</td><td>{fmt(round(precio_max(s), -3))} €</td></tr>" for s in SUELDOS)
ra = sorted(C.items(), key=lambda kc: kc[1]["alquiler"])
tra = "".join(f'<tr><td><a href="../{k}/sueldo-para-alquilar/">{esc(c["n"])}</a></td>' + "".join(f"<td>{fmt(s * ESF / c['alquiler'])} m²</td>" for s in SB) + "</tr>" for k, c in ra)
rv = sorted(C.items(), key=lambda kc: kc[1]["venta"])
trv = "".join(f'<tr><td><a href="../{k}/sueldo-para-comprar/">{esc(c["n"])}</a></td>' + "".join(f"<td>{fmt(precio_max(s) / c['venta'])} m²</td>" for s in SB) + "</tr>" for k, c in rv)
cab = '<tr><th scope="col">Ciudad</th>' + "".join(f'<th scope="col">{fmt(s)} €</th>' for s in SB) + "</tr>"
mb, mc = ra[0][1], ra[-1][1]
bdc = min(((d, dprice(mc, d)[1]) for d in mc["d"]), key=lambda x: x[1])
s15 = 1500
sq_html, sq_ld = faq([
    ("¿Cuánto puedo pagar de alquiler si gano 1.500 € al mes?",
     f"Lo recomendable es que el alquiler no pase del 33 % de lo que ganas: con 1.500 € netos, unos {fmt(1500 * ESF)} € al mes. Con 1.200 €, unos {fmt(1200 * ESF)} €; con 2.000 €, unos {fmt(2000 * ESF)} €."),
    ("¿Qué hipoteca puedo pagar con 2.000 € al mes?",
     f"Si la cuota no pasa del 30 % del sueldo, unos {fmt(2000 * ESC)} € al mes. Con una hipoteca del 80 % a {ANOS} años al 2,8 %, eso da para un piso de unos {fmt(round(precio_max(2000), -3))} €, y harían falta además la entrada del 20 % y los impuestos y gastos de compra."),
    (f"¿Dónde me llega para más metros de alquiler con {fmt(s15)} €?",
     f"De estas 10 ciudades, en {mb['n']}: unos {fmt(s15 * ESF / mb['alquiler'])} m² al precio medio. En {mc['n']}, solo unos {fmt(s15 * ESF / mc['alquiler'])} m². "
     f"Dentro de cada ciudad cambia mucho: en {bdc[0]}, el distrito más barato para alquilar de {mc['n']}, unos {fmt(s15 * ESF / bdc[1])} m²."),
    ("¿Cuánto tengo que ganar para alquilar solo?",
     f"Para un piso de {M2A} m² al precio medio, entre unos {fmt(mb['alquiler'] * M2A / ESF)} € netos al mes en {mb['n']} y unos {fmt(mc['alquiler'] * M2A / ESF)} € en {mc['n']}. Si no llegas, compartir piso sale bastante más barato: cada ciudad tiene su guía de habitaciones."),
])
body = f"""<h1>¿Qué piso puedo pagar con mi sueldo? ({esc(mes_txt)})</h1>
<p>La regla más usada: que el alquiler no pase del 33 % de lo que ganas y la hipoteca, del 30 %. Aquí tienes cuánto da cada sueldo neto y para cuántos metros llega en cada ciudad, con los precios medios de idealista.</p>
<div class="g"><div class="k"><small>Con 1.500 € netos, alquiler de hasta</small><b>≈ {fmt(1500 * ESF)} €/mes</b></div>
<div class="k"><small>Con 2.000 € netos, piso de hasta</small><b>≈ {fmt(round(precio_max(2000), -3))} €</b><small>Hipoteca del 80 %</small></div></div>
<div class="card"><table class="cmp"><caption class="m" style="text-align:left;padding-bottom:6px">Sueldo neto al mes, alquiler máximo (33 %), cuota de hipoteca máxima (30 %) y precio del piso que permite esa cuota (hipoteca del 80 % a {ANOS} años al 2,8 %)</caption><tr><th scope="col">Sueldo</th><th scope="col">Alquiler</th><th scope="col">Cuota</th><th scope="col">Piso</th></tr>{tr}</table>
<p class="m">Para comprar hace falta además ahorrar la entrada (20 %) y el impuesto y los gastos, que cambian según la comunidad: lo tienes en la guía «gastos de compra» de cada ciudad.</p></div>
<h2 style="font:700 21px/1.2 Fraunces,Georgia,serif;margin:24px 0 0">¿Para cuántos metros de alquiler te llega?</h2>
<div class="card"><table class="cmp"><caption class="m" style="text-align:left;padding-bottom:6px">Metros que puedes alquilar al precio medio de cada ciudad según tu sueldo neto (alquiler ≤ 33 %), de la ciudad más barata a la más cara</caption>{cab}{tra}</table></div>
<h2 style="font:700 21px/1.2 Fraunces,Georgia,serif;margin:24px 0 0">¿Para cuántos metros te llega si compras?</h2>
<div class="card"><table class="cmp"><caption class="m" style="text-align:left;padding-bottom:6px">Metros que puedes comprar al precio medio de cada ciudad según tu sueldo neto (cuota ≤ 30 %, hipoteca del 80 % a {ANOS} años al 2,8 %), de la más barata a la más cara</caption>{cab}{trv}</table>
<p class="m">Cifras orientativas con precios medios; dentro de cada ciudad hay distritos mucho más baratos y más caros. El detalle está en la guía de cada ciudad.</p></div>
{sq_html}
<a class="cta" href="../">¿Has visto un piso? Comprueba si te lo puedes permitir</a>
<div class="card m"><b>Más guías:</b> <a href="../hipoteca/">Cuota de la hipoteca</a> · <a href="../precios/">Comparar las 10 ciudades</a> · """ + " · ".join(f'<a href="../{k}/">{esc(c["n"])}</a>' for k, c in C.items()) + """</div>"""
os.makedirs(F("sueldo"), exist_ok=True)
open(F("sueldo", "index.html"), "w", encoding="utf-8").write(page(
    "¿Qué piso puedo pagar con mi sueldo? Alquiler e hipoteca (2026)",
    desc_corta(f"Con 1.500 € netos, alquiler de hasta {fmt(1500 * ESF)} €; con 2.000 €, piso de hasta {fmt(round(precio_max(2000), -3))} €. Metros que te llegan en 10 ciudades.", " Alquiler e hipoteca."),
    "sueldo/", body, [("Vivible", "../"), ("Qué piso puedo pagar", None)], sq_ld))
urls.insert(2, BASE + "sueldo/")

# ---------- cuota de la hipoteca (hipoteca/): «cuota hipoteca 150.000 euros», «cuánto se paga al mes por una hipoteca de 200.000»;
# préstamo francés al TIN y ANOS de las guías (2,8 %, 30 años); los otros tipos y plazos son ejemplos de cálculo, no ofertas de bancos
def cuota_p(prestamo, tin=TIN, anos=ANOS):
    i = tin / 12; return prestamo * i / (1 - (1 + i) ** -(anos * 12))
PRESTAMOS = [100000, 120000, 150000, 180000, 200000, 250000, 300000, 350000, 400000]
PLAZOS = [20, 25, 30]
TIPOS = [.02, .025, .028, .03, .035, .04]
pc = lambda t: dec(t * 100, 1 if round(t * 1000) % 10 else 0)
th1 = '<tr><th scope="col">Hipoteca</th>' + "".join(f'<th scope="col">{a} años</th>' for a in PLAZOS) + "</tr>"
tr1 = "".join(f"<tr><td>{fmt(h)} €</td>" + "".join(f"<td>{fmt(cuota_p(h, anos=a))} €</td>" for a in PLAZOS) + "</tr>" for h in PRESTAMOS)
tr2 = "".join(f"<tr><td>{fmt(h)} €</td><td>{fmt(cuota_p(h) * ANOS * 12 - h)} €</td><td><b>{fmt(cuota_p(h) / ESC)} €</b></td></tr>" for h in PRESTAMOS)
tr3 = "".join(f"<tr><td>{pc(t)} %</td><td>{fmt(cuota_p(100000, t, 25))} €</td><td>{fmt(cuota_p(100000, t, 30))} €</td></tr>" for t in TIPOS)
rc = sorted(C.items(), key=lambda kc: kc[1]["venta"])
tr4 = "".join(f'<tr><td><a href="../{k}/sueldo-para-comprar/">{esc(c["n"])}</a></td><td>{fmt(c["venta"] * M2A)} €</td><td>{fmt(cuota(c["venta"] * M2A))} €</td></tr>' for k, c in rc)
h150, h200 = cuota_p(150000), cuota_p(200000)
i25, i30 = cuota_p(200000, anos=25) * 300 - 200000, cuota_p(200000) * 360 - 200000
hq_html, hq_ld = faq([
    ("¿Cuánto se paga al mes por una hipoteca de 150.000 €?",
     f"A {ANOS} años al 2,8 %, unos {fmt(h150)} € al mes. A 25 años, unos {fmt(cuota_p(150000, anos=25))} €, y a 20 años, unos {fmt(cuota_p(150000, anos=20))} €. La cuota no incluye los seguros que suele pedir el banco."),
    ("¿Cuánto se paga al mes por una hipoteca de 200.000 €?",
     f"A {ANOS} años al 2,8 %, unos {fmt(h200)} € al mes; a 25 años, unos {fmt(cuota_p(200000, anos=25))} €. Si el tipo fuera del 3,5 %, la cuota a {ANOS} años subiría a unos {fmt(cuota_p(200000, .035))} €."),
    ("¿Cuánto hay que ganar para una hipoteca de 200.000 €?",
     f"Si la cuota no debe pasar del 30 % de lo que ganas, unos {fmt(h200 / ESC)} € netos al mes con una hipoteca a {ANOS} años al 2,8 % (unos {fmt(h200 / ESC2)} € si el banco acepta el 35 %). Entre dos, la mitad cada uno."),
    ("¿Es mejor la hipoteca a 25 o a 30 años?",
     f"A {ANOS} años la cuota es más baja, pero pagas más intereses. Con 200.000 € al 2,8 %: a 25 años pagas unos {fmt(cuota_p(200000, anos=25))} € al mes y {fmt(i25)} € de intereses en total; a 30 años, unos {fmt(h200)} € al mes y {fmt(i30)} € de intereses."),
    ("¿Qué no incluye la cuota de la hipoteca?",
     "Los seguros (el de hogar es obligatorio y el banco suele ofrecer el de vida), el IBI y la comunidad. Además, al comprar hay que pagar la entrada (normalmente el 20 %), el impuesto de compra y los gastos de notaría, registro y gestoría."),
])
body = f"""<h1>Cuota de la hipoteca: cuánto pagarás al mes (2026)</h1>
<p>Lo que pagas cada mes depende de cuánto te prestan, a cuántos años y a qué tipo de interés. Aquí tienes la cuota de las hipotecas más comunes, los intereses que pagarás en total y lo que tendrías que ganar. Los cálculos usan un tipo fijo del 2,8 %, el mismo que el resto de guías de Vivible; abajo puedes poner el tuyo.</p>
<div class="g"><div class="k"><small>Hipoteca de 150.000 € a {ANOS} años</small><b>≈ {fmt(h150)} €/mes</b><small>Al 2,8 %</small></div>
<div class="k"><small>Hipoteca de 200.000 € a {ANOS} años</small><b>≈ {fmt(h200)} €/mes</b><small>Ganar ≈ {fmt(h200 / ESC)} € netos</small></div></div>
<div class="card"><form id="calc" onsubmit="return false"><b>Calcula tu cuota</b>
<div class="g" style="margin-top:10px"><label class="m">Lo que te prestan (€)<input id="hq" type="number" inputmode="numeric" min="1000" step="1000" value="150000"></label>
<label class="m">Años<input id="ha" type="number" inputmode="numeric" min="1" max="40" value="{ANOS}"></label>
<label class="m">Tipo de interés (%)<input id="ht" type="number" inputmode="decimal" min="0" max="15" step="0.05" value="2.8"></label>
<div class="k" aria-live="polite"><small>Cuota al mes</small><b id="hr">≈ {fmt(h150)} €</b><small id="hs">Ganar ≈ {fmt(h150 / ESC)} € netos</small></div></div></form></div>
<h2 style="font:700 21px/1.2 Fraunces,Georgia,serif;margin:24px 0 0">Cuota al mes según el plazo</h2>
<div class="card"><table class="cmp"><caption class="m" style="text-align:left;padding-bottom:6px">Cuota mensual de una hipoteca a tipo fijo del 2,8 % según lo que te prestan y los años (sin seguros)</caption>{th1}{tr1}</table></div>
<h2 style="font:700 21px/1.2 Fraunces,Georgia,serif;margin:24px 0 0">Intereses en total y sueldo necesario</h2>
<div class="card"><table class="cmp"><caption class="m" style="text-align:left;padding-bottom:6px">Hipoteca a {ANOS} años al 2,8 %: intereses que pagas en total y sueldo neto al mes para que la cuota no pase del 30 %</caption><tr><th scope="col">Hipoteca</th><th scope="col">Intereses</th><th scope="col">Sueldo neto</th></tr>{tr2}</table></div>
<h2 style="font:700 21px/1.2 Fraunces,Georgia,serif;margin:24px 0 0">Si tu tipo de interés es otro</h2>
<div class="card"><table class="cmp"><caption class="m" style="text-align:left;padding-bottom:6px">Cuota al mes por cada 100.000 € prestados según el tipo de interés (ejemplos de cálculo, no ofertas de bancos)</caption><tr><th scope="col">Tipo</th><th scope="col">25 años</th><th scope="col">30 años</th></tr>{tr3}</table>
<p class="m">Para otra cantidad, multiplica: una hipoteca de 250.000 € paga 2,5 veces la cuota de 100.000 €.</p></div>
<h2 style="font:700 21px/1.2 Fraunces,Georgia,serif;margin:24px 0 0">La hipoteca del piso medio en cada ciudad</h2>
<div class="card"><table class="cmp"><caption class="m" style="text-align:left;padding-bottom:6px">Piso de {M2A} m² al precio medio de cada ciudad ({esc(mes_txt)}) y su cuota con una hipoteca del 80 % a {ANOS} años al 2,8 %</caption><tr><th scope="col">Ciudad</th><th scope="col">Piso</th><th scope="col">Cuota</th></tr>{tr4}</table>
<p class="m">El banco suele prestar hasta el 80 % del precio: el 20 % restante, el impuesto y los gastos los pones tú. Lo tienes por distritos en la guía de cada ciudad.</p></div>
{hq_html}
<a class="cta" href="../">¿Has visto un piso? Comprueba si te lo puedes permitir</a>
<div class="card m"><b>Más guías:</b> <a href="../sueldo/">Qué piso puedo pagar con mi sueldo</a> · <a href="../gastos-de-compra/">Calculadora de gastos de compra</a> · <a href="../precios/">Comparar las 10 ciudades</a> · """ + " · ".join(f'<a href="../{k}/gastos-de-compra/">Gastos de comprar en {esc(c["n"])}</a>' for k, c in C.items()) + f"""</div>
<style>#calc input{{display:block;width:100%;box-sizing:border-box;margin-top:4px;font:16px Inter,system-ui,sans-serif;padding:10px;min-height:44px;border:1px solid #d6d0c4;border-radius:10px;background:#fff;color:#1d2321}}#calc label{{display:block}}</style>
<script>(function(){{var f=function(n){{return String(Math.round(n)).replace(/\\B(?=(\\d{{3}})+(?!\\d))/g,".")}};function c(){{var tv=document.getElementById("ht").value,q=+document.getElementById("hq").value,a=+document.getElementById("ha").value,t=+tv/1200,r=document.getElementById("hr"),s=document.getElementById("hs");
if(tv===""||!(q>0&&a>0&&a<=50&&t>=0&&t<1)){{r.textContent="—";s.textContent="Revisa los datos";return}}var n=a*12,m=t?q*t/(1-Math.pow(1+t,-n)):q/n;r.textContent="≈ "+f(m)+" €";s.textContent="Ganar ≈ "+f(m/{ESC})+" € netos · intereses "+f(m*n-q)+" €"}}
["hq","ha","ht"].forEach(function(i){{document.getElementById(i).addEventListener("input",c)}});c()}})()</script>"""
os.makedirs(F("hipoteca"), exist_ok=True)
open(F("hipoteca", "index.html"), "w", encoding="utf-8").write(page(
    "Cuota de la hipoteca: cuánto pagarás al mes (calculadora 2026)",
    desc_corta(f"Hipoteca de 150.000 € a {ANOS} años: ≈ {fmt(h150)} €/mes; de 200.000 €: ≈ {fmt(h200)} €. Cuotas a 20, 25 y 30 años, intereses y sueldo necesario.", " Calculadora."),
    "hipoteca/", body, [("Vivible", "../"), ("Cuota de la hipoteca", None)], hq_ld))
urls.insert(3, BASE + "hipoteca/")

# ---------- dinero para alquilar (gastos-de-alquiler/): «cuánto dinero necesito para alquilar un piso», «fianza alquiler», «garantía adicional»;
# primer mes + fianza legal de un mes (LAU art. 36) + garantía adicional de hasta dos meses; honorarios de la inmobiliaria a cargo del propietario (Ley 12/2023)
ra = sorted(C.items(), key=lambda kc: kc[1]["alquiler"])
tra = "".join(f'<tr><td><a href="../{k}/sueldo-para-alquilar/">{esc(c["n"])}</a></td><td>{fmt(c["alquiler"] * M2A)} €</td><td>{fmt(c["alquiler"] * M2A * 2)} €</td><td><b>{fmt(c["alquiler"] * M2A * 4)} €</b></td></tr>' for k, c in ra)
rh = sorted(C.items(), key=lambda kc: kc[1]["hab"])
trh = "".join(f'<tr><td><a href="../{k}/habitacion/">{esc(c["n"])}</a></td><td>{fmt(c["hab"])} €</td><td><b>{fmt(c["hab"] * 2)} €</b></td></tr>' for k, c in rh)
EJ = [600, 800, 1000, 1200, 1500]
tre = "".join(f"<tr><td>{fmt(r)} €</td><td>{fmt(r * 2)} €</td><td>{fmt(r * 4)} €</td><td>{fmt(r / ESF)} €</td></tr>" for r in EJ)
ab, ac = ra[0][1], ra[-1][1]
ga_html, ga_ld = faq([
    ("¿Cuánto dinero necesito para alquilar un piso?",
     "Lo normal es pagar al firmar el primer mes y una fianza de un mes: el doble del alquiler. Si el propietario pide además una garantía adicional (hasta dos meses más), hasta cuatro veces el alquiler. "
     f"Para un piso medio de {M2A} m², de {fmt(ab['alquiler'] * M2A * 2)} € en {ab['n']} a {fmt(ac['alquiler'] * M2A * 4)} € en {ac['n']}."),
    ("¿Cuánto es la fianza de un alquiler?",
     "Para una vivienda, la ley fija una fianza de un mes de alquiler. Te la deben devolver al terminar el contrato, descontando solo lo que se deba o los daños que no sean el desgaste normal."),
    ("¿Qué es la garantía adicional y cuánto pueden pedir?",
     "Es un dinero extra, aparte de la fianza, que algunos propietarios piden como seguridad (en efectivo o con un aval bancario). En los contratos de vivienda de hasta cinco años (siete si el propietario es una empresa) no puede pasar de dos meses de alquiler."),
    ("¿Tengo que pagar a la inmobiliaria si alquilo un piso?",
     "No. Desde la Ley 12/2023, de vivienda, los honorarios de la inmobiliaria y los gastos de hacer el contrato los paga el propietario, no quien alquila."),
    ("¿Cuánto dinero necesito para alquilar una habitación?",
     f"Normalmente el primer mes y un mes de fianza. Con el precio medio de cada ciudad, de unos {fmt(rh[0][1]['hab'] * 2)} € en {rh[0][1]['n']} a unos {fmt(rh[-1][1]['hab'] * 2)} € en {rh[-1][1]['n']}."),
])
body = f"""<h1>¿Cuánto dinero necesito para alquilar un piso? Fianza y garantía (2026)</h1>
<p>Antes de entrar a vivir de alquiler hay que tener ahorrado algo más que el primer mes. Aquí tienes qué se paga al firmar, cuánto es en cada ciudad para un piso medio de {M2A} m² y para una habitación, y lo que la ley permite pedir.</p>
<div class="g"><div class="k"><small>Lo normal al firmar</small><b>2 meses</b><small>Primer mes y fianza de un mes</small></div>
<div class="k"><small>Como mucho, con garantía</small><b>4 meses</b><small>Más hasta dos meses de garantía adicional</small></div></div>
<div class="card"><b>Qué se paga al firmar</b><ul style="margin:8px 0 0;padding-left:20px">
<li><b>El primer mes</b> de alquiler.</li>
<li><b>La fianza:</b> un mes, obligatoria por ley. Te la devuelven al irte si no hay deudas ni daños.</li>
<li><b>La garantía adicional</b> (si te la piden): hasta dos meses más, en efectivo o con aval.</li>
<li><b>La inmobiliaria no la pagas tú:</b> sus honorarios corren a cargo del propietario (Ley 12/2023).</li></ul></div>
<h2 style="font:700 21px/1.2 Fraunces,Georgia,serif;margin:24px 0 0">Dinero para entrar en un piso, por ciudad</h2>
<div class="card"><table class="cmp"><caption class="m" style="text-align:left;padding-bottom:6px">Piso de {M2A} m² al alquiler medio de cada ciudad ({esc(mes_txt)}): alquiler al mes, lo normal al firmar (primer mes y fianza) y el máximo con dos meses de garantía adicional</caption><tr><th scope="col">Ciudad</th><th scope="col">Alquiler</th><th scope="col">Al firmar</th><th scope="col">Máximo</th></tr>{tra}</table></div>
<h2 style="font:700 21px/1.2 Fraunces,Georgia,serif;margin:24px 0 0">Dinero para entrar en una habitación</h2>
<div class="card"><table class="cmp"><caption class="m" style="text-align:left;padding-bottom:6px">Habitación al precio medio de cada ciudad: alquiler al mes y lo que se suele pagar al entrar (primer mes y un mes de fianza)</caption><tr><th scope="col">Ciudad</th><th scope="col">Habitación</th><th scope="col">Al entrar</th></tr>{trh}</table></div>
<h2 style="font:700 21px/1.2 Fraunces,Georgia,serif;margin:24px 0 0">Según lo que cueste el piso</h2>
<div class="card"><table class="cmp"><caption class="m" style="text-align:left;padding-bottom:6px">Dinero al firmar según el alquiler, y sueldo neto recomendado para que el alquiler no pase del 33 %</caption><tr><th scope="col">Alquiler</th><th scope="col">Al firmar</th><th scope="col">Máximo</th><th scope="col">Sueldo neto</th></tr>{tre}</table>
<p class="m">Cuenta también con la mudanza y con el alta de la luz, el agua e internet si van a tu nombre.</p></div>
{ga_html}
<a class="cta" href="../">¿Has visto un piso? Comprueba si el precio es justo</a>
<div class="card m"><b>Más guías:</b> <a href="../sueldo/">Qué piso puedo pagar con mi sueldo</a> · <a href="../precios/">Comparar las 10 ciudades</a> · """ + " · ".join(f'<a href="../{k}/alquiler/">Alquiler en {esc(c["n"])}</a>' for k, c in C.items()) + """</div>"""
os.makedirs(F("gastos-de-alquiler"), exist_ok=True)
open(F("gastos-de-alquiler", "index.html"), "w", encoding="utf-8").write(page(
    "¿Cuánto dinero necesito para alquilar un piso? Fianza y garantía (2026)",
    desc_corta(f"Al firmar se paga el primer mes y un mes de fianza, y hasta dos de garantía. Para un piso medio, de {fmt(ab['alquiler'] * M2A * 2)} € en {ab['n']} a {fmt(ac['alquiler'] * M2A * 4)} € en {ac['n']}.", ""),
    "gastos-de-alquiler/", body, [("Vivible", "../"), ("Dinero para alquilar", None)], ga_ld))
urls.insert(4, BASE + "gastos-de-alquiler/")

# ---------- gastos de comprar (gastos-de-compra/): «calculadora gastos compra vivienda», «cuánto dinero necesito para comprar un piso»,
# «impuestos al comprar una vivienda»; las mismas fórmulas que las guías de gastos de compra de cada ciudad (gastos(), NOT, TAS, cuota())
assert "gastos-de-compra" not in C
rg = sorted(C.items(), key=lambda kc: gastos(kc[1]["venta"] * M2A, kc[1])[2])
trg = "".join(f'<tr><td><a href="../{k}/gastos-de-compra/">{esc(c["n"])}</a></td><td>{pct(c["itp"])} %</td><td>{fmt(c["venta"] * M2A)} €</td><td>{fmt(gastos(c["venta"] * M2A, c)[0])} €</td><td><b>{fmt(gastos(c["venta"] * M2A, c)[2])} €</b></td></tr>' for k, c in rg)
cc = sorted({c["ccaa"]: c for c in C.values()}.values(), key=lambda c: c["itp"])
trc = "".join(f'<tr><td>{esc(c["ccaa"])}</td><td>{pct(c["itp"])} %</td><td>10 % + {pct(c["ajd"])} %</td></tr>' for c in cc)
E200 = {k: gastos(200000, c) for k, c in C.items()}
gb, gc = min(C, key=lambda k: E200[k][0]), max(C, key=lambda k: E200[k][0])
gmad = gastos(200000, C["madrid"]) if "madrid" in C else E200[gb]
GJS = json.dumps({k: [c["n"], c["ccaa"], c["itp"], c["ajd"], round(c["venta"] * M2A, -3)] for k, c in C.items()}, ensure_ascii=False).replace("</", "<\\/")
opts = "".join(f'<option value="{k}">{esc(c["n"])} ({esc(c["ccaa"])})</option>' for k, c in C.items())
k0 = next(iter(C)); c0 = C[k0]; p0 = round(c0["venta"] * M2A, -3); g0 = gastos(p0, c0)
gc_html, gc_ld = faq([
    ("¿Cuánto dinero necesito para comprar un piso?",
     "Normalmente el 20 % del precio de entrada (el banco suele prestar como mucho el 80 %), más el impuesto de compra y unos gastos de notaría, registro, gestoría y tasación. "
     f"Para un piso de 200.000 € de segunda mano, entre {fmt(E200[gb][2])} € {en_ccaa(C[gb]['ccaa'])} y {fmt(E200[gc][2])} € {en_ccaa(C[gc]['ccaa'])}."),
    ("¿Qué impuestos se pagan al comprar una vivienda?",
     "Si es de segunda mano, el impuesto de transmisiones patrimoniales (ITP), que fija cada comunidad. Si es nueva (la primera venta, de la constructora), el 10 % de IVA y el impuesto de actos jurídicos documentados (AJD) de la comunidad."),
    ("¿Cuánto son los gastos de notaría, registro y gestoría?",
     f"Como orientación, alrededor del 1,5 % del precio entre los tres, más unos {TAS} € de tasación si pides hipoteca. Para un piso de 200.000 €, unos {fmt(200000 * NOT + TAS)} €."),
    ("¿Cuánto cuesta comprar un piso de 200.000 €?",
     f"De segunda mano, el impuesto va de {fmt(E200[gb][0])} € ({C[gb]['ccaa']}, {pct(C[gb]['itp'])} %) a {fmt(E200[gc][0])} € ({C[gc]['ccaa']}, {pct(C[gc]['itp'])} %). Con la entrada del 20 % y los gastos, necesitarás ahorrar entre {fmt(E200[gb][2])} € y {fmt(E200[gc][2])} €."),
    ("¿Los gastos de compra entran en la hipoteca?",
     "Normalmente no: el banco presta un porcentaje del precio (o de la tasación, si es menor) y los impuestos y gastos los pagas con tus ahorros. Desde 2019 los gastos de la escritura de la hipoteca los paga el banco."),
])
body = f"""<h1>Gastos de comprar un piso: calculadora de impuestos y ahorro (2026)</h1>
<p>Al precio del piso hay que sumarle el impuesto de compra, que depende de la comunidad y de si el piso es nuevo o de segunda mano, y los gastos de notaría, registro, gestoría y tasación. Además, el banco suele prestar como mucho el 80 %, así que la entrada también sale de tus ahorros. Calcula cuánto necesitas:</p>
<div class="card"><form id="calc" onsubmit="return false"><b>Calcula los gastos de tu compra</b>
<div class="g" style="margin-top:10px"><label class="m">Precio del piso (€)<input id="gp" type="number" inputmode="numeric" min="1000" step="1000" value="{p0}"></label>
<label class="m">Ciudad<select id="gk">{opts}</select></label>
<label class="m">Tipo de piso<select id="gn"><option value="0">Segunda mano (ITP)</option><option value="1">Obra nueva (IVA y AJD)</option></select></label>
<label class="m">Entrada (%)<input id="ge" type="number" inputmode="numeric" min="0" max="100" step="5" value="20"></label></div>
<div class="g" style="margin-top:12px" aria-live="polite"><div class="k"><small id="gil">Impuesto (ITP {pct(c0["itp"])} %)</small><b id="gi">{fmt(g0[0])} €</b></div>
<div class="k"><small>Notaría, registro, gestoría y tasación</small><b id="go">{fmt(g0[1])} €</b></div>
<div class="k"><small>Ahorro total necesario</small><b id="gt">{fmt(g0[2])} €</b><small id="gts">Entrada, impuesto y gastos</small></div>
<div class="k"><small>Hipoteca (30 años, 2,8 %)</small><b id="gh">{fmt(cuota(p0))} €/mes</b><small id="ghs">Préstamo del 80 %</small></div></div></form>
<p class="m">El precio de partida es el de un piso medio de {M2A} m² en la ciudad elegida. Tipos generales de cada comunidad; algunas los rebajan a jóvenes, familias numerosas o pisos baratos.</p></div>
<h2 style="font:700 21px/1.2 Fraunces,Georgia,serif;margin:24px 0 0">Ahorro para comprar el piso medio, por ciudad</h2>
<div class="card"><table class="cmp"><caption class="m" style="text-align:left;padding-bottom:6px">Piso de segunda mano de {M2A} m² al precio medio de cada ciudad ({esc(mes_txt)}): ITP de la comunidad, impuesto y ahorro total con el 20 % de entrada, de menos a más</caption><tr><th scope="col">Ciudad</th><th scope="col">ITP</th><th scope="col">Piso</th><th scope="col">Impuesto</th><th scope="col">Ahorro</th></tr>{trg}</table></div>
<h2 style="font:700 21px/1.2 Fraunces,Georgia,serif;margin:24px 0 0">Impuestos por comunidad</h2>
<div class="card"><table class="cmp"><caption class="m" style="text-align:left;padding-bottom:6px">Tipo general del ITP (segunda mano) y de IVA más AJD (obra nueva) en las comunidades de las ciudades de Vivible</caption><tr><th scope="col">Comunidad</th><th scope="col">Segunda mano</th><th scope="col">Obra nueva</th></tr>{trc}</table>
<p class="m">Tipos generales: revisa en la web de tu comunidad si tienes derecho a uno reducido antes de firmar.</p></div>
{gc_html}
<a class="cta" href="../">¿Has visto un piso? Comprueba si el precio es justo</a>
<div class="card m"><b>Más guías:</b> <a href="../hipoteca/">Cuota de la hipoteca</a> · <a href="../sueldo/">Qué piso puedo pagar con mi sueldo</a> · <a href="../precios/">Comparar las 10 ciudades</a> · """ + " · ".join(f'<a href="../{k}/gastos-de-compra/">Gastos de comprar en {esc(c["n"])}</a>' for k, c in C.items()) + f"""</div>
<style>#calc input,#calc select{{display:block;width:100%;box-sizing:border-box;margin-top:4px;font:16px Inter,system-ui,sans-serif;padding:10px;min-height:44px;border:1px solid #d6d0c4;border-radius:10px;background:#fff;color:#1d2321}}#calc label{{display:block}}</style>
<script>(function(){{var D={GJS},$=function(i){{return document.getElementById(i)}},f=function(n){{return String(Math.round(n)).replace(/\\B(?=(\\d{{3}})+(?!\\d))/g,".")}},pc=function(x){{return String(x).replace(".",",")}},ult="{k0}";
function c(){{var c=D[$("gk").value],nu=$("gn").value==="1",pv=$("gp").value,ev=$("ge").value,p=+pv,e=+ev/100;if(!c)return;
$("gil").textContent=nu?"Impuesto (IVA 10 % y AJD "+pc(c[3])+" %)":"Impuesto (ITP "+pc(c[2])+" %)";
if(pv===""||ev===""||!(p>0&&e>=0&&e<=1)){{["gi","go","gt","gh"].forEach(function(i){{$(i).textContent="—"}});$("gts").textContent="Revisa los datos";return}}
var im=p*(nu?10+c[3]:c[2])/100,ot=p*{NOT}+{TAS},t=p*e+im+ot,q=p*(1-e),i={TIN}/12,m=q>0?q*i/(1-Math.pow(1+i,-{ANOS * 12})):0;
$("gi").textContent=f(im)+" €";$("go").textContent=f(ot)+" €";$("gt").textContent=f(t)+" €";$("gts").textContent="Entrada ("+f(p*e)+" €), impuesto y gastos";
$("gh").textContent=f(m)+" €/mes";$("ghs").textContent="Préstamo de "+f(q)+" €"}}
$("gk").addEventListener("change",function(){{var a=D[ult],b=D[$("gk").value];if(a&&b&&+$("gp").value===a[4])$("gp").value=b[4];ult=$("gk").value;c()}});
["gp","gn","ge"].forEach(function(i){{$(i).addEventListener("input",c);$(i).addEventListener("change",c)}});c()}})()</script>"""
os.makedirs(F("gastos-de-compra"), exist_ok=True)
open(F("gastos-de-compra", "index.html"), "w", encoding="utf-8").write(page(
    "Gastos de comprar un piso: calculadora de impuestos y ahorro (2026)",
    desc_corta(f"Calcula el ITP o el IVA, la notaría y el ahorro para comprar un piso. Con 200.000 € de segunda mano, de {fmt(E200[gb][2])} € a {fmt(E200[gc][2])} € según la comunidad.", ""),
    "gastos-de-compra/", body, [("Vivible", "../"), ("Gastos de comprar", None)], gc_ld))
urls.insert(5, BASE + "gastos-de-compra/")

# ---------- rentabilidad del alquiler (rentabilidad/): «rentabilidad alquiler por ciudades», «dónde es más rentable comprar para alquilar»;
# rentabilidad bruta = alquiler de un año / precio de compra (la misma que las guías «comprar o alquilar»); en el ranking de distritos
# solo entran los que tienen los dos precios publicados (los estimados saldrían de nuestra propia fórmula, no del mercado)
rc = sorted(C.items(), key=lambda kc: -(kc[1]["alquiler"] * 12 / kc[1]["venta"]))
rb_c = lambda c: c["alquiler"] * 12 / c["venta"] * 100
trc = "".join(f'<tr><td><a href="../{k}/comprar-o-alquilar/">{esc(c["n"])}</a></td><td>{fmt(c["venta"] * M2A)} €</td><td>{fmt(c["alquiler"] * M2A)} €</td><td><b>{dec(rb_c(c))} %</b></td></tr>' for k, c in rc)
rdis = []
for ck, c in C.items():
    for d, (s, r) in c["d"].items():
        if s is not None and r is not None: rdis.append((r * 12 / s * 100, d, ck, c["n"], s * M2A, r * M2A))
rdis.sort(key=lambda x: -x[0])
NTOP = 15
fila_d = lambda x: f'<tr><td><a href="../{x[2]}/{slug(x[1])}/">{esc(x[1])}</a> <span class="m">({esc(x[3])})</span></td><td>{fmt(x[4])} €</td><td>{fmt(x[5])} €</td><td><b>{dec(x[0])} %</b></td></tr>'
trt, trb = "".join(fila_d(x) for x in rdis[:NTOP]), "".join(fila_d(x) for x in rdis[::-1][:10])
nest = sum(len(c["d"]) for c in C.values()) - len(rdis)
cmx, cmn = rc[0][1], rc[-1][1]
rt_html, rt_ld = faq([
    ("¿En qué ciudad es más rentable comprar un piso para alquilarlo?",
     f"De estas 10, en {cmx['n']}: un piso medio de {M2A} m² cuesta unos {fmt(cmx['venta'] * M2A)} € y se alquila por unos {fmt(cmx['alquiler'] * M2A)} € al mes, una rentabilidad bruta del {dec(rb_c(cmx))} %. "
     f"La más baja es {cmn['n']}, con un {dec(rb_c(cmn))} %."),
    ("¿Qué distritos dan más rentabilidad al alquilar?",
     "Con los precios medios publicados, " + ", ".join(f"{x[1]} ({x[3]}, {dec(x[0])} %)" for x in rdis[:3]) + ". Suelen ser barrios con pisos más baratos, donde el alquiler pesa más en proporción al precio."),
    ("¿Cómo se calcula la rentabilidad bruta de un alquiler?",
     "Se divide lo que se cobra de alquiler en un año entre lo que cuesta el piso y se multiplica por 100. Por ejemplo, un piso de 200.000 € alquilado a 900 € al mes da 10.800 € al año: un 5,4 % bruto."),
    ("¿Qué gastos hay que restar para saber la rentabilidad real?",
     "La rentabilidad bruta no descuenta nada. Para la real (neta) hay que restar el impuesto y los gastos de la compra, el IBI, la comunidad, el seguro, las reparaciones, los meses en que el piso esté vacío y el IRPF de lo que cobres. Por eso la neta suele quedar bastante por debajo."),
])
body = f"""<h1>Rentabilidad del alquiler en España por ciudades y distritos (2026)</h1>
<p>¿Cuánto renta un piso alquilado? Comparamos la rentabilidad bruta (alquiler de un año entre el precio de compra) en las 10 ciudades de Vivible y en sus distritos, con los precios medios de idealista ({esc(mes_txt)}).</p>
<div class="g"><div class="k"><small>Ciudad más rentable</small><b>{dec(rb_c(cmx))} %</b><small>{esc(cmx["n"])}</small></div>
<div class="k"><small>Ciudad menos rentable</small><b>{dec(rb_c(cmn))} %</b><small>{esc(cmn["n"])}</small></div></div>
<h2 style="font:700 21px/1.2 Fraunces,Georgia,serif;margin:24px 0 0">Por ciudades</h2>
<div class="card"><table class="cmp"><caption class="m" style="text-align:left;padding-bottom:6px">Piso medio de {M2A} m²: precio de compra, alquiler al mes y rentabilidad bruta, de la ciudad más rentable a la menos</caption><tr><th scope="col">Ciudad</th><th scope="col">Precio</th><th scope="col">Alquiler</th><th scope="col">Rentab.</th></tr>{trc}</table></div>
<h2 style="font:700 21px/1.2 Fraunces,Georgia,serif;margin:24px 0 0">Los {NTOP} distritos más rentables</h2>
<div class="card"><table class="cmp"><caption class="m" style="text-align:left;padding-bottom:6px">Piso de {M2A} m² en cada distrito: precio, alquiler al mes y rentabilidad bruta</caption><tr><th scope="col">Distrito</th><th scope="col">Precio</th><th scope="col">Alquiler</th><th scope="col">Rentab.</th></tr>{trt}</table></div>
<h2 style="font:700 21px/1.2 Fraunces,Georgia,serif;margin:24px 0 0">Los 10 distritos menos rentables</h2>
<div class="card"><table class="cmp"><caption class="m" style="text-align:left;padding-bottom:6px">Piso de {M2A} m²: precio, alquiler al mes y rentabilidad bruta, del menos rentable hacia arriba</caption><tr><th scope="col">Distrito</th><th scope="col">Precio</th><th scope="col">Alquiler</th><th scope="col">Rentab.</th></tr>{trb}</table>
<p class="m">Solo entran los {len(rdis)} distritos con precio de venta y de alquiler publicados ({nest} quedan fuera porque idealista no da uno de los dos). Rentabilidad bruta: no descuenta impuestos ni gastos. Cifras orientativas, no una recomendación de inversión.</p></div>
{rt_html}
<a class="cta" href="../">¿Has visto un piso? Comprueba si el precio es justo</a>
<div class="card m"><b>Más guías:</b> <a href="../precios/">Comparar las 10 ciudades</a> · <a href="../gastos-de-compra/">Calculadora de gastos de compra</a> · <a href="../hipoteca/">Cuota de la hipoteca</a> · <a href="../barrios-baratos/">Barrios más baratos</a> · <a href="../barrios-caros/">Barrios más caros</a> · """ + " · ".join(f'<a href="../{k}/comprar-o-alquilar/">Comprar o alquilar en {esc(c["n"])}</a>' for k, c in C.items()) + """</div>"""
os.makedirs(F("rentabilidad"), exist_ok=True)
open(F("rentabilidad", "index.html"), "w", encoding="utf-8").write(page(
    "Rentabilidad del alquiler por ciudades y distritos (2026)",
    desc_corta(f"Rentabilidad bruta de alquilar un piso en 10 ciudades: del {dec(rb_c(cmx))} % de {cmx['n']} al {dec(rb_c(cmn))} % de {cmn['n']}.", " Y los distritos más y menos rentables."),
    "rentabilidad/", body, [("Vivible", "../"), ("Rentabilidad del alquiler", None)], rt_ld))
urls.insert(6, BASE + "rentabilidad/")

# ---------- barrios más baratos (barrios-baratos/): «barrios más baratos para alquilar en España», «distrito más barato de <ciudad>»;
# solo distritos con el precio publicado por idealista (los estimados saldrían de nuestra propia fórmula); piso de M2A m² como en las demás guías
assert "barrios-baratos" not in C
NBB = 15
pub_r = sorted(((r, d, ck, c["n"]) for ck, c in C.items() for d, (s_, r) in c["d"].items() if r is not None), key=lambda x: x[0])
pub_s = sorted(((s_, d, ck, c["n"]) for ck, c in C.items() for d, (s_, r) in c["d"].items() if s_ is not None), key=lambda x: x[0])
fila_bb = lambda x, ud, mes: f'<tr><td><a href="../{x[2]}/{slug(x[1])}/">{esc(x[1])}</a> <span class="m">({esc(x[3])})</span></td><td>{dec(x[0]) if mes else fmt(x[0])} €</td><td><b>{fmt(x[0] * M2A)} €{ud}</b></td></tr>'
tbr = "".join(fila_bb(x, "", True) for x in pub_r[:NBB])
tbs = "".join(fila_bb(x, "", False) for x in pub_s[:NBB])
por_c = []
for ck, c in C.items():
    rr = [x for x in pub_r if x[2] == ck]; ss = [x for x in pub_s if x[2] == ck]
    por_c.append((ck, c, rr[0] if rr else None, ss[0] if ss else None))
celda = lambda x, mes: (f'<a href="../{x[2]}/{slug(x[1])}/">{esc(x[1])}</a><br><span class="m">{fmt(x[0] * M2A)} €{"/mes" if mes else ""}</span>' if x else '<span class="m">Sin dato</span>')
tbc = "".join(f'<tr><td><a href="../{ck}/">{esc(c["n"])}</a></td><td style="white-space:normal">{celda(r_, True)}</td><td style="white-space:normal">{celda(s_, False)}</td></tr>' for ck, c, r_, s_ in por_c)
r0, s0 = pub_r[0], pub_s[0]
bb_html, bb_ld = faq([
    ("¿Cuál es el barrio más barato para alquilar en una gran ciudad de España?",
     f"De los {len(pub_r)} distritos con alquiler publicado en estas 10 ciudades, {r0[1]} ({r0[3]}): {dec(r0[0])} € por m² al mes, unos {fmt(r0[0] * M2A)} € por un piso de {M2A} m². "
     "Le siguen " + ", ".join(f"{x[1]} ({x[3]}, {dec(x[0])} €/m²)" for x in pub_r[1:3]) + "."),
    ("¿Dónde es más barato comprar un piso en una gran ciudad?",
     f"En {s0[1]} ({s0[3]}): {fmt(s0[0])} € por m², unos {fmt(s0[0] * M2A)} € por un piso de {M2A} m². "
     "Le siguen " + ", ".join(f"{x[1]} ({x[3]}, {fmt(x[0])} €/m²)" for x in pub_s[1:3]) + "."),
    ("¿Cuál es el distrito más barato de cada ciudad para alquilar?",
     "; ".join(f"{c['n']}: {r_[1]} ({dec(r_[0])} €/m²)" for ck, c, r_, s_ in por_c if r_) + "."),
    ("¿Por qué hay tanta diferencia de precio entre barrios?",
     "Influyen la distancia al centro, el transporte, los servicios, la antigüedad de los edificios y la demanda. Un barrio barato puede compensar si tienes buen transporte al trabajo: compruébalo antes de decidir."),
])
body = f"""<h1>Los barrios más baratos para alquilar y comprar en España (2026)</h1>
<p>¿Dónde sale más barato vivir en las grandes ciudades? Ordenamos los distritos de las 10 ciudades de Vivible por precio del alquiler y de la compra, con los precios medios de idealista ({esc(mes_txt)}), para un piso de {M2A} m² (unos 2 dormitorios).</p>
<div class="g"><div class="k"><small>Más barato para alquilar</small><b>{fmt(r0[0] * M2A)} €/mes</b><small>{esc(r0[1])} ({esc(r0[3])})</small></div>
<div class="k"><small>Más barato para comprar</small><b>{fmt(s0[0] * M2A)} €</b><small>{esc(s0[1])} ({esc(s0[3])})</small></div></div>
<h2 style="font:700 21px/1.2 Fraunces,Georgia,serif;margin:24px 0 0">Los {NBB} más baratos para alquilar</h2>
<div class="card"><table class="cmp"><caption class="m" style="text-align:left;padding-bottom:6px">Alquiler medio por m² al mes y lo que cuesta al mes un piso de {M2A} m², del más barato hacia arriba</caption><tr><th scope="col">Distrito</th><th scope="col">€/m² al mes</th><th scope="col">{M2A} m² al mes</th></tr>{tbr}</table></div>
<h2 style="font:700 21px/1.2 Fraunces,Georgia,serif;margin:24px 0 0">Los {NBB} más baratos para comprar</h2>
<div class="card"><table class="cmp"><caption class="m" style="text-align:left;padding-bottom:6px">Precio medio por m² y lo que cuesta un piso de {M2A} m², del más barato hacia arriba</caption><tr><th scope="col">Distrito</th><th scope="col">€/m²</th><th scope="col">Piso de {M2A} m²</th></tr>{tbs}</table></div>
<h2 style="font:700 21px/1.2 Fraunces,Georgia,serif;margin:24px 0 0">El más barato de cada ciudad</h2>
<div class="card"><table class="cmp"><caption class="m" style="text-align:left;padding-bottom:6px">Distrito con el alquiler y con el precio de compra más bajos de cada ciudad, para un piso de {M2A} m²</caption><tr><th scope="col">Ciudad</th><th scope="col">Para alquilar</th><th scope="col">Para comprar</th></tr>{tbc}</table>
<p class="m">Solo entran los distritos con precio publicado por idealista ({len(pub_r)} con alquiler y {len(pub_s)} con venta). Un piso concreto puede costar más o menos según su estado, planta y calle.</p></div>
{bb_html}
<a class="cta" href="../">¿Has visto un piso en un barrio barato? Comprueba su precio, transporte y ruido</a>
<div class="card m"><b>Más guías:</b> <a href="../barrios-caros/">Barrios más caros</a> · <a href="../precios/">Comparar las 10 ciudades</a> · <a href="../barrios/">¿En qué distrito está mi barrio?</a> · <a href="../rentabilidad/">Rentabilidad del alquiler</a> · <a href="../sueldo/">Qué piso puedo pagar con mi sueldo</a> · """ + " · ".join(f'<a href="../{k}/alquiler/">Alquiler en {esc(c["n"])}</a> · <a href="../{k}/venta/">Comprar en {esc(c["n"])}</a>' for k, c in C.items()) + """</div>"""
os.makedirs(F("barrios-baratos"), exist_ok=True)
open(F("barrios-baratos", "index.html"), "w", encoding="utf-8").write(page(
    "Barrios más baratos para alquilar y comprar en España (2026)",
    desc_corta(f"Los distritos más baratos de 10 ciudades: alquilar desde {fmt(r0[0] * M2A)} €/mes en {r0[1]} ({r0[3]}) y comprar desde {fmt(s0[0] * M2A)} € en {s0[1]} ({s0[3]}).", " Y el más barato de cada ciudad."),
    "barrios-baratos/", body, [("Vivible", "../"), ("Barrios más baratos", None)], bb_ld))
urls.insert(7, BASE + "barrios-baratos/")

# ---------- barrios más caros (barrios-caros/): «barrio más caro de España», «zonas más caras para vivir en Madrid»;
# la pareja de barrios-baratos/, con las mismas listas (solo precio publicado) leídas del más caro hacia abajo
assert "barrios-caros" not in C
car_r, car_s = sorted(pub_r, key=lambda x: -x[0]), sorted(pub_s, key=lambda x: -x[0])  # empates en el mismo orden que barrios-baratos
tcr = "".join(fila_bb(x, "", True) for x in car_r[:NBB])
tcs = "".join(fila_bb(x, "", False) for x in car_s[:NBB])
tcc = "".join(f'<tr><td><a href="../{ck}/">{esc(c["n"])}</a></td><td style="white-space:normal">{celda(([x for x in car_r if x[2] == ck] or [None])[0], True)}</td><td style="white-space:normal">{celda(([x for x in car_s if x[2] == ck] or [None])[0], False)}</td></tr>' for ck, c in C.items())
rc, sc_ = car_r[0], car_s[0]
bc_html, bc_ld = faq([
    ("¿Cuál es el barrio más caro para alquilar en una gran ciudad de España?",
     f"De los {len(pub_r)} distritos con alquiler publicado en estas 10 ciudades, {rc[1]} ({rc[3]}): {dec(rc[0])} € por m² al mes, unos {fmt(rc[0] * M2A)} € por un piso de {M2A} m². "
     "Le siguen " + " y ".join(f"{x[1]} ({x[3]}, {dec(x[0])} €/m²)" for x in car_r[1:3]) + "."),
    ("¿Dónde es más caro comprar un piso en una gran ciudad?",
     f"En {sc_[1]} ({sc_[3]}): {fmt(sc_[0])} € por m², unos {fmt(sc_[0] * M2A)} € por un piso de {M2A} m². "
     "Le siguen " + " y ".join(f"{x[1]} ({x[3]}, {fmt(x[0])} €/m²)" for x in car_s[1:3]) + "."),
    ("¿Cuál es el distrito más caro de cada ciudad para alquilar?",
     "; ".join(f"{c['n']}: {x[1]} ({dec(x[0])} €/m²)" for ck, c in C.items() for x in [([y for y in car_r if y[2] == ck] or [None])[0]] if x) + "."),
    ("¿Cuánto más cuesta vivir en el distrito más caro que en el más barato?",
     f"Alquilar un piso de {M2A} m² en {rc[1]} ({rc[3]}) cuesta unos {fmt(rc[0] * M2A)} € al mes; en {pub_r[0][1]} ({pub_r[0][3]}), unos {fmt(pub_r[0][0] * M2A)} €: "
     f"{dec(rc[0] / pub_r[0][0])} veces más. Comprar en {sc_[1]} cuesta {dec(sc_[0] / pub_s[0][0])} veces más que en {pub_s[0][1]} ({pub_s[0][3]})."),
    ("¿Merece la pena pagar más por un barrio caro?",
     "Depende de lo que te ahorres en tiempo y transporte. Un barrio caro suele estar bien comunicado y con servicios cerca, pero un piso concreto puede no justificar su precio: compara con distritos vecinos y comprueba el estado, la planta y la luz."),
])
body = f"""<h1>Los barrios más caros para alquilar y comprar en España (2026)</h1>
<p>¿Dónde cuesta más vivir en las grandes ciudades? Ordenamos los distritos de las 10 ciudades de Vivible por precio del alquiler y de la compra, del más caro hacia abajo, con los precios medios de idealista ({esc(mes_txt)}), para un piso de {M2A} m² (unos 2 dormitorios).</p>
<div class="g"><div class="k"><small>Más caro para alquilar</small><b>{fmt(rc[0] * M2A)} €/mes</b><small>{esc(rc[1])} ({esc(rc[3])})</small></div>
<div class="k"><small>Más caro para comprar</small><b>{fmt(sc_[0] * M2A)} €</b><small>{esc(sc_[1])} ({esc(sc_[3])})</small></div></div>
<h2 style="font:700 21px/1.2 Fraunces,Georgia,serif;margin:24px 0 0">Los {NBB} más caros para alquilar</h2>
<div class="card"><table class="cmp"><caption class="m" style="text-align:left;padding-bottom:6px">Alquiler medio por m² al mes y lo que cuesta al mes un piso de {M2A} m², del más caro hacia abajo</caption><tr><th scope="col">Distrito</th><th scope="col">€/m² al mes</th><th scope="col">{M2A} m² al mes</th></tr>{tcr}</table></div>
<h2 style="font:700 21px/1.2 Fraunces,Georgia,serif;margin:24px 0 0">Los {NBB} más caros para comprar</h2>
<div class="card"><table class="cmp"><caption class="m" style="text-align:left;padding-bottom:6px">Precio medio por m² y lo que cuesta un piso de {M2A} m², del más caro hacia abajo</caption><tr><th scope="col">Distrito</th><th scope="col">€/m²</th><th scope="col">Piso de {M2A} m²</th></tr>{tcs}</table></div>
<h2 style="font:700 21px/1.2 Fraunces,Georgia,serif;margin:24px 0 0">El más caro de cada ciudad</h2>
<div class="card"><table class="cmp"><caption class="m" style="text-align:left;padding-bottom:6px">Distrito con el alquiler y con el precio de compra más altos de cada ciudad, para un piso de {M2A} m²</caption><tr><th scope="col">Ciudad</th><th scope="col">Para alquilar</th><th scope="col">Para comprar</th></tr>{tcc}</table>
<p class="m">Solo entran los distritos con precio publicado por idealista ({len(pub_r)} con alquiler y {len(pub_s)} con venta). Un piso concreto puede costar más o menos según su estado, planta y calle.</p></div>
{bc_html}
<a class="cta" href="../">¿Te piden mucho por un piso? Comprueba si su precio es justo para la zona</a>
<div class="card m"><b>Más guías:</b> <a href="../barrios-baratos/">Barrios más baratos</a> · <a href="../precios/">Comparar las 10 ciudades</a> · <a href="../barrios/">¿En qué distrito está mi barrio?</a> · <a href="../rentabilidad/">Rentabilidad del alquiler</a> · <a href="../sueldo/">Qué piso puedo pagar con mi sueldo</a> · """ + " · ".join(f'<a href="../{k}/alquiler/">Alquiler en {esc(c["n"])}</a> · <a href="../{k}/venta/">Comprar en {esc(c["n"])}</a>' for k, c in C.items()) + """</div>"""
os.makedirs(F("barrios-caros"), exist_ok=True)
open(F("barrios-caros", "index.html"), "w", encoding="utf-8").write(page(
    "Barrios más caros para alquilar y comprar en España (2026)",
    desc_corta((f"Los distritos más caros de 10 ciudades: en {rc[1]} ({rc[3]}) un piso de {M2A} m² se alquila por {fmt(rc[0] * M2A)} €/mes y se compra por {fmt(sc_[0] * M2A)} €." if rc[1:3] == sc_[1:3] else f"Los distritos más caros de 10 ciudades: alquilar {fmt(rc[0] * M2A)} €/mes en {rc[1]} ({rc[3]}) y comprar {fmt(sc_[0] * M2A)} € en {sc_[1]} ({sc_[3]}).") , " Y el más caro de cada ciudad."),
    "barrios-caros/", body, [("Vivible", "../"), ("Barrios más caros", None)], bc_ld))
urls.insert(8, BASE + "barrios-caros/")

# ---------- comparar dos ciudades (comparar/<a>-o-<b>/ y comparar/): «vivir en Madrid o Barcelona», «Valencia o Málaga para vivir»;
# las mismas cifras y reglas que /precios/ y las guías de cada ciudad (precios.json, piso de M2A m², alquiler ≤ 33 %, cuota ≤ 30 %)
def mas_barato(xa, xb, na, nb):  # («Madrid», 18) : dónde es más barato y cuánto (en % sobre la más cara)
    return (na, (1 - xa / xb) * 100) if xa <= xb else (nb, (1 - xb / xa) * 100)
def barato_d(c, i):  # distrito más barato (i=0 venta, 1 alquiler) con precio publicado; si no hay, con estimado
    pub = [d for d in c["d"] if c["d"][d][i] is not None] or list(c["d"])
    return min(pub, key=lambda d: dprice(c, d)[i])
H2 = 'style="font:700 21px/1.2 Fraunces,Georgia,serif;margin:24px 0 0"'
pares = [(ka, kb) for i, ka in enumerate(C) for kb in list(C)[i + 1:]]
os.makedirs(F("comparar"), exist_ok=True)
for ka, kb in pares:
    A, B = C[ka], C[kb]; na, nb = A["n"], B["n"]; sl = par(ka, kb)
    sa, sb = sueldos(A), sueldos(B)
    va, vb = A["venta"] * M2A, B["venta"] * M2A
    ra, rb = A["alquiler"] * M2A, B["alquiler"] * M2A
    fila = lambda t, x, y: f'<tr><th scope="row" style="font-weight:400">{t}</th><td>{x}</td><td>{y}</td></tr>'
    dva, dvb, dra, drb = barato_d(A, 0), barato_d(B, 0), barato_d(A, 1), barato_d(B, 1)
    tb = (f'<tr><th scope="col">Precio medio</th><th scope="col">{esc(na)}</th><th scope="col">{esc(nb)}</th></tr>'
        + fila("Comprar (m²)", f"{fmt(A['venta'])} €", f"{fmt(B['venta'])} €")
        + fila(f"Piso de {M2A} m² en venta", f"{fmt(va)} €", f"{fmt(vb)} €")
        + fila("Alquilar (m² al mes)", f"{dec(A['alquiler'])} €", f"{dec(B['alquiler'])} €")
        + fila(f"Piso de {M2A} m² en alquiler", f"{fmt(ra)} €/mes", f"{fmt(rb)} €/mes")
        + fila("Habitación", f"{fmt(A['hab'])} €/mes", f"{fmt(B['hab'])} €/mes")
        + fila("Impuesto de compra (2ª mano)", f"{pct(A['itp'])} %", f"{pct(B['itp'])} %")
        + fila(f"Ahorros para comprar el piso de {M2A} m²", f"{fmt(sa[3])} €", f"{fmt(sb[3])} €")
        + fila(f"Hipoteca de ese piso", f"{fmt(cuota(va))} €/mes", f"{fmt(cuota(vb))} €/mes"))
    ts = (f'<tr><th scope="col">Sueldo neto al mes</th><th scope="col">{esc(na)}</th><th scope="col">{esc(nb)}</th></tr>'
        + fila(f"Para alquilar el piso de {M2A} m²", f"{fmt(sa[0])} €", f"{fmt(sb[0])} €")
        + fila("Para una habitación", f"{fmt(sa[1])} €", f"{fmt(sb[1])} €")
        + fila(f"Para comprarlo", f"{fmt(sa[2])} €", f"{fmt(sb[2])} €"))
    td = (f'<tr><th scope="col">Distrito más barato</th><th scope="col">{esc(na)}</th><th scope="col">{esc(nb)}</th></tr>'
        + fila("Para alquilar", f'<a href="../../{ka}/{slug(dra)}/">{esc(dra)}</a><br>{fmt(dprice(A, dra)[1] * M2A)} €/mes', f'<a href="../../{kb}/{slug(drb)}/">{esc(drb)}</a><br>{fmt(dprice(B, drb)[1] * M2A)} €/mes')
        + fila("Para comprar", f'<a href="../../{ka}/{slug(dva)}/">{esc(dva)}</a><br>{fmt(dprice(A, dva)[0] * M2A)} €', f'<a href="../../{kb}/{slug(dvb)}/">{esc(dvb)}</a><br>{fmt(dprice(B, dvb)[0] * M2A)} €')).replace("<td>", '<td style="white-space:normal">')  # nombres largos («Casetas - Garrapinillos - Monzalbarba»): que puedan partirse
    xr, pr = mas_barato(ra, rb, na, nb); xv, pv = mas_barato(va, vb, na, nb); xh, ph = mas_barato(A["hab"], B["hab"], na, nb)
    def fr(x, p, que, a="o"):  # «alquilar un piso, un 12 % más barato en Barcelona» (por debajo del 2 %, «casi igual»)
        return f"{que}, casi igual en las dos" if p < 2 else f"{que}, un {dec(p, 0)} % más barat{a} en {x}"
    resumen = f"{fr(xr, pr, 'Alquilar un piso')}; {fr(xh, ph, 'una habitación', 'a')}, y {fr(xv, pv, 'comprar')}."
    itp_txt = (f"En {na} y en {nb} el impuesto de compra de segunda mano es el mismo, un {pct(A['itp'])} %" if A["itp"] == B["itp"] else
        f"El impuesto de compra de segunda mano (ITP) es del {pct(A['itp'])} % {en_ccaa(A['ccaa'])} y del {pct(B['itp'])} % {en_ccaa(B['ccaa'])}")
    cq_html, cq_ld = faq([
        (f"¿Es más barato vivir en {na} o en {nb}?",
         f"En vivienda: {resumen[0].lower() + resumen[1:]} Un piso de {M2A} m² se alquila por unos {fmt(ra)} € al mes en {na} y {fmt(rb)} € en {nb}; comprarlo cuesta unos {fmt(va)} € y {fmt(vb)} €."),
        (f"¿Cuánto hay que ganar para vivir en {na} o en {nb}?",
         f"Para alquilar un piso de {M2A} m² sin apuros (alquiler ≤ 33 % del sueldo), unos {fmt(sa[0])} € netos al mes en {na} y {fmt(sb[0])} € en {nb}. "
         f"Para una habitación, unos {fmt(sa[1])} € y {fmt(sb[1])} €. Para comprarlo con una hipoteca del 80 % a {ANOS} años al 2,8 % (cuota ≤ 30 %), unos {fmt(sa[2])} € y {fmt(sb[2])} €."),
        (f"¿Dónde se pagan menos impuestos al comprar un piso, en {na} o en {nb}?",
         f"{itp_txt}. En el piso medio de {M2A} m² son unos {fmt(gastos(va, A)[0])} € en {na} y {fmt(gastos(vb, B)[0])} € en {nb}. En total hay que tener ahorrados unos {fmt(sa[3])} € y {fmt(sb[3])} € (entrada del 20 %, impuesto, notaría y tasación)."),
        (f"¿Cuál es el distrito más barato de {na} y de {nb}?",
         f"Para alquilar, {dra} en {na} (unos {fmt(dprice(A, dra)[1] * M2A)} € al mes por {M2A} m²) y {drb} en {nb} ({fmt(dprice(B, drb)[1] * M2A)} €). "
         f"Para comprar, {dva} en {na} (unos {fmt(dprice(A, dva)[0] * M2A)} €) y {dvb} en {nb} ({fmt(dprice(B, dvb)[0] * M2A)} €)."),
    ])
    mas = " · ".join(f'<a href="../{par(ka, k)}/">{esc(na)} o {esc(C[k]["n"])}</a>' for k in C if k not in (ka, kb)) + " · " + " · ".join(f'<a href="../{par(kb, k)}/">{esc(nb)} o {esc(C[k]["n"])}</a>' for k in C if k not in (ka, kb))
    body = f"""<h1>¿Vivir en {esc(na)} o en {esc(nb)}? Precio de la vivienda comparado ({esc(mes_txt)})</h1>
<p>{esc(resumen)} Estas son las cifras medias de las dos ciudades, para un piso de {M2A} m² o una habitación en piso compartido.</p>
<div class="card"><table class="cmp"><caption class="m" style="text-align:left;padding-bottom:6px">Precio medio de la vivienda en {esc(na)} y {esc(nb)} ({esc(mes_txt)})</caption>{tb}</table></div>
<h2 {H2}>¿Cuánto hay que ganar en cada una?</h2>
<div class="card"><table class="cmp"><caption class="m" style="text-align:left;padding-bottom:6px">Sueldo neto recomendado: alquiler ≤ 33 % (habitación con gastos), cuota de la hipoteca ≤ 30 % (80 % a {ANOS} años al 2,8 %)</caption>{ts}</table></div>
<h2 {H2}>El distrito más barato de cada una</h2>
<div class="card"><table class="cmp"><caption class="m" style="text-align:left;padding-bottom:6px">Para un piso de {M2A} m², entre los distritos con precio publicado</caption>{td}</table>
<p class="m">Cifras orientativas con precios medios: un piso concreto puede costar más o menos según su estado, planta y calle.</p></div>
{cq_html}
<a class="cta" href="../../">¿Has visto un piso en {esc(na)} o en {esc(nb)}? Analízalo gratis</a>
<div class="card m"><b>Más sobre {esc(na)}:</b> <a href="../../{ka}/">Precios por distritos</a> · <a href="../../{ka}/alquiler/">Alquiler</a> · <a href="../../{ka}/venta/">Comprar</a> · <a href="../../{ka}/habitacion/">Habitación</a></div>
<div class="card m"><b>Más sobre {esc(nb)}:</b> <a href="../../{kb}/">Precios por distritos</a> · <a href="../../{kb}/alquiler/">Alquiler</a> · <a href="../../{kb}/venta/">Comprar</a> · <a href="../../{kb}/habitacion/">Habitación</a></div>
<div class="card m"><b>Otras comparaciones:</b> {mas} · <a href="../">Todas</a> · <a href="../../precios/">Las 10 ciudades</a></div>"""
    os.makedirs(F("comparar", sl), exist_ok=True)
    open(F("comparar", sl, "index.html"), "w", encoding="utf-8").write(page(
        f"{na} o {nb}: ¿dónde es más barato vivir? (2026)",
        desc_corta(f"{na} o {nb}: un piso de {M2A} m² se alquila por ≈ {fmt(ra)} € frente a {fmt(rb)} €/mes, y una habitación por {fmt(A['hab'])} € frente a {fmt(B['hab'])} €.", " Compra, impuestos y sueldo."),
        f"comparar/{sl}/", body, [("Vivible", "../../"), ("Comparar ciudades", "../"), (f"{na} o {nb}", None)], cq_ld))
    urls.append(BASE + f"comparar/{sl}/")
lis = "".join(f'<p style="margin:0 0 6px"><b>{esc(c["n"])}:</b> ' + " · ".join(f'<a href="{par(k, k2)}/">{esc(c["n"])} o {esc(c2["n"])}</a>' for k2, c2 in C.items() if k2 != k) + "</p>" for k, c in C.items())
body = f"""<h1>Comparar dos ciudades para vivir: precio de la vivienda ({esc(mes_txt)})</h1>
<p>¿Dudas entre dos ciudades? Elige la pareja y verás, lado a lado, lo que cuesta alquilar, compartir piso o comprar, el impuesto de compra, el sueldo que hace falta y el distrito más barato de cada una.</p>
<div class="card m">{lis}</div>
<a class="cta" href="../">Analiza un piso concreto gratis</a>
<div class="card m"><b>Más guías:</b> <a href="../precios/">Las 10 ciudades en una tabla</a> · <a href="../barrios-baratos/">Barrios más baratos</a> · <a href="../barrios-caros/">Barrios más caros</a> · <a href="../sueldo/">Qué piso puedo pagar con mi sueldo</a></div>"""
open(F("comparar", "index.html"), "w", encoding="utf-8").write(page(
    "Comparar ciudades para vivir: precio de la vivienda (2026)",
    f"Compara dos de estas 10 ciudades: alquiler, habitación, compra, impuestos y sueldo necesario, lado a lado. {len(pares)} comparaciones.",
    "comparar/", body, [("Vivible", "../"), ("Comparar ciudades", None)]))
urls.insert(8, BASE + "comparar/")

# ---------- buscador de barrios (barrios/): «en qué distrito está Russafa», «barrios de Madrid», «precio alquiler <barrio>»;
# cada barrio oficial de BAR con su distrito y el precio medio del distrito (idealista no publica por barrio; ≈ = estimado como en el distrito)
assert "barrios" not in C
fil_b, n_b = [], {}
for ck, BB in BAR.items():
    c = C[ck]; n_b[ck] = sum(map(len, BB.values()))
    for d, bs in BB.items():
        s_, r_, es_, er_ = dprice(c, d)
        for b in bs: fil_b.append((slug(b), b, d, ck, c["n"], s_, r_, es_, er_))
fil_b.sort(key=lambda x: (list(BAR).index(x[3]), x[0]))
def fila_barrio(x):
    _, b, d, ck, cn, s_, r_, es_, er_ = x
    q = slug(f"{b} {d} {cn}").replace("-", " ")
    return (f'<tr data-q="{esc(q)}"><td style="white-space:normal"><b>{esc(b)}</b><br><span class="m">{esc(cn)}</span></td>'
            f'<td style="white-space:normal"><a href="../{ck}/{slug(d)}/">{esc(d)}</a></td>'
            f'<td>{"≈ " if er_ else ""}{dec(r_)} €<br><span class="m">{"≈ " if es_ else ""}{fmt(s_)} €</span></td></tr>')
tbb = "".join(fila_barrio(x) for x in fil_b)
nbt = len(fil_b)
ciu_b = " y ".join([", ".join(C[k]["n"] for k in list(BAR)[:-1]), C[list(BAR)[-1]]["n"]])
br_html, br_ld = faq([
    ("¿Cuántos barrios hay en " + ciu_b + "?",
     "; ".join(f"{C[k]['n']} tiene {n_b[k]} barrios oficiales en {len(BB)} distritos" for k, BB in BAR.items())
     + (". En Valencia no entran los 17 barrios de los Pobles del Nord, de l'Oest y del Sud, que no tienen precio publicado." if "valencia" in BAR else ".")),
    ("¿Qué diferencia hay entre barrio y distrito?",
     "El distrito es la división grande del ayuntamiento y cada uno agrupa varios barrios. Los portales publican el precio medio por distrito, así que para saber cuánto cuesta vivir en un barrio hay que mirar el de su distrito."),
    ("¿Por qué el precio es el del distrito y no el del barrio?",
     f"Porque idealista publica el precio medio por distrito ({mes_txt}). Dentro de un mismo distrito puede haber calles más caras y más baratas; para un piso concreto, pega su anuncio en Vivible y lo compara con su zona."),
    ("¿Qué hago si mi barrio no sale?",
     "Puede que el anuncio use un nombre popular (por ejemplo, la calle o una urbanización). Escribe la dirección en Vivible y te dice el distrito y el precio de la zona."),
])
body = f"""<h1>¿En qué distrito está mi barrio? Barrios de {esc(ciu_b)}</h1>
<p>Los anuncios suelen decir el barrio, pero los precios se publican por distrito. Busca el barrio y verás su distrito y lo que cuesta vivir allí: alquiler medio por m² al mes y precio de compra por m² (idealista, {esc(mes_txt)}).</p>
<div class="card"><form id="bq" onsubmit="return false"><label class="m" for="bqi"><b style="color:#1d2321">Busca tu barrio</b></label>
<input id="bqi" type="search" placeholder="Por ejemplo: Russafa, Pacífico, Poblenou" autocomplete="off" enterkeyhint="search"></form>
<p id="bqn" class="m" aria-live="polite" style="margin:8px 0 0">{nbt} barrios</p></div>
<div class="card"><table class="cmp" id="bqt"><caption class="m" style="text-align:left;padding-bottom:6px">Barrio, su distrito y el precio medio del distrito: alquiler por m² al mes y, debajo, compra por m². ≈ es estimado.</caption><tr><th scope="col">Barrio</th><th scope="col">Distrito</th><th scope="col">Alquiler / compra</th></tr>{tbb}</table>
<p id="bq0" class="m" hidden>No encuentro ese barrio. <a href="../">Escribe la dirección en Vivible</a> y te digo su distrito y su precio.</p></div>
<style>#bqi{{display:block;width:100%;box-sizing:border-box;margin-top:6px;font:16px Inter,system-ui,sans-serif;padding:10px;min-height:44px;border:1px solid #d6d0c4;border-radius:10px;background:#fff;color:#1d2321}}</style>
<script>(function(){{var i=document.getElementById("bqi"),rs=[].slice.call(document.querySelectorAll("#bqt tr[data-q]")),n=document.getElementById("bqn"),z=document.getElementById("bq0");
function nm(s){{return s.toLowerCase().normalize("NFD").replace(/[\\u0300-\\u036f]/g,"").replace(/[^a-z0-9]+/g," ").trim()}}
function f(){{var q=nm(i.value),k=0;rs.forEach(function(r){{var v=!q||(" "+r.getAttribute("data-q")).indexOf(" "+q)>=0||r.getAttribute("data-q").indexOf(q)>=0;r.hidden=!v;if(v)k++}});n.textContent=k+(k==1?" barrio":" barrios");z.hidden=k>0}}
i.addEventListener("input",f);var p=new URLSearchParams(location.search).get("q");if(p){{i.value=p;f()}}}})();</script>
{br_html}
<a class="cta" href="../">¿Has visto un piso? Pega el anuncio y te decimos si está bien de precio</a>
<div class="card m"><b>Barrios por ciudad:</b> """ + " · ".join(f'<a href="../{k}/">Distritos y barrios de {esc(C[k]["n"])}</a>' for k in BAR) + """ · <a href="../barrios-baratos/">Barrios más baratos</a> · <a href="../barrios-caros/">Barrios más caros</a> · <a href="../precios/">Comparar las 10 ciudades</a></div>"""
os.makedirs(F("barrios"), exist_ok=True)
open(F("barrios", "index.html"), "w", encoding="utf-8").write(page(
    f"¿En qué distrito está mi barrio? {ciu_b} (2026)",
    desc_corta(f"Busca entre los {nbt} barrios de {ciu_b}: en qué distrito está cada uno y cuánto cuesta alquilar y comprar allí.", " Gratis."),
    "barrios/", body, [("Vivible", "../"), ("Barrios", None)], br_ld))
urls.insert(9, BASE + "barrios/")

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
