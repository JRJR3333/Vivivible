"""Genera la web de Vivible: index.html, páginas por ciudad y distrito, sitemap.xml y robots.txt.
Uso (desde la raíz del repositorio):  python3 fuente/build.py
"""
import json, math, os, re, unicodedata, html
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
    links = "".join(f'<a href="{pre}{k}/">Vivir en {esc(c["n"])}</a>' for k, c in C.items()) + f'<a href="{pre}precios/">Comparar ciudades</a><a href="{pre}sueldo/">Qué piso puedo pagar</a><a href="{pre}hipoteca/">Cuota de la hipoteca</a><a href="{pre}gastos-de-alquiler/">Dinero para alquilar</a><a href="{pre}gastos-de-compra/">Gastos de comprar</a><a href="{pre}comparar/">Ciudad o ciudad</a><a href="{pre}barrios/">¿En qué distrito está mi barrio?</a><a href="{pre}barrios-baratos/">Barrios más baratos</a><a href="{pre}barrios-caros/">Barrios más caros</a><a href="{pre}rentabilidad/">Rentabilidad del alquiler</a><a href="{pre}visitar-un-piso/">Qué mirar al visitar un piso</a><a href="{pre}papeles-para-alquilar/">Papeles para alquilar</a><a href="{pre}contrato-de-alquiler/">Contrato de alquiler</a><a href="{pre}devolver-fianza/">Devolver la fianza</a><a href="{pre}dejar-el-piso/">Carta para dejar el piso</a><a href="{pre}reparaciones-alquiler/">Quién paga las reparaciones</a><a href="{pre}repartir-alquiler/">Repartir el alquiler</a><a href="{pre}independizarse/">Cuánto cuesta independizarse</a><a href="{pre}mudanza/">Lista para la mudanza</a><a href="{pre}ahorrar-para-comprar/">Ahorrar para comprar</a><a href="{pre}pasos-para-comprar/">Pasos para comprar</a><a href="{pre}vender-un-piso/">Vender un piso: IRPF</a><a href="{pre}como-calculamos/">Cómo calculamos</a>'
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
.cmp td+td,.cmp th+th{white-space:nowrap}@media(max-width:480px){.cmp{font-size:13px}.cmp td,.cmp th{padding:7px 2px}.card:has(.cmp){padding:14px 10px}}.faq h2{font:700 21px/1.2 Fraunces,Georgia,serif;margin:0 0 4px}.faq h3{font-size:16px;margin:14px 0 2px}.faq p{margin:0}footer.m a{display:inline-block;min-height:44px;line-height:44px}
@media(max-width:480px){.g{grid-template-columns:1fr}h1{font-size:26px}}"""

def tit_distrito(d, cn):
    t = f"{d}, {cn}: precio por m² y alquiler 2026 | Vivible"
    if len(t) > 65: t = t.replace(" | Vivible", "")
    if len(t) > 65: t = t.replace(" y alquiler", "")
    if len(t) > 65: t = t.replace(" 2026", "")
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
<footer class="m" style="margin-top:28px">Datos: precios medios de idealista ({esc(mes_txt)}); habitaciones: precio medio de la ciudad. Estimaciones orientativas, no tasaciones oficiales: <a href="{"../" * path.count("/")}como-calculamos/">cómo calculamos</a>. Hecho por <a href="{"../" * path.count("/")}">Vivible</a>.</footer></div></body></html>"""

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
<div class="card m"><b>¿Vas a comprar?</b> <a href="venta/">Precio de la vivienda en {esc(c["n"])} por tamaño</a> · <a href="gastos-de-compra/">Gastos e impuestos de comprar un piso en {esc(c["n"])}</a> · <a href="sueldo-para-comprar/">Cuánto hay que ganar para comprar</a> · <a href="comprar-con-presupuesto/">Qué piso puedo comprar con mi presupuesto</a> · <a href="../pasos-para-comprar/">Pasos para comprar un piso</a></div>
<div class="card m"><b>¿Vas a alquilar?</b> <a href="alquiler/">Precio del alquiler en {esc(c["n"])} por distritos</a> · <a href="sueldo-para-alquilar/">Cuánto hay que ganar para alquilar en {esc(c["n"])}</a> · <a href="alquilar-con-presupuesto/">Qué piso puedo alquilar con mi presupuesto</a> · <a href="../papeles-para-alquilar/">Qué papeles piden para alquilar</a> · <a href="../contrato-de-alquiler/">Cuánto dura el contrato</a> · <a href="../devolver-fianza/">Cuándo te devuelven la fianza</a> · <a href="../reparaciones-alquiler/">Quién paga las reparaciones</a> · <a href="../mudanza/">Lista para la mudanza</a></div>
<div class="card m"><b>¿Buscas habitación?</b> <a href="habitacion/">Precio de una habitación en {esc(c["n"])} por distritos</a> · <a href="../repartir-alquiler/">Cómo repartir el alquiler</a></div>
<div class="card m"><b>¿Dudas?</b> <a href="comprar-o-alquilar/">Comprar o alquilar en {esc(c["n"])}: hipoteca frente a alquiler</a> · <a href="../visitar-un-piso/">Qué mirar al visitar un piso</a></div>
<div class="card m"><b>Otras ciudades:</b> {" · ".join(f'<a href="../{k2}/">{esc(c2["n"])}</a>' for k2, c2 in C.items() if k2 != ck)} · <a href="../precios/">Comparar las 10 ciudades</a></div>
<div class="card m"><b>¿Dudas entre {esc(c["n"])} y otra ciudad?</b> {" · ".join(f'<a href="../comparar/{par(ck, k2)}/">{esc(c["n"])} o {esc(c2["n"])}</a>' for k2, c2 in C.items() if k2 != ck)}</div>"""
    if ck in BAR:  # «en qué distrito está <barrio>»: muchos anuncios dicen el barrio y no el distrito
        BB = BAR[ck]
        body = body.replace("\n" + fq_html, "\n" + f'<div class="card"><h2 style="font:700 21px/1.2 Fraunces,Georgia,serif;margin:0 0 4px">Barrios de {esc(c["n"])} por distrito</h2><p class="m" style="margin:0 0 6px">Los anuncios suelen decir el barrio: búscalo aquí para saber en qué distrito está, o usa el <a href="../barrios/">buscador de barrios</a>.</p><table>'
            + "".join(f'<tr><td><a href="{slug(d)}/">{esc(d)}</a></td><td style="text-align:left">{esc(("; " if coma(BB[d]) else ", ").join(BB[d]))}</td></tr>' for d, *_ in rows) + "</table></div>\n" + fq_html, 1)
    open(F(ck, "index.html"), "w", encoding="utf-8").write(page(
        (lambda t: t if len(t) <= 65 else t.replace(" | Vivible", ""))(f"Vivir en {c['n']}: precio de la vivienda por distritos (2026) | Vivible"),
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
            bar_html = f'<div class="card"><b>Barrios de {esc(d)}</b><p>{esc(d)} tiene {len(bs)} barrios: {esc(y_lista(bs))}. Si el anuncio dice uno de ellos, el piso está en este distrito. ¿No sale el tuyo? Usa el <a href="../../barrios/">buscador de barrios</a>.</p></div>\n'
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
<div class="card m"><b>¿Vas a comprar?</b> <a href="../venta/">Precio de la vivienda por tamaño</a> · <a href="../gastos-de-compra/">Gastos e impuestos de comprar un piso en {esc(c["n"])}</a> · <a href="../sueldo-para-comprar/">Cuánto hay que ganar para comprar</a> · <a href="../../pasos-para-comprar/">Pasos para comprar un piso</a></div>
<div class="card m"><b>¿Vas a alquilar?</b> <a href="../alquiler/">Precio del alquiler en {esc(c["n"])}</a> · <a href="../sueldo-para-alquilar/">Cuánto hay que ganar para alquilar en {esc(c["n"])}</a> · <a href="../../papeles-para-alquilar/">Qué papeles piden para alquilar</a> · <a href="../../contrato-de-alquiler/">Cuánto dura el contrato</a> · <a href="../../devolver-fianza/">Cuándo te devuelven la fianza</a> · <a href="../../reparaciones-alquiler/">Quién paga las reparaciones</a> · <a href="../../mudanza/">Lista para la mudanza</a></div>
<div class="card m"><b>¿Buscas habitación?</b> <a href="../habitacion/">Precio de una habitación en {esc(c["n"])} por distritos</a> · <a href="../../repartir-alquiler/">Cómo repartir el alquiler</a></div>
<div class="card m"><b>¿Dudas?</b> <a href="../comprar-o-alquilar/">Comprar o alquilar en {esc(c["n"])}: hipoteca frente a alquiler</a> · <a href="../../visitar-un-piso/">Qué mirar al visitar un piso</a></div>
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
<div class="card m"><b>Precios en {esc(c["n"])}:</b> <a href="../">Por distritos</a> · <a href="../venta/">Precio por tamaño</a> · <a href="../sueldo-para-comprar/">Sueldo para comprar</a> · <a href="../sueldo-para-alquilar/">Sueldo para alquilar</a> · <a href="../../hipoteca/">Cuota de la hipoteca</a> · <a href="../../gastos-de-compra/">Calculadora de gastos</a> · <a href="../../pasos-para-comprar/">Pasos para comprar</a> · <a href="../../precios/">Comparar las 10 ciudades</a></div>"""
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
<div class="card m"><b>Más sobre {esc(c["n"])}:</b> <a href="../alquilar-con-presupuesto/">Qué alquilar con tu presupuesto</a> · <a href="../">Precios por distritos</a> · <a href="../alquiler/">Alquiler por tamaño</a> · <a href="../gastos-de-compra/">Gastos de comprar</a> · <a href="../comprar-o-alquilar/">Comprar o alquilar</a> · <a href="../habitacion/">Habitación</a> · <a href="../../gastos-de-alquiler/">Dinero para entrar de alquiler</a> · <a href="../../sueldo/">Qué piso puedo pagar con mi sueldo</a> · <a href="../../hipoteca/">Cuota de la hipoteca</a> · <a href="../../precios/">Comparar las 10 ciudades</a></div>"""
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
<div class="card m"><b>Más sobre {esc(c["n"])}:</b> <a href="../alquilar-con-presupuesto/">Qué alquilar con tu presupuesto</a> · <a href="../">Precios por distritos</a> · <a href="../venta/">Precio de compra</a> · <a href="../sueldo-para-alquilar/">Sueldo para alquilar</a> · <a href="../habitacion/">Habitación</a> · <a href="../comprar-o-alquilar/">Comprar o alquilar</a> · <a href="../../barrios-baratos/">Barrios más baratos de España</a> · <a href="../../barrios-caros/">Barrios más caros</a> · <a href="../../precios/">Comparar las 10 ciudades</a></div>"""
    os.makedirs(F(ck, "alquiler"), exist_ok=True)
    open(F(ck, "alquiler", "index.html"), "w", encoding="utf-8").write(page(
        f"Precio del alquiler en {c['n']} por distritos (2026)",
        desc_corta(f"Alquiler en {c['n']}: {dec(r)} €/m² al mes. Estudio ≈ {fmt(r * 40)} €, 2 dormitorios ≈ {fmt(r * M2A)} € y 3 ≈ {fmt(r * 90)} €.", " Por distritos, del más barato al más caro."),
        f"{ck}/alquiler/", body, [("Vivible", "../../"), (c["n"], "../"), ("Alquiler", None)], aq_ld))
    urls.append(BASE + f"{ck}/alquiler/")

# ---------- alquilar con tu presupuesto (<ciudad>/alquilar-con-presupuesto/): «qué puedo alquilar en <ciudad> con 1.000 euros»,
# «cuántos metros puedo alquilar con 800 €»: metros que da cada presupuesto con el €/m² de cada distrito (las mismas cifras que alquiler/)
PRES, M2D = [600, 800, 1000, 1200, 1500], 60  # presupuestos al mes y metros mínimos que se cuentan como «piso de 2 dormitorios»
for ck, c in C.items():
    assert "alquilar-con-presupuesto" not in [slug(d) for d in c["d"]]
    rows = sorted(((d, dprice(c, d)[1], dprice(c, d)[3]) for d in c["d"]), key=lambda x: x[1])
    r, hab = c["alquiler"], c["hab"]
    bar, car = rows[0], rows[-1]
    tr = "".join(f'<tr><td><a href="../{slug(d)}/">{esc(d)}</a>{"*" if e else ""}</td>' + "".join(f"<td>{round(p / x)}</td>" for p in PRES) + "</tr>" for d, x, e in rows)
    nota = '<p class="m">* Alquiler estimado a partir del precio de venta del distrito: idealista no publica ese dato.</p>' if any(e for *_, e in rows) else ""
    def caben(p): return [d for d, x, _ in rows if p / x >= M2D]
    def resp(p):
        ds = caben(p)
        t = (f"Con {fmt(p)} € al mes, en {c['n']} da de media para unos {round(p / r)} m²: desde unos {round(p / car[1])} m² en {car[0]} hasta unos {round(p / bar[1])} m² en {bar[0]}. ")
        if len(ds) == len(rows): t += f"Para un piso de 2 dormitorios (unos {M2D} m²) llega en todos los distritos."
        elif ds: t += f"Para un piso de 2 dormitorios (unos {M2D} m²) llega en {len(ds)} de los {len(rows)} distritos: {y_lista(ds) if len(ds) <= 6 else ('; ' if coma(ds[:6]) else ', ').join(ds[:6]) + f' y {len(ds) - 6} más'}."
        else: t += f"No llega para un piso de 2 dormitorios (unos {M2D} m²) en ningún distrito" + (f"; una habitación (unos {fmt(hab)} €) sí." if hab <= p else ".")
        return t + f" Para pagarlo sin apuros conviene ganar unos {fmt(p / ESF)} € netos."
    pq_html, pq_ld = faq([(f"¿Qué piso puedo alquilar en {c['n']} con {fmt(p)} €?", resp(p)) for p in PRES[1:4]] + [
        (f"¿Cuánto hace falta para alquilar un piso de 2 dormitorios en {c['n']}?",
         f"Un piso de {M2D} m² cuesta unos {fmt(bar[1] * M2D)} € al mes en {bar[0]}, el distrito más barato, y unos {fmt(car[1] * M2D)} € en {car[0]}, el más caro. "
         f"Si no llegas, una habitación en piso compartido cuesta de media unos {fmt(hab)} € al mes."),
    ])
    D = json.dumps([[d, round(x, 2), slug(d)] for d, x, _ in rows], ensure_ascii=False).replace("</", "<\\/")
    p0 = 1000
    body = f"""<h1>¿Qué piso puedo alquilar en {esc(c["n"])} con mi presupuesto? (2026)</h1>
<p>Con el alquiler medio de cada distrito ({dec(r)} €/m² al mes en toda la ciudad, {esc(c["mes"])}), esto es lo que da tu dinero en {esc(c["n"])}: cuántos metros cuadrados puedes alquilar en cada distrito con 600, 800, 1.000, 1.200 o 1.500 € al mes. Escribe tu presupuesto para verlo con tu cifra.</p>
<div class="card"><form id="pres" onsubmit="return false"><label class="m"><b>Tu presupuesto al mes (€)</b><input id="pv" type="number" inputmode="numeric" min="100" step="50" value="{p0}"></label></form>
<p id="pr" aria-live="polite" style="margin:10px 0 0">{esc(resp(p0))}</p></div>
<div class="card"><table class="cmp"><caption class="m" style="text-align:left;padding-bottom:6px">Metros cuadrados que puedes alquilar en cada distrito de {esc(c["n"])} según lo que pagues al mes, del distrito más barato al más caro</caption><tr><th scope="col">Distrito</th>""" + "".join(f'<th scope="col">{fmt(p)} €</th>' for p in PRES) + f"""</tr>{tr}</table>{nota}
<p class="m">Metros = presupuesto ÷ alquiler medio por m² del distrito. Un piso de 2 dormitorios suele tener {M2D}–70 m²; un estudio, unos 40. Un piso concreto puede costar más o menos según su estado, planta y calle.</p></div>
<div class="g" style="margin-top:16px"><div class="k"><small>Habitación en {esc(c["n"])}</small><b>≈ {fmt(hab)} €/mes</b><small><a href="../habitacion/">Por distritos</a></small></div>
<div class="k"><small>Piso de {M2D} m² más barato</small><b>≈ {fmt(bar[1] * M2D)} €/mes</b><small>En {esc(bar[0])}</small></div></div>
{pq_html}
<a class="cta" href="../../#c={ck}&op=alquiler">¿Has visto un piso de alquiler? Comprueba si su precio es justo</a>
<div class="card m"><b>Más sobre {esc(c["n"])}:</b> <a href="../alquiler/">Alquiler por tamaño</a> · <a href="../sueldo-para-alquilar/">Sueldo para alquilar</a> · <a href="../habitacion/">Habitación</a> · <a href="../">Precios por distritos</a> · <a href="../../gastos-de-alquiler/">Dinero para entrar de alquiler</a> · <a href="../../sueldo/">Qué piso puedo pagar con mi sueldo</a> · <a href="../../barrios-baratos/">Barrios más baratos de España</a></div>
<style>#pres input{{display:block;width:100%;box-sizing:border-box;margin-top:4px;font:16px Inter,system-ui,sans-serif;padding:10px;min-height:44px;border:1px solid #d6d0c4;border-radius:10px;background:#fff;color:#1d2321}}#pres label{{display:block}}</style>
<script>(function(){{var D={D},R={r},H={hab},M={M2D},E={ESF},N="{c['n']}",i=document.getElementById("pv"),o=document.getElementById("pr"),f=function(n){{return String(Math.round(n)).replace(/\\B(?=(\\d{{3}})+(?!\\d))/g,".")}};
function y(a){{return a.length<2?a.join(""):a.slice(0,-1).join(a.some(function(s){{return s.indexOf(",")>=0}})?"; ":", ")+" y "+a[a.length-1]}}
function c(){{var p=+i.value;if(!(p>=100&&p<=100000)){{o.textContent="Escribe una cantidad al mes, por ejemplo 900.";return}}var b=D[0],z=D[D.length-1],ds=D.filter(function(x){{return p/x[1]>=M}}).map(function(x){{return x[0]}});
var t="Con "+f(p)+" € al mes, en "+N+" da de media para unos "+f(p/R)+" m²: desde unos "+f(p/z[1])+" m² en "+z[0]+" hasta unos "+f(p/b[1])+" m² en "+b[0]+". ";
t+=ds.length==D.length?"Para un piso de 2 dormitorios (unos "+M+" m²) llega en todos los distritos.":ds.length?"Para un piso de 2 dormitorios (unos "+M+" m²) llega en "+ds.length+" de los "+D.length+" distritos: "+(ds.length>6?ds.slice(0,6).join(ds.slice(0,6).some(function(s){{return s.indexOf(",")>=0}})?"; ":", ")+" y "+(ds.length-6)+" más":y(ds))+".":"No llega para un piso de 2 dormitorios (unos "+M+" m²) en ningún distrito"+(H<=p?"; una habitación (unos "+f(H)+" €) sí.":".");
o.textContent=t+" Para pagarlo sin apuros conviene ganar unos "+f(p/E)+" € netos."}}
i.addEventListener("input",c);c()}})()</script>"""
    os.makedirs(F(ck, "alquilar-con-presupuesto"), exist_ok=True)
    open(F(ck, "alquilar-con-presupuesto", "index.html"), "w", encoding="utf-8").write(page(
        f"¿Qué piso puedo alquilar en {c['n']} con mi presupuesto? (2026)",
        desc_corta(f"Con 1.000 € al mes en {c['n']}: unos {round(1000 / r)} m² de media, hasta {round(1000 / bar[1])} m² en {bar[0]}. Metros por distrito con 600 a 1.500 €.", " Calculadora."),
        f"{ck}/alquilar-con-presupuesto/", body, [("Vivible", "../../"), (c["n"], "../"), ("Alquilar con tu presupuesto", None)], pq_ld))
    urls.append(BASE + f"{ck}/alquilar-con-presupuesto/")

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
<div class="card m"><b>Más sobre {esc(c["n"])}:</b> <a href="../comprar-con-presupuesto/">Qué comprar con tu presupuesto</a> · <a href="../">Precios por distritos</a> · <a href="../../cuanto-vale-mi-piso/?c={ck}">¿Cuánto vale mi piso?</a> · <a href="../../precio-metro-cuadrado/?c={ck}">Precio por m²</a> · <a href="../gastos-de-compra/">Gastos de comprar</a> · <a href="../sueldo-para-comprar/">Sueldo para comprar</a> · <a href="../comprar-o-alquilar/">Comprar o alquilar</a> · <a href="../alquiler/">Alquiler por tamaño</a> · <a href="../../barrios-baratos/">Barrios más baratos de España</a> · <a href="../../barrios-caros/">Barrios más caros</a> · <a href="../../precios/">Comparar las 10 ciudades</a></div>"""
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
<div class="card m"><b>Más sobre {esc(c["n"])}:</b> <a href="../">Precios por distritos</a> · <a href="../sueldo-para-alquilar/">Sueldo para alquilar</a> · <a href="../comprar-o-alquilar/">Comprar o alquilar</a> · <a href="../../repartir-alquiler/">Cómo repartir el alquiler</a> · <a href="../../independizarse/">Cuánto cuesta independizarse</a> · <a href="../../precios/">Comparar las 10 ciudades</a></div>"""
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
<div class="card m"><b>Más sobre {esc(c["n"])}:</b> <a href="../comprar-con-presupuesto/">Qué comprar con tu presupuesto</a> · <a href="../">Precios por distritos</a> · <a href="../venta/">Precio de compra</a> · <a href="../gastos-de-compra/">Gastos de comprar</a> · <a href="../sueldo-para-comprar/">Sueldo para comprar</a> · <a href="../sueldo-para-alquilar/">Sueldo para alquilar</a> · <a href="../../hipoteca/">Cuota de la hipoteca</a> · <a href="../../rentabilidad/">Rentabilidad del alquiler en 10 ciudades</a></div>"""
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
<div class="card m"><b>Más sobre {esc(c["n"])}:</b> <a href="../comprar-con-presupuesto/">Qué comprar con tu presupuesto</a> · <a href="../">Precios por distritos</a> · <a href="../venta/">Precio de compra</a> · <a href="../gastos-de-compra/">Gastos de comprar</a> · <a href="../comprar-o-alquilar/">Comprar o alquilar</a> · <a href="../sueldo-para-alquilar/">Sueldo para alquilar</a> · <a href="../../sueldo/">Qué piso puedo pagar con mi sueldo</a> · <a href="../../hipoteca/">Cuota de la hipoteca</a> · <a href="../../ahorrar-para-comprar/">Cuánto tardo en ahorrar</a> · <a href="../../precios/">Comparar las 10 ciudades</a></div>"""
    os.makedirs(F(ck, "sueldo-para-comprar"), exist_ok=True)
    open(F(ck, "sueldo-para-comprar", "index.html"), "w", encoding="utf-8").write(page(
        f"Cuánto hay que ganar para comprar un piso en {c['n']} (2026)",
        desc_corta(f"Sueldo neto para comprar en {c['n']}: piso medio ≈ {fmt(med)} €, hipoteca ≈ {fmt(cm)} €/mes, ganar ≈ {fmt(sc)} € y ahorrar {fmt(ah)} €.", " Por distritos."),
        f"{ck}/sueldo-para-comprar/", body, [("Vivible", "../../"), (c["n"], "../"), ("Sueldo para comprar", None)], pq_ld))
    urls.append(BASE + f"{ck}/sueldo-para-comprar/")

# ---------- comprar con tu presupuesto (<ciudad>/comprar-con-presupuesto/): «qué piso puedo comprar en <ciudad> con 200.000 euros»,
# «cuántos metros puedo comprar con 150.000 €»: metros por distrito con el €/m² de venta (las mismas cifras que venta/), ahorros con gastos()
# y cuota con cuota() (80 %, 30 años, 2,8 %; cuota ≤ 30 % del sueldo, como sueldo-para-comprar/)
PRESC = [100000, 150000, 200000, 300000, 400000]
for ck, c in C.items():
    assert "comprar-con-presupuesto" not in [slug(d) for d in c["d"]]
    rows = sorted(((d, dprice(c, d)[0], dprice(c, d)[2]) for d in c["d"]), key=lambda x: x[1])
    v = c["venta"]
    bar, car = rows[0], rows[-1]
    tr = "".join(f'<tr><td><a href="../{slug(d)}/">{esc(d)}</a>{"*" if e else ""}</td>' + "".join(f"<td>{round(p / x)}</td>" for p in PRESC) + "</tr>" for d, x, e in rows)
    nota = '<p class="m">* Precio de venta estimado a partir del alquiler del distrito: idealista no publica ese dato.</p>' if any(e for *_, e in rows) else ""
    def caben(p): return [d for d, x, _ in rows if p / x >= M2D]
    def resp(p):
        ds = caben(p)
        t = f"Con {fmt(p)} €, en {c['n']} da de media para unos {round(p / v)} m²: desde unos {round(p / car[1])} m² en {car[0]} hasta unos {round(p / bar[1])} m² en {bar[0]}. "
        if len(ds) == len(rows): t += f"Para un piso de 2 dormitorios (unos {M2D} m²) llega en todos los distritos."
        elif ds: t += f"Para un piso de 2 dormitorios (unos {M2D} m²) llega en {len(ds)} de los {len(rows)} distritos: {y_lista(ds) if len(ds) <= 6 else ('; ' if coma(ds[:6]) else ', ').join(ds[:6]) + f' y {len(ds) - 6} más'}."
        else: t += f"No llega para un piso de 2 dormitorios (unos {M2D} m²) en ningún distrito."
        return t + f" Necesitas unos {fmt(gastos(p, c)[2])} € ahorrados (entrada del 20 %, impuesto y gastos) y la hipoteca saldría por unos {fmt(cuota(p))} € al mes: conviene ganar unos {fmt(cuota(p) / ESC)} € netos."
    cq_html, cq_ld = faq([(f"¿Qué piso puedo comprar en {c['n']} con {fmt(p)} €?", resp(p)) for p in PRESC[1:4]] + [
        (f"¿Cuánto cuesta un piso de 2 dormitorios en {c['n']}?",
         f"Un piso de {M2D} m² cuesta unos {fmt(bar[1] * M2D)} € en {bar[0]}, el distrito más barato, y unos {fmt(car[1] * M2D)} € en {car[0]}, el más caro. "
         f"Al precio hay que sumarle el impuesto de compra ({pct(c['itp'])} % de ITP {en_ccaa(c['ccaa'])} si es de segunda mano) y los gastos de notaría, registro y gestoría."),
    ])
    D = json.dumps([[d, round(x)] for d, x, _ in rows], ensure_ascii=False).replace("</", "<\\/")
    p0 = 200000
    body = f"""<h1>¿Qué piso puedo comprar en {esc(c["n"])} con mi presupuesto? (2026)</h1>
<p>Con el precio medio de venta de cada distrito ({fmt(v)} €/m² en toda la ciudad, {esc(c["mes"])}), esto es lo que da tu dinero en {esc(c["n"])}: cuántos metros cuadrados puedes comprar en cada distrito con 100.000, 150.000, 200.000, 300.000 o 400.000 €, y cuánto tendrías que tener ahorrado y pagar de hipoteca. Escribe tu presupuesto para verlo con tu cifra.</p>
<div class="card"><form id="pres" onsubmit="return false"><label class="m"><b>Precio máximo del piso (€)</b><input id="pv" type="number" inputmode="numeric" min="10000" step="5000" value="{p0}"></label></form>
<p id="pr" aria-live="polite" style="margin:10px 0 0">{esc(resp(p0))}</p></div>
<div class="card"><table class="cmp"><caption class="m" style="text-align:left;padding-bottom:6px">Metros cuadrados que puedes comprar en cada distrito de {esc(c["n"])} según tu presupuesto, del distrito más barato al más caro</caption><tr><th scope="col">Distrito</th>""" + "".join(f'<th scope="col">{fmt(p / 1000)}<br>mil €</th>' for p in PRESC) + f"""</tr>{tr}</table>{nota}
<p class="m">Metros = presupuesto ÷ precio medio por m² del distrito. Un piso de 2 dormitorios suele tener {M2D}–70 m²; un estudio, unos 40. Un piso concreto puede costar más o menos según su estado, planta y calle.</p></div>
<div class="card"><table class="cmp"><caption class="m" style="text-align:left;padding-bottom:6px">Ahorros, hipoteca (80 % a {ANOS} años al 2,8 %) y sueldo neto recomendado (cuota ≤ 30 %) según el precio del piso de segunda mano</caption><tr><th scope="col">Precio</th><th scope="col">Ahorros</th><th scope="col">Hipoteca</th><th scope="col">Sueldo neto</th></tr>""" + "".join(f"<tr><td>{fmt(p)} €</td><td>{fmt(gastos(p, c)[2])} €</td><td>{fmt(cuota(p))} €/mes</td><td><b>{fmt(cuota(p) / ESC)} €</b></td></tr>" for p in PRESC) + f"""</table>
<p class="m">Ahorros: el 20 % que no financia el banco, el {pct(c["itp"])} % de ITP {esc(en_ccaa(c["ccaa"]))} y notaría, registro, gestoría y tasación. Cuota sin seguros.</p></div>
{cq_html}
<a class="cta" href="../../#c={ck}&op=venta">¿Has visto un piso en venta? Comprueba si su precio es justo</a>
<div class="card m"><b>Más sobre {esc(c["n"])}:</b> <a href="../venta/">Precio de compra por tamaño</a> · <a href="../sueldo-para-comprar/">Sueldo para comprar</a> · <a href="../gastos-de-compra/">Gastos de comprar</a> · <a href="../comprar-o-alquilar/">Comprar o alquilar</a> · <a href="../alquilar-con-presupuesto/">Qué alquilar con tu presupuesto</a> · <a href="../">Precios por distritos</a> · <a href="../../hipoteca/">Cuota de la hipoteca</a> · <a href="../../ahorrar-para-comprar/">Cuánto tardo en ahorrar</a> · <a href="../../barrios-baratos/">Barrios más baratos de España</a></div>
<style>#pres input{{display:block;width:100%;box-sizing:border-box;margin-top:4px;font:16px Inter,system-ui,sans-serif;padding:10px;min-height:44px;border:1px solid #d6d0c4;border-radius:10px;background:#fff;color:#1d2321}}#pres label{{display:block}}</style>
<script>(function(){{var D={D},V={v},M={M2D},E={ESC},T={c["itp"]},N="{c['n']}",i=document.getElementById("pv"),o=document.getElementById("pr"),f=function(n){{return String(Math.round(n)).replace(/\\B(?=(\\d{{3}})+(?!\\d))/g,".")}};
function q(p){{var k={TIN}/12;return p*.8*k/(1-Math.pow(1+k,-{ANOS * 12}))}}
function y(a){{return a.length<2?a.join(""):a.slice(0,-1).join(a.some(function(s){{return s.indexOf(",")>=0}})?"; ":", ")+" y "+a[a.length-1]}}
function c(){{var p=+i.value;if(!(p>=10000&&p<=10000000)){{o.textContent="Escribe el precio máximo del piso, por ejemplo 180000.";return}}var b=D[0],z=D[D.length-1],ds=D.filter(function(x){{return p/x[1]>=M}}).map(function(x){{return x[0]}});
var t="Con "+f(p)+" €, en "+N+" da de media para unos "+f(p/V)+" m²: desde unos "+f(p/z[1])+" m² en "+z[0]+" hasta unos "+f(p/b[1])+" m² en "+b[0]+". ";
t+=ds.length==D.length?"Para un piso de 2 dormitorios (unos "+M+" m²) llega en todos los distritos.":ds.length?"Para un piso de 2 dormitorios (unos "+M+" m²) llega en "+ds.length+" de los "+D.length+" distritos: "+(ds.length>6?ds.slice(0,6).join(ds.slice(0,6).some(function(s){{return s.indexOf(",")>=0}})?"; ":", ")+" y "+(ds.length-6)+" más":y(ds))+".":"No llega para un piso de 2 dormitorios (unos "+M+" m²) en ningún distrito.";
o.textContent=t+" Necesitas unos "+f(p*.2+p*T/100+p*{NOT}+{TAS})+" € ahorrados (entrada del 20 %, impuesto y gastos) y la hipoteca saldría por unos "+f(q(p))+" € al mes: conviene ganar unos "+f(q(p)/E)+" € netos."}}
i.addEventListener("input",c);c()}})()</script>"""
    os.makedirs(F(ck, "comprar-con-presupuesto"), exist_ok=True)
    open(F(ck, "comprar-con-presupuesto", "index.html"), "w", encoding="utf-8").write(page(
        f"¿Qué piso puedo comprar en {c['n']} con mi presupuesto? (2026)",
        desc_corta(f"Con 200.000 € en {c['n']}: unos {round(200000 / v)} m² de media, hasta {round(200000 / bar[1])} m² en {bar[0]}. Metros por distrito, ahorros e hipoteca.", " Calculadora."),
        f"{ck}/comprar-con-presupuesto/", body, [("Vivible", "../../"), (c["n"], "../"), ("Comprar con tu presupuesto", None)], cq_ld))
    urls.append(BASE + f"{ck}/comprar-con-presupuesto/")

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
def fila_sc(k, c, sv):
    return f'<tr><td><a href="../{k}/alquilar-con-presupuesto/">{esc(c["n"])}</a></td><td>{fmt(sv * ESF / c["alquiler"])} m²</td><td><a href="../{k}/comprar-con-presupuesto/">{fmt(precio_max(sv) / c["venta"])} m²</a></td></tr>'
stc = "".join(fila_sc(k, c, 1500) for k, c in ra)
SCD = json.dumps([[k, c["n"], c["alquiler"], c["venta"]] for k, c in ra], ensure_ascii=False).replace("</", "<\\/")
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
<p>La regla más usada: que el alquiler no pase del 33 % de lo que ganas y la hipoteca, del 30 %. Escribe tu sueldo neto y verás cuánto alquiler y qué piso puedes pagar y para cuántos metros te llega en cada ciudad, con los precios medios de idealista.</p>
<div class="g"><div class="k"><small>Con 1.500 € netos, alquiler de hasta</small><b>≈ {fmt(1500 * ESF)} €/mes</b></div>
<div class="k"><small>Con 2.000 € netos, piso de hasta</small><b>≈ {fmt(round(precio_max(2000), -3))} €</b><small>Hipoteca del 80 %</small></div></div>
<div class="card"><form id="sc" onsubmit="return false"><label class="m"><b>Calcula con tu sueldo neto al mes (€)</b><input id="sv" type="number" inputmode="numeric" min="300" step="50" value="1500"></label></form>
<div class="g" style="margin-top:10px" aria-live="polite"><div class="k"><small>Alquiler de hasta (33 %)</small><b id="sa">≈ {fmt(1500 * ESF)} €/mes</b></div>
<div class="k"><small>Piso para comprar de hasta</small><b id="sp">≈ {fmt(round(precio_max(1500), -3))} €</b><small id="sq">Cuota de hasta {fmt(1500 * ESC)} € (30 %), hipoteca del 80 %</small></div></div>
<table class="cmp" style="margin-top:12px"><caption class="m" style="text-align:left;padding-bottom:6px">Metros que te llegan con ese sueldo al precio medio de cada ciudad</caption><tr><th scope="col">Ciudad</th><th scope="col">Alquilar</th><th scope="col">Comprar</th></tr><tbody id="st">{stc}</tbody></table>
<p class="m" style="margin-bottom:0">Si sois dos, suma los dos sueldos netos. Para comprar hace falta además ahorrar la entrada (20 %) y el impuesto y los gastos.</p></div>
<div class="card"><table class="cmp"><caption class="m" style="text-align:left;padding-bottom:6px">Sueldo neto al mes, alquiler máximo (33 %), cuota de hipoteca máxima (30 %) y precio del piso que permite esa cuota (hipoteca del 80 % a {ANOS} años al 2,8 %)</caption><tr><th scope="col">Sueldo</th><th scope="col">Alquiler</th><th scope="col">Cuota</th><th scope="col">Piso</th></tr>{tr}</table>
<p class="m">Para comprar hace falta además ahorrar la entrada (20 %) y el impuesto y los gastos, que cambian según la comunidad: lo tienes en la guía «gastos de compra» de cada ciudad.</p></div>
<h2 style="font:700 21px/1.2 Fraunces,Georgia,serif;margin:24px 0 0">¿Para cuántos metros de alquiler te llega?</h2>
<div class="card"><table class="cmp"><caption class="m" style="text-align:left;padding-bottom:6px">Metros que puedes alquilar al precio medio de cada ciudad según tu sueldo neto (alquiler ≤ 33 %), de la ciudad más barata a la más cara</caption>{cab}{tra}</table></div>
<h2 style="font:700 21px/1.2 Fraunces,Georgia,serif;margin:24px 0 0">¿Para cuántos metros te llega si compras?</h2>
<div class="card"><table class="cmp"><caption class="m" style="text-align:left;padding-bottom:6px">Metros que puedes comprar al precio medio de cada ciudad según tu sueldo neto (cuota ≤ 30 %, hipoteca del 80 % a {ANOS} años al 2,8 %), de la más barata a la más cara</caption>{cab}{trv}</table>
<p class="m">Cifras orientativas con precios medios; dentro de cada ciudad hay distritos mucho más baratos y más caros. El detalle está en la guía de cada ciudad.</p></div>
{sq_html}
<a class="cta" href="../">¿Has visto un piso? Comprueba si te lo puedes permitir</a>
<div class="card m"><b>Más guías:</b> <a href="../hipoteca/">Cuota de la hipoteca</a> · <a href="../precios/">Comparar las 10 ciudades</a> · """ + " · ".join(f'<a href="../{k}/">{esc(c["n"])}</a>' for k, c in C.items()) + f"""</div>
<style>#sc input{{display:block;width:100%;box-sizing:border-box;margin-top:4px;font:16px Inter,system-ui,sans-serif;padding:10px;min-height:44px;border:1px solid #d6d0c4;border-radius:10px;background:#fff;color:#1d2321}}#sc label{{display:block}}#st a{{display:inline-block;min-height:44px;line-height:44px}}</style>
<script>(function(){{var D={SCD},E={ESF},Q={ESC},P={cuota(1)!r},i=document.getElementById("sv"),f=function(n){{return String(Math.round(n)).replace(/\\B(?=(\\d{{3}})+(?!\\d))/g,".")}};
function c(){{var s=+i.value,a=document.getElementById("sa"),p=document.getElementById("sp"),q=document.getElementById("sq"),t=document.getElementById("st");if(!(s>=300&&s<=100000)){{a.textContent=p.textContent="—";q.textContent="Escribe lo que ganas al mes, por ejemplo 1.600.";return}}
var m=s*Q/P;a.textContent="≈ "+f(s*E)+" €/mes";p.textContent="≈ "+f(Math.round(m/1000)*1000)+" €";q.textContent="Cuota de hasta "+f(s*Q)+" € (30 %), hipoteca del 80 %";
t.innerHTML=D.map(function(x){{return '<tr><td><a href="../'+x[0]+'/alquilar-con-presupuesto/">'+x[1]+'</a></td><td>'+f(s*E/x[2])+' m²</td><td><a href="../'+x[0]+'/comprar-con-presupuesto/">'+f(m/x[3])+' m²</a></td></tr>'}}).join("")}}
i.addEventListener("input",c);c()}})()</script>"""
os.makedirs(F("sueldo"), exist_ok=True)
open(F("sueldo", "index.html"), "w", encoding="utf-8").write(page(
    "¿Qué piso puedo pagar con mi sueldo? Calculadora (2026)",
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
<div class="card m"><b>Más guías:</b> <a href="../independizarse/">Cuánto cuesta independizarse</a> · <a href="../sueldo/">Qué piso puedo pagar con mi sueldo</a> · <a href="../papeles-para-alquilar/">Qué papeles piden para alquilar</a> · <a href="../contrato-de-alquiler/">Contrato de alquiler: cuánto dura</a> · <a href="../devolver-fianza/">Cuándo te devuelven la fianza</a> · <a href="../dejar-el-piso/">Carta para dejar el piso</a> · <a href="../reparaciones-alquiler/">Quién paga las reparaciones</a> · <a href="../mudanza/">Lista para la mudanza</a> · <a href="../visitar-un-piso/">Qué mirar al visitar un piso</a> · <a href="../precios/">Comparar las 10 ciudades</a> · """ + " · ".join(f'<a href="../{k}/alquiler/">Alquiler en {esc(c["n"])}</a>' for k, c in C.items()) + """</div>"""
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

# ---------- qué mirar al visitar un piso (visitar-un-piso/): «qué mirar al ver un piso», «qué revisar al visitar un piso de alquiler»,
# «preguntas al visitar un piso»; lista para marcar en el móvil durante la visita (sin cifras: solo consejos y papeles que pide la ley)
assert "visitar-un-piso" not in C
VIS = [
    ("El edificio y el portal", [
        "¿Tiene ascensor? Si no, ¿te importa subir esa altura con la compra o una maleta?",
        "Estado de la fachada, la escalera y el portal: grietas, humedades, limpieza.",
        "Pregunta si hay obras o derramas aprobadas en la comunidad (arreglo de fachada, ascensor, tejado).",
        "¿Hay portero, trastero o plaza de garaje? ¿Entran en el precio?",
    ]),
    ("Luz, ruido y temperatura", [
        "¿Es exterior o interior? Mira a qué da cada ventana y cuántas horas de sol entran.",
        "Cierra las ventanas y escucha: tráfico, bares, vecinos, ascensor o tuberías.",
        "Ventanas: doble cristal y que cierren bien. Influye mucho en el ruido y en la factura.",
        "Calefacción y aire acondicionado: de qué tipo son y si funcionan. Pide la etiqueta energética.",
    ]),
    ("Humedades e instalaciones", [
        "Busca manchas, moho o pintura reciente en techos, esquinas, detrás de muebles y en el baño.",
        "Abre los grifos y la ducha: presión del agua y cuánto tarda en salir caliente.",
        "Cuadro eléctrico y enchufes: que no sean muy antiguos y que haya en cada habitación.",
        "Cobertura del móvil y si llega fibra al edificio.",
    ]),
    ("Cocina, baño y dormitorios", [
        "Electrodomésticos: cuáles se quedan, su estado y si funcionan (enciende la placa y el horno).",
        "Baño: ventilación (ventana o extractor), sanitarios y juntas sin moho.",
        "Mide o calcula si caben tus muebles: cama, sofá, mesa de trabajo.",
        "Armarios y sitio para guardar cosas.",
    ]),
    ("El barrio", [
        "Ve a otra hora del día (y de noche) para ver el ambiente y el ruido de la calle.",
        "Cuánto tardas al trabajo o a clase en transporte público, y a qué hora pasa el último.",
        "Supermercado, farmacia, centro de salud y colegio cerca.",
        "Aparcamiento en la calle si tienes coche.",
    ]),
    ("Si vas a alquilar", [
        "Pregunta qué gastos pagas tú además del alquiler: comunidad, agua, luz, gas, internet, basuras.",
        "Fianza: un mes por ley. Garantía adicional: como mucho dos meses más.",
        "Los honorarios de la inmobiliaria los paga el propietario, no tú (Ley 12/2023).",
        "Pide el contrato antes de firmar: duración, subidas del precio y quién arregla qué.",
        "Haz fotos con fecha de cómo está todo al entrar: te servirán para recuperar la fianza.",
    ]),
    ("Si vas a comprar", [
        "Pide la nota simple del Registro de la Propiedad: quién es el dueño y si tiene hipotecas o embargos.",
        "Pide el certificado de estar al día con la comunidad y el último recibo del IBI.",
        "Pregunta por la inspección técnica del edificio (ITE o IEE) si el edificio es antiguo.",
        "Pide el certificado de eficiencia energética: es obligatorio para vender.",
        "Comprueba que los metros del anuncio coinciden con los de la nota simple o el catastro.",
    ]),
]
nvis = sum(len(xs) for _, xs in VIS)
vi_html, vi_ld = faq([
    ("¿Qué hay que mirar al visitar un piso?",
     "Lo más importante es lo que luego cuesta arreglar o no se puede cambiar: humedades, ruido, luz natural, el estado del edificio (y si hay derramas), las ventanas, la calefacción y el transporte hasta tu trabajo. Ve a otra hora del día para ver el barrio."),
    ("¿Qué preguntar al visitar un piso de alquiler?",
     "Qué gastos pagas tú además del alquiler, cuánto piden de fianza y garantía, cuánto dura el contrato y cómo sube el precio, qué muebles y electrodomésticos se quedan y quién paga las averías."),
    ("¿Qué papeles hay que pedir al comprar un piso?",
     "La nota simple del Registro (dueño y cargas como hipotecas o embargos), el certificado de deudas con la comunidad, el último recibo del IBI, el certificado de eficiencia energética y, si el edificio es antiguo, la inspección técnica del edificio."),
    ("¿Cómo saber si un piso tiene humedades?",
     "Mira techos, esquinas, detrás de los muebles, el baño y los marcos de las ventanas. Las manchas oscuras, el moho, el olor a cerrado o la pintura muy reciente en un solo trozo de pared son señales de aviso."),
    ("¿Cómo saber si el precio del piso es justo?",
     "Compáralo con lo que cuesta el m² en su distrito. En Vivible puedes pegar el anuncio y te dice si el precio está por encima o por debajo de su zona, y cómo es el transporte, el ruido y los servicios cerca."),
])
lis = "".join(f'<div class="card"><h2 class="vh">{esc(t)}</h2>' + "".join(
    f'<label class="vc"><input type="checkbox" data-k="{i}-{j}"><span>{esc(x)}</span></label>' for j, x in enumerate(xs)) + "</div>" for i, (t, xs) in enumerate(VIS))
body = f"""<h1>Qué mirar al visitar un piso: lista para comprobar</h1>
<p>Una visita dura poco y con los nervios se olvidan cosas. Abre esta lista en el móvil y ve marcando lo que revisas: {nvis} puntos para un piso en alquiler o en venta, también si buscas habitación. Lo que marques se queda guardado en este móvil.</p>
<div class="card" id="vp" aria-live="polite"><b id="vn">0 de {nvis} revisados</b><div class="vb"><i id="vi"></i></div>
<button type="button" id="vr" class="vbt">Empezar otra visita</button></div>
{lis}
<style>.vh{{font:700 19px/1.2 Fraunces,Georgia,serif;margin:0 0 6px}}.vc{{display:flex;gap:10px;align-items:flex-start;padding:9px 0;min-height:44px;box-sizing:border-box;border-top:1px solid #f1ede6;cursor:pointer}}.vc input{{width:22px;height:22px;margin:2px 0 0;flex:none;accent-color:#1f6f54}}.vc input:checked+span{{color:#5f6b66;text-decoration:line-through}}
.vb{{height:8px;background:#efebe4;border-radius:99px;margin:8px 0 10px;overflow:hidden}}.vb i{{display:block;height:100%;width:0;background:#1f6f54}}.vbt{{font:600 14px Inter,system-ui,sans-serif;min-height:44px;padding:0 14px;border:1px solid #d6d0c4;border-radius:10px;background:#fff;color:#1d2321;cursor:pointer}}
#vp{{position:sticky;top:0;z-index:1}}</style>
<script>(function(){{var K="vivible.visita",cs=[].slice.call(document.querySelectorAll(".vc input")),s={{}};
try{{s=JSON.parse(localStorage.getItem(K)||"{{}}")||{{}}}}catch(e){{}}
function pinta(){{var k=0;cs.forEach(function(c){{if(c.checked)k++}});document.getElementById("vn").textContent=k+" de "+cs.length+" revisados";document.getElementById("vi").style.width=(k*100/cs.length)+"%"}}
function guarda(){{var o={{}};cs.forEach(function(c){{if(c.checked)o[c.getAttribute("data-k")]=1}});try{{localStorage.setItem(K,JSON.stringify(o))}}catch(e){{}}}}
cs.forEach(function(c){{c.checked=!!s[c.getAttribute("data-k")];c.addEventListener("change",function(){{guarda();pinta()}})}});
document.getElementById("vr").addEventListener("click",function(){{if(cs.some(function(c){{return c.checked}})&&!confirm("¿Borrar lo que has marcado y empezar de cero?"))return;cs.forEach(function(c){{c.checked=false}});guarda();pinta()}});pinta()}})();</script>
{vi_html}
<a class="cta" href="../">¿Te ha gustado el piso? Pega el anuncio y comprueba si el precio es justo</a>
<div class="card m"><b>Más guías:</b> <a href="../gastos-de-alquiler/">Dinero para alquilar</a> · <a href="../papeles-para-alquilar/">Papeles para alquilar</a> · <a href="../gastos-de-compra/">Gastos de comprar</a> · <a href="../sueldo/">Qué piso puedo pagar con mi sueldo</a> · <a href="../hipoteca/">Cuota de la hipoteca</a> · <a href="../pasos-para-comprar/">Pasos para comprar un piso</a> · <a href="../barrios/">¿En qué distrito está mi barrio?</a> · """ + " · ".join(f'<a href="../{k}/">Vivir en {esc(c["n"])}</a>' for k, c in C.items()) + """</div>"""
os.makedirs(F("visitar-un-piso"), exist_ok=True)
open(F("visitar-un-piso", "index.html"), "w", encoding="utf-8").write(page(
    "Qué mirar al visitar un piso: lista para alquilar o comprar",
    desc_corta(f"Lista de {nvis} puntos para revisar en la visita: humedades, ruido, luz, edificio, gastos y papeles. Márcala en el móvil mientras ves el piso.", " Gratis."),
    "visitar-un-piso/", body, [("Vivible", "../"), ("Visitar un piso", None)], vi_ld))
urls.insert(10, BASE + "visitar-un-piso/")

# ---------- papeles para alquilar (papeles-para-alquilar/): «qué papeles piden para alquilar un piso», «documentos para alquilar
# un piso», «requisitos para alquilar»; lista para marcar lo que ya tienes, lo que te debe dar el propietario y lo que no te pueden
# pedir (LAU y Ley 12/2023, como gastos-de-alquiler/); sueldo que suelen pedir con la regla de las guías (alquiler ≤ 33 %)
assert "papeles-para-alquilar" not in C
PAP = [
    ("Quién eres", [
        "DNI o NIE en vigor (de cada persona que vaya a firmar el contrato).",
        "Un teléfono y un correo donde localizarte.",
    ]),
    ("Si trabajas por cuenta ajena", [
        "Las últimas nóminas (lo habitual es que pidan las tres últimas).",
        "El contrato de trabajo. Si es indefinido, dilo: es lo que más tranquiliza al propietario.",
        "El informe de vida laboral (se descarga gratis en la web de la Seguridad Social).",
    ]),
    ("Si eres autónomo", [
        "La última declaración de la renta.",
        "Los últimos pagos trimestrales a Hacienda (IVA e IRPF).",
        "El informe de vida laboral o el alta como autónomo.",
    ]),
    ("Si estudias o aún no tienes ingresos fijos", [
        "La matrícula o la carta de la universidad, si eres estudiante.",
        "Un avalista: alguien que se compromete a pagar si tú no pagas, con sus propias nóminas o declaración de la renta.",
        "Si no tienes avalista, pregunta si aceptan un aval bancario o varios meses pagados por adelantado (cuidado: en contratos de vivienda la garantía adicional no puede pasar de dos meses).",
    ]),
    ("Lo que ayuda a que te elijan", [
        "Una carta o contacto de tu casero anterior que diga que pagabas a tiempo.",
        "Un justificante de ahorros o la última declaración de la renta, aunque tengas nómina.",
        "Tenerlo todo en PDF en el móvil para mandarlo el mismo día de la visita.",
    ]),
]
PAP_PROP = [
    "El contrato por escrito, con la duración, el precio, cómo se actualiza y quién paga cada gasto.",
    "El certificado de eficiencia energética: es obligatorio para alquilar.",
    "El justificante de la fianza: en muchas comunidades el propietario debe depositarla en un organismo de la comunidad autónoma.",
    "Un recibo de cada pago, si no pagas por transferencia.",
    "Un inventario con fotos de los muebles y del estado del piso al entrar (pídelo o hazlo tú y mándaselo).",
]
PAP_NO = [
    "Pagar los honorarios de la inmobiliaria o los gastos de hacer el contrato: corren a cargo del propietario (Ley 12/2023).",
    "Una fianza distinta de un mes de alquiler en un piso para vivir.",
    "Más de dos meses de garantía adicional en contratos de hasta cinco años (siete si el propietario es una empresa).",
]
npap = sum(len(xs) for _, xs in PAP)
rp = sorted(C.items(), key=lambda kc: kc[1]["alquiler"])
trp = "".join(f'<tr><td><a href="../{k}/sueldo-para-alquilar/">{esc(c["n"])}</a></td><td>{fmt(c["alquiler"] * M2A)} €</td><td><b>{fmt(c["alquiler"] * M2A / ESF)} €</b></td></tr>' for k, c in rp)
pb, pc = rp[0][1], rp[-1][1]
pa_html, pa_ld = faq([
    ("¿Qué papeles piden para alquilar un piso?",
     "Lo normal es el DNI o NIE y algo que demuestre que puedes pagar: las últimas nóminas y el contrato de trabajo, o la declaración de la renta y los pagos trimestrales si eres autónomo. Muchos propietarios piden también la vida laboral, y si no tienes ingresos fijos, un avalista."),
    ("¿Cuánto tengo que ganar para que me alquilen un piso?",
     f"Muchos propietarios piden que el alquiler no pase de un tercio de lo que ganas en neto. Para un piso medio de {M2A} m², son unos {fmt(pb['alquiler'] * M2A / ESF)} € netos al mes en {pb['n']} y unos {fmt(pc['alquiler'] * M2A / ESF)} € en {pc['n']}. Si alquiláis entre dos, se suelen sumar los dos sueldos."),
    ("¿Qué es un avalista y cuándo lo piden?",
     "Es una persona (a menudo un familiar) que firma que pagará el alquiler si tú no lo haces. Lo suelen pedir a estudiantes, a quien acaba de empezar a trabajar o a quien tiene un contrato temporal. El avalista tiene que demostrar sus propios ingresos."),
    ("¿Qué documentos me tiene que dar el propietario?",
     "El contrato por escrito, el certificado de eficiencia energética (obligatorio para alquilar) y un justificante de cada pago si no pagas por transferencia. En muchas comunidades debe depositar la fianza en un organismo autonómico: puedes pedirle el justificante."),
    ("¿Me pueden cobrar la inmobiliaria por alquilar?",
     "No. Desde la Ley 12/2023, de vivienda, los honorarios de la inmobiliaria y los gastos de hacer el contrato los paga el propietario. Al firmar solo pagas el primer mes, la fianza de un mes y, si te la piden, una garantía adicional de hasta dos meses."),
])
lip = "".join(f'<div class="card"><h2 class="vh">{esc(t)}</h2>' + "".join(
    f'<label class="vc"><input type="checkbox" data-k="{i}-{j}"><span>{esc(x)}</span></label>' for j, x in enumerate(xs)) + "</div>" for i, (t, xs) in enumerate(PAP))
body = f"""<h1>Qué papeles piden para alquilar un piso: lista de documentos</h1>
<p>En las ciudades con más demanda, el piso se lo queda quien manda antes los papeles. Ten esta lista a mano y marca lo que ya tienes preparado: {npap} documentos según trabajes, seas autónomo o estudies. Lo que marques se queda guardado en este móvil. Debajo tienes lo que te tiene que dar el propietario y lo que no te pueden pedir.</p>
<div class="card" id="vp" aria-live="polite"><b id="vn">0 de {npap} preparados</b><div class="vb"><i id="vi"></i></div>
<button type="button" id="vr" class="vbt">Empezar de nuevo</button></div>
{lip}
<h2 style="font:700 21px/1.2 Fraunces,Georgia,serif;margin:24px 0 0">Lo que te tiene que dar el propietario</h2>
<div class="card"><ul style="margin:0;padding-left:20px">{"".join(f"<li>{esc(x)}</li>" for x in PAP_PROP)}</ul></div>
<h2 style="font:700 21px/1.2 Fraunces,Georgia,serif;margin:24px 0 0">Lo que no te pueden pedir</h2>
<div class="card"><ul style="margin:0;padding-left:20px">{"".join(f"<li>{esc(x)}</li>" for x in PAP_NO)}</ul>
<p class="m">Cuánto dinero hay que tener al firmar, ciudad por ciudad: <a href="../gastos-de-alquiler/">dinero para alquilar un piso</a>.</p></div>
<h2 style="font:700 21px/1.2 Fraunces,Georgia,serif;margin:24px 0 0">Cuánto suelen pedir que ganes</h2>
<div class="card"><table class="cmp"><caption class="m" style="text-align:left;padding-bottom:6px">Piso de {M2A} m² al alquiler medio de cada ciudad ({esc(mes_txt)}) y sueldo neto al mes para que el alquiler no pase de un tercio, la regla que usan muchos propietarios</caption><tr><th scope="col">Ciudad</th><th scope="col">Alquiler</th><th scope="col">Sueldo neto</th></tr>{trp}</table>
<p class="m">Es una referencia: cada propietario decide. Si el piso cuesta otra cifra, calcula la tuya en <a href="../sueldo/">qué piso puedo pagar con mi sueldo</a>.</p></div>
<style>.vh{{font:700 19px/1.2 Fraunces,Georgia,serif;margin:0 0 6px}}.vc{{display:flex;gap:10px;align-items:flex-start;padding:9px 0;min-height:44px;box-sizing:border-box;border-top:1px solid #f1ede6;cursor:pointer}}.vc input{{width:22px;height:22px;margin:2px 0 0;flex:none;accent-color:#1f6f54}}.vc input:checked+span{{color:#5f6b66;text-decoration:line-through}}
.vb{{height:8px;background:#efebe4;border-radius:99px;margin:8px 0 10px;overflow:hidden}}.vb i{{display:block;height:100%;width:0;background:#1f6f54}}.vbt{{font:600 14px Inter,system-ui,sans-serif;min-height:44px;padding:0 14px;border:1px solid #d6d0c4;border-radius:10px;background:#fff;color:#1d2321;cursor:pointer}}
#vp{{position:sticky;top:0;z-index:1}}</style>
<script>(function(){{var K="vivible.papeles",cs=[].slice.call(document.querySelectorAll(".vc input")),s={{}};
try{{s=JSON.parse(localStorage.getItem(K)||"{{}}")||{{}}}}catch(e){{}}
function pinta(){{var k=0;cs.forEach(function(c){{if(c.checked)k++}});document.getElementById("vn").textContent=k+" de "+cs.length+" preparados";document.getElementById("vi").style.width=(k*100/cs.length)+"%"}}
function guarda(){{var o={{}};cs.forEach(function(c){{if(c.checked)o[c.getAttribute("data-k")]=1}});try{{localStorage.setItem(K,JSON.stringify(o))}}catch(e){{}}}}
cs.forEach(function(c){{c.checked=!!s[c.getAttribute("data-k")];c.addEventListener("change",function(){{guarda();pinta()}})}});
document.getElementById("vr").addEventListener("click",function(){{if(cs.some(function(c){{return c.checked}})&&!confirm("¿Borrar lo que has marcado y empezar de cero?"))return;cs.forEach(function(c){{c.checked=false}});guarda();pinta()}});pinta()}})();</script>
{pa_html}
<a class="cta" href="../">¿Ya tienes un piso en mente? Pega el anuncio y comprueba si el precio es justo</a>
<div class="card m"><b>Más guías:</b> <a href="../gastos-de-alquiler/">Dinero para alquilar</a> · <a href="../contrato-de-alquiler/">Contrato de alquiler: cuánto dura</a> · <a href="../visitar-un-piso/">Qué mirar al visitar un piso</a> · <a href="../sueldo/">Qué piso puedo pagar con mi sueldo</a> · <a href="../barrios-baratos/">Barrios más baratos</a> · """ + " · ".join(f'<a href="../{k}/alquiler/">Alquiler en {esc(c["n"])}</a>' for k, c in C.items()) + """</div>"""
os.makedirs(F("papeles-para-alquilar"), exist_ok=True)
open(F("papeles-para-alquilar", "index.html"), "w", encoding="utf-8").write(page(
    "Qué papeles piden para alquilar un piso: lista de documentos",
    desc_corta(f"Documentos para alquilar un piso si trabajas, eres autónomo o estudias, lo que te debe dar el propietario y lo que no te pueden pedir. Lista para marcar en el móvil.", ""),
    "papeles-para-alquilar/", body, [("Vivible", "../"), ("Papeles para alquilar", None)], pa_ld))
urls.insert(11, BASE + "papeles-para-alquilar/")

# ---------- contrato de alquiler (contrato-de-alquiler/): «cuánto dura un contrato de alquiler», «qué debe incluir un contrato
# de alquiler», «puedo irme antes de que acabe el contrato»; plazos de la Ley de Arrendamientos Urbanos (LAU, tras el RDL 7/2019 y la
# Ley 12/2023) y calculadora de fechas (fin de la prórroga obligatoria y desde cuándo puedes irte). Sin cifras inventadas: solo plazos de la ley.
assert "contrato-de-alquiler" not in C
CON = [
    ("Quiénes firman y qué se alquila", "Nombre y DNI o NIE de propietario e inquilinos, la dirección del piso y lo que entra (trastero, garaje, muebles)."),
    ("La duración", "La fecha de inicio y cuánto dura. Aunque ponga un año, en un piso para vivir puedes quedarte hasta cinco (siete si el propietario es una empresa)."),
    ("El precio y cómo se paga", "Cuánto pagas al mes, qué día y de qué forma. Mejor por transferencia: queda justificante de cada pago."),
    ("Si sube el precio y cómo", "La renta solo puede subir una vez al año y solo si el contrato lo dice. Mira qué índice usa para la subida."),
    ("La fianza y la garantía", "La fianza es un mes de alquiler. Si piden garantía adicional, que conste cuánto es: como mucho dos meses en contratos de hasta cinco o siete años."),
    ("Quién paga cada gasto", "Comunidad, IBI, basuras, luz, agua, gas e internet. Si te toca pagar la comunidad o el IBI, el contrato tiene que decir cuánto es al año."),
    ("El estado del piso al entrar", "Un inventario con fotos de los muebles y de cómo está el piso. Es lo que evita discusiones con la fianza al irte."),
    ("Mascotas, obras y subalquiler", "Lo que se permite y lo que no. Para subalquilar o traspasar el contrato hace falta el permiso por escrito del propietario."),
    ("Si el propietario puede recuperar el piso", "Solo puede pedirlo para vivir él o un familiar directo antes de los cinco años si el contrato lo dice expresamente, y siempre después del primer año."),
]
PLZ = [
    ("Duración mínima garantizada", "5 años", "7 si el propietario es una empresa. Cada año el contrato se renueva solo, salvo que tú avises con 30 días de antelación de que te vas."),
    ("Prórroga después", "Hasta 3 años más", "Año a año, si nadie avisa: el propietario, con 4 meses de antelación; tú, con 2 meses."),
    ("Irte antes de tiempo", "Desde los 6 meses", "Avisando con 30 días. El contrato puede fijar una indemnización de un mes por cada año que quede (la parte proporcional si es menos)."),
    ("Subida del alquiler", "Una vez al año", "Solo si el contrato lo dice, en la fecha en que se cumple cada año de contrato."),
    ("Si venden el piso", "Sigues dentro", "El nuevo dueño tiene que respetar tu contrato durante los cinco (o siete) años."),
]
nco = len(CON)
co_html, co_ld = faq([
    ("¿Cuánto dura un contrato de alquiler de vivienda?",
     "Lo que pactéis, pero si es menos de cinco años se renueva solo cada año hasta llegar a cinco (siete si el propietario es una empresa), salvo que tú avises con 30 días de que te vas. Después, si nadie avisa, se alarga año a año hasta tres años más."),
    ("¿Me pueden echar cuando acabe el primer año?",
     "No, si es tu vivienda habitual. El contrato se renueva solo hasta los cinco años (siete si el propietario es una empresa). La única excepción es que el propietario necesite el piso para vivir él o un familiar directo, que el contrato lo diga expresamente y que te avise con al menos dos meses."),
    ("¿Puedo irme antes de que acabe el contrato?",
     "Sí, a partir de los seis meses, avisando con 30 días de antelación. Si el contrato lo dice, tendrás que pagar una indemnización de un mes de alquiler por cada año que quede, o la parte proporcional."),
    ("¿Cuánto me pueden subir el alquiler?",
     "Solo una vez al año y solo si el contrato incluye la subida, con el índice que diga. Si el contrato no dice nada de actualizar la renta, el precio no sube durante el contrato."),
    ("¿Quién paga las reparaciones del piso?",
     "Las reparaciones necesarias para que el piso se pueda habitar las paga el propietario. Las pequeñas reparaciones por el desgaste del uso normal (un grifo que gotea, un enchufe) las pagas tú."),
    ("¿Qué pasa si venden el piso que tengo alquilado?",
     "Que el nuevo dueño se subroga en el contrato: tiene que respetarlo hasta que se cumplan los cinco años (siete si el antiguo propietario era una empresa), con el mismo precio y condiciones."),
])
lic = "".join(f'<label class="vc"><input type="checkbox" data-k="{i}"><span><b>{esc(t)}.</b> {esc(x)}</span></label>' for i, (t, x) in enumerate(CON))
tpl = "".join(f'<tr><td style="text-align:left;white-space:normal">{esc(a)}</td><td><b>{esc(b)}</b></td><td style="text-align:left;white-space:normal" class="m">{esc(x)}</td></tr>' for a, b, x in PLZ)
body = f"""<h1>Contrato de alquiler: cuánto dura y qué debe incluir</h1>
<p>Antes de firmar, comprueba que el contrato tiene todo lo importante y conoce los plazos que marca la ley para un piso en el que vas a vivir. Pon la fecha de tu contrato y te decimos hasta cuándo puedes quedarte y desde cuándo puedes irte.</p>
<div class="card" id="cf"><b>¿Hasta cuándo dura mi contrato?</b>
<div style="display:flex;flex-wrap:wrap;gap:10px;margin:10px 0 4px"><label class="m" style="flex:1 1 150px">Empezó el<br><input type="date" id="cd" style="font:16px Inter,system-ui,sans-serif;min-height:44px;width:100%;box-sizing:border-box;padding:0 8px;border:1px solid #d6d0c4;border-radius:10px"></label>
<label class="m" style="flex:1 1 150px">El propietario es<br><select id="ct" style="font:16px Inter,system-ui,sans-serif;min-height:44px;width:100%;box-sizing:border-box;padding:0 8px;border:1px solid #d6d0c4;border-radius:10px;background:#fff"><option value="5">Una persona</option><option value="7">Una empresa</option></select></label></div>
<div id="cr" aria-live="polite" class="m">Elige la fecha en que empezó (o empezará) el contrato.</div></div>
<h2 style="font:700 21px/1.2 Fraunces,Georgia,serif;margin:24px 0 0">Los plazos que marca la ley</h2>
<div class="card"><table class="cmp"><caption class="m" style="text-align:left;padding-bottom:6px">Contratos de vivienda habitual firmados desde marzo de 2019 (Ley de Arrendamientos Urbanos)</caption><tr><th scope="col" style="text-align:left">Qué</th><th scope="col">Plazo</th><th scope="col" style="text-align:left">Detalle</th></tr>{tpl}</table>
<p class="m">Si alquilas una habitación o un piso de temporada (por estudios o trabajo, menos de un año), estos plazos no se aplican igual: manda lo que firmes, así que léelo con calma.</p></div>
<h2 style="font:700 21px/1.2 Fraunces,Georgia,serif;margin:24px 0 0">Qué debe incluir el contrato</h2>
<div class="card" id="vp" aria-live="polite"><b id="vn">0 de {nco} revisados</b><div class="vb"><i id="vi"></i></div>
<button type="button" id="vr" class="vbt">Empezar de nuevo</button></div>
<div class="card">{lic}</div>
<p class="m">Lo que tienes que tener preparado tú: <a href="../papeles-para-alquilar/">papeles que piden para alquilar</a>. Lo que pagas al firmar: <a href="../gastos-de-alquiler/">fianza y garantía por ciudad</a>.</p>
<style>.vc{{display:flex;gap:10px;align-items:flex-start;padding:9px 0;min-height:44px;box-sizing:border-box;border-top:1px solid #f1ede6;cursor:pointer}}.vc:first-child{{border-top:0}}.vc input{{width:22px;height:22px;margin:2px 0 0;flex:none;accent-color:#1f6f54}}.vc input:checked+span{{color:#5f6b66}}
.vb{{height:8px;background:#efebe4;border-radius:99px;margin:8px 0 10px;overflow:hidden}}.vb i{{display:block;height:100%;width:0;background:#1f6f54}}.vbt{{font:600 14px Inter,system-ui,sans-serif;min-height:44px;padding:0 14px;border:1px solid #d6d0c4;border-radius:10px;background:#fff;color:#1d2321;cursor:pointer}}
#cr b{{color:#1d2321}}</style>
<script>(function(){{var K="vivible.contrato",cs=[].slice.call(document.querySelectorAll(".vc input")),s={{}};
try{{s=JSON.parse(localStorage.getItem(K)||"{{}}")||{{}}}}catch(e){{}}
function pinta(){{var k=0;cs.forEach(function(c){{if(c.checked)k++}});document.getElementById("vn").textContent=k+" de "+cs.length+" revisados";document.getElementById("vi").style.width=(k*100/cs.length)+"%"}}
function guarda(){{var o={{}};cs.forEach(function(c){{if(c.checked)o[c.getAttribute("data-k")]=1}});try{{localStorage.setItem(K,JSON.stringify(o))}}catch(e){{}}}}
cs.forEach(function(c){{c.checked=!!s[c.getAttribute("data-k")];c.addEventListener("change",function(){{guarda();pinta()}})}});
document.getElementById("vr").addEventListener("click",function(){{if(cs.some(function(c){{return c.checked}})&&!confirm("¿Borrar lo que has marcado y empezar de cero?"))return;cs.forEach(function(c){{c.checked=false}});guarda();pinta()}});pinta();
var M=["enero","febrero","marzo","abril","mayo","junio","julio","agosto","septiembre","octubre","noviembre","diciembre"],d=document.getElementById("cd"),t=document.getElementById("ct"),r=document.getElementById("cr");
function mas(f,a,m){{var x=new Date(f.getFullYear()+a,f.getMonth()+m,1),u=new Date(x.getFullYear(),x.getMonth()+1,0).getDate();x.setDate(Math.min(f.getDate(),u));return x}}
function txt(x){{return x.getDate()+" de "+M[x.getMonth()]+" de "+x.getFullYear()}}
function calc(){{var v=/^(\\d{{4}})-(\\d{{2}})-(\\d{{2}})$/.exec(d.value||"");if(!v){{r.textContent="Elige la fecha en que empezó (o empezará) el contrato.";return}}
var f=new Date(+v[1],v[2]-1,+v[3]),n=+t.value,fin=mas(f,n,0),pr=mas(f,n+3,0),ir=mas(f,0,6),av=mas(fin,0,-4);
r.innerHTML="Puedes quedarte al menos hasta el <b>"+txt(fin)+"</b> ("+n+" años). Si nadie avisa antes, se alarga año a año hasta el <b>"+txt(pr)+"</b>; para no renovar, el propietario tiene que avisarte antes del "+txt(av)+".<br>Puedes irte desde el <b>"+txt(ir)+"</b> avisando con 30 días."}}
d.addEventListener("change",calc);d.addEventListener("input",calc);t.addEventListener("change",calc);calc()}})();</script>
{co_html}
<a class="cta" href="../">¿Ya tienes el piso? Comprueba si el precio es justo</a>
<div class="card m"><b>Más guías:</b> <a href="../papeles-para-alquilar/">Papeles para alquilar</a> · <a href="../gastos-de-alquiler/">Dinero para alquilar</a> · <a href="../devolver-fianza/">Cuándo te devuelven la fianza</a> · <a href="../dejar-el-piso/">Carta para dejar el piso</a> · <a href="../reparaciones-alquiler/">Quién paga las reparaciones</a> · <a href="../mudanza/">Lista para la mudanza</a> · <a href="../visitar-un-piso/">Qué mirar al visitar un piso</a> · <a href="../sueldo/">Qué piso puedo pagar con mi sueldo</a> · """ + " · ".join(f'<a href="../{k}/alquiler/">Alquiler en {esc(c["n"])}</a>' for k, c in C.items()) + """</div>"""
os.makedirs(F("contrato-de-alquiler"), exist_ok=True)
open(F("contrato-de-alquiler", "index.html"), "w", encoding="utf-8").write(page(
    "Contrato de alquiler: cuánto dura y qué debe incluir",
    desc_corta("Duración del contrato de alquiler (5 o 7 años y prórroga), cuándo puedes irte, subidas y qué debe incluir. Calcula las fechas de tu contrato.", " Gratis."),
    "contrato-de-alquiler/", body, [("Vivible", "../"), ("Contrato de alquiler", None)], co_ld))
urls.insert(12, BASE + "contrato-de-alquiler/")

# ---------- devolver la fianza (devolver-fianza/): «cuándo me devuelven la fianza del alquiler», «plazo devolución fianza»,
# «qué pueden descontar de la fianza», «el casero no me devuelve la fianza»; LAU art. 36.4 (un mes desde la entrega de llaves;
# después, el interés legal del dinero), art. 21.4 (pequeñas reparaciones), LEC art. 23 y 31 (sin abogado ni procurador hasta 2.000 €)
# y LO 1/2025 (antes de demandar, intentar un acuerdo). Cifras por ciudad: las mismas que gastos-de-alquiler/ (precios.json).
assert "devolver-fianza" not in C
DSC = [
    ("Sí pueden descontar", "Alquileres que debas, recibos de luz, agua o gas a tu cargo sin pagar y daños que hayas causado tú (un mueble roto, agujeros de más, una puerta golpeada)."),
    ("No pueden descontar", "El desgaste normal por vivir en el piso: pintura gastada por el tiempo, roces leves, el uso normal de los electrodomésticos o averías que no son culpa tuya."),
    ("Tiene que justificarlo", "Cada descuento con su motivo y, si son daños, con presupuesto o factura. No vale quedarse la fianza entera «por si acaso»."),
]
PAS = [
    ("Al irte", "Haz fotos y vídeo con fecha de cada habitación, lee los contadores y entrega las llaves con un documento firmado que diga el día (o por burofax si no quiere firmar)."),
    ("Pasado un mes", "Si no te la ha devuelto, pídesela por escrito: un burofax con acuse de recibo y copia certificada que diga cuánto reclamas, a qué cuenta y en qué plazo."),
    ("Si sigue sin pagar", "Desde abril de 2025, antes de demandar hay que intentar un acuerdo y poder demostrarlo: ese burofax con una propuesta sirve. Pide también el justificante del depósito de la fianza en tu comunidad autónoma."),
    ("En el juzgado", "Hasta 2.000 € puedes reclamar tú mismo en el juzgado de tu partido judicial, con un impreso y sin abogado ni procurador. Le puedes reclamar también el interés legal desde que pasó el mes."),
]
rfa = sorted(C.items(), key=lambda kc: kc[1]["alquiler"])
tfa = "".join(f'<tr><td><a href="../{k}/alquiler/">{esc(c["n"])}</a></td><td>{fmt(c["alquiler"] * M2A)} €</td><td>{fmt(c["hab"])} €</td></tr>' for k, c in rfa)
fa_html, fa_ld = faq([
    ("¿Cuánto tarda el propietario en devolver la fianza?",
     "La ley le da un mes desde que entregas las llaves. Si pasa ese mes sin devolverla, además de la fianza te debe el interés legal del dinero desde ese día."),
    ("¿Qué me pueden descontar de la fianza?",
     "Lo que debas (alquiler, recibos a tu cargo) y los daños que hayas causado, justificados. No el desgaste normal de vivir en el piso, como la pintura gastada por los años o el uso normal de los muebles."),
    ("¿Me tienen que devolver también la garantía adicional?",
     "Sí. La garantía adicional, si la pagaste, se devuelve igual que la fianza al terminar el contrato, con los mismos descuentos justificados."),
    ("¿Qué hago si el casero no me devuelve la fianza?",
     "Reclámasela por escrito con un burofax, proponiendo un plazo para pagar. Si no responde, puedes ir al juzgado: hasta 2.000 € no necesitas abogado ni procurador. Antes de demandar hay que haber intentado un acuerdo, y el burofax sirve para demostrarlo."),
    ("¿Puedo no pagar el último mes y que se quede la fianza?",
     "No es buena idea: la fianza no está para pagar el último mes y el propietario podría reclamarte ese mes y además descontar daños. Lo seguro es pagar el último mes y pedir la fianza al entregar las llaves."),
    ("¿Cuánto es la fianza de un piso de alquiler?",
     f"Un mes de alquiler, obligatoria por ley en los pisos para vivir. Para el piso medio de {M2A} m², de unos {fmt(rfa[0][1]['alquiler'] * M2A)} € en {rfa[0][1]['n']} a unos {fmt(rfa[-1][1]['alquiler'] * M2A)} € en {rfa[-1][1]['n']}."),
])
tds = "".join(f'<tr><td style="text-align:left;white-space:normal"><b>{esc(a)}</b></td><td style="text-align:left;white-space:normal" class="m">{esc(x)}</td></tr>' for a, x in DSC)
lps = "".join(f'<li><b>{esc(a)}.</b> {esc(x)}</li>' for a, x in PAS)
body = f"""<h1>¿Cuándo me devuelven la fianza del alquiler?</h1>
<p>Cuando dejas un piso de alquiler, el propietario tiene <b>un mes desde que le entregas las llaves</b> para devolverte la fianza. Pon el día en que las entregas y te decimos hasta cuándo tiene, qué te puede descontar y qué hacer si no te la devuelve.</p>
<div class="card" id="ff"><b>¿Hasta cuándo tiene para devolvérmela?</b>
<div style="display:flex;flex-wrap:wrap;gap:10px;margin:10px 0 4px"><label class="m" style="flex:1 1 150px">Entregué las llaves el<br><input type="date" id="fd" style="font:16px Inter,system-ui,sans-serif;min-height:44px;width:100%;box-sizing:border-box;padding:0 8px;border:1px solid #d6d0c4;border-radius:10px"></label>
<label class="m" style="flex:1 1 150px">Fianza (€, opcional)<br><input type="number" id="fi" inputmode="decimal" min="0" step="10" placeholder="Por ejemplo, 900" style="font:16px Inter,system-ui,sans-serif;min-height:44px;width:100%;box-sizing:border-box;padding:0 8px;border:1px solid #d6d0c4;border-radius:10px"></label></div>
<div id="fr" aria-live="polite" class="m">Elige el día en que entregaste (o vas a entregar) las llaves.</div></div>
<div class="g"><div class="k"><small>Plazo para devolverla</small><b>1 mes</b><small>Desde que entregas las llaves</small></div>
<div class="k"><small>Si se retrasa</small><b>+ intereses</b><small>El interés legal del dinero desde ese día</small></div></div>
<h2 style="font:700 21px/1.2 Fraunces,Georgia,serif;margin:24px 0 0">Qué te pueden descontar y qué no</h2>
<div class="card"><table class="cmp"><caption class="m" style="text-align:left;padding-bottom:6px">Descuentos de la fianza al terminar el contrato (Ley de Arrendamientos Urbanos)</caption>{tds}</table>
<p class="m">Las pequeñas reparaciones por el uso diario (una bombilla, un grifo que gotea) te tocan a ti mientras vives en el piso; las que hacen falta para que el piso se pueda habitar, al propietario.</p></div>
<h2 style="font:700 21px/1.2 Fraunces,Georgia,serif;margin:24px 0 0">Qué hacer si no te la devuelven</h2>
<div class="card"><ol style="margin:0;padding-left:20px">{lps}</ol></div>
<h2 style="font:700 21px/1.2 Fraunces,Georgia,serif;margin:24px 0 0">Cuánto es la fianza en cada ciudad</h2>
<div class="card"><table class="cmp"><caption class="m" style="text-align:left;padding-bottom:6px">Fianza de un mes para un piso de {M2A} m² y para una habitación, al precio medio de cada ciudad ({esc(mes_txt)})</caption><tr><th scope="col">Ciudad</th><th scope="col">Piso</th><th scope="col">Habitación</th></tr>{tfa}</table>
<p class="m">Lo que pagas al entrar, con la garantía adicional: <a href="../gastos-de-alquiler/">dinero para alquilar un piso</a>.</p></div>
<script>(function(){{var M=["enero","febrero","marzo","abril","mayo","junio","julio","agosto","septiembre","octubre","noviembre","diciembre"],d=document.getElementById("fd"),a=document.getElementById("fi"),r=document.getElementById("fr");
function mas(f,m){{var x=new Date(f.getFullYear(),f.getMonth()+m,1),u=new Date(x.getFullYear(),x.getMonth()+1,0).getDate();x.setDate(Math.min(f.getDate(),u));return x}}
function txt(x){{return x.getDate()+" de "+M[x.getMonth()]+" de "+x.getFullYear()}}
function eur(n){{return Math.round(n).toString().replace(/\\B(?=(\\d{{3}})+(?!\\d))/g,".")+" €"}}
function calc(){{var v=/^(\\d{{4}})-(\\d{{2}})-(\\d{{2}})$/.exec(d.value||"");if(!v){{r.textContent="Elige el día en que entregaste (o vas a entregar) las llaves.";return}}
var f=new Date(+v[1],v[2]-1,+v[3]),fin=mas(f,1),h=new Date(),hoy=new Date(h.getFullYear(),h.getMonth(),h.getDate()),dias=Math.round((fin-hoy)/864e5),q=parseFloat((a.value||"").replace(",","."));
var s="Tiene hasta el <b>"+txt(fin)+"</b> para devolverte la fianza"+(q>0?" (<b>"+eur(q)+"</b>, menos los descuentos que justifique)":"")+". ";
if(dias>1)s+="Quedan "+dias+" días.";else if(dias===1)s+="Queda 1 día.";else if(dias===0)s+="Hoy es el último día.";else s+="<b>Ya ha pasado el plazo</b> ("+(-dias)+(dias===-1?" día":" días")+"): pídesela por escrito con un burofax; desde el día siguiente al plazo te debe también el interés legal.";
r.innerHTML=s}}
d.addEventListener("change",calc);d.addEventListener("input",calc);a.addEventListener("input",calc);calc()}})();</script>
{fa_html}
<a class="cta" href="../">¿Buscas otro piso? Comprueba si el precio es justo</a>
<div class="card m"><b>Más guías:</b> <a href="../dejar-el-piso/">Carta para dejar el piso</a> · <a href="../reparaciones-alquiler/">Quién paga las reparaciones</a> · <a href="../mudanza/">Lista para la mudanza</a> · <a href="../contrato-de-alquiler/">Contrato de alquiler: cuánto dura</a> · <a href="../gastos-de-alquiler/">Dinero para alquilar</a> · <a href="../papeles-para-alquilar/">Papeles para alquilar</a> · <a href="../visitar-un-piso/">Qué mirar al visitar un piso</a> · """ + " · ".join(f'<a href="../{k}/alquiler/">Alquiler en {esc(c["n"])}</a>' for k, c in C.items()) + """</div>"""
os.makedirs(F("devolver-fianza"), exist_ok=True)
open(F("devolver-fianza", "index.html"), "w", encoding="utf-8").write(page(
    "¿Cuándo me devuelven la fianza del alquiler? Plazo y descuentos",
    desc_corta("El propietario tiene un mes desde que entregas las llaves para devolver la fianza. Calcula tu plazo, qué pueden descontar y cómo reclamarla.", " Gratis."),
    "devolver-fianza/", body, [("Vivible", "../"), ("Devolver la fianza", None)], fa_ld))
urls.insert(13, BASE + "devolver-fianza/")

# ---------- repartir el alquiler (repartir-alquiler/): «cómo repartir el alquiler de un piso compartido», «calculadora dividir
# alquiler por habitaciones», «quién paga más en un piso compartido». Calculadora (mitad a partes iguales por las zonas comunes y
# mitad según los metros de cada habitación, con un extra por baño propio o balcón; los gastos a partes iguales) y tabla por
# ciudad con la habitación media y el piso de 3 dormitorios entero (precios.json). El método es una propuesta, no una cifra de mercado.
assert "repartir-alquiler" not in C
M2T = 90
tr_r = "".join(f'<tr><td><a href="../{k}/habitacion/">{esc(c["n"])}</a></td><td><b>{fmt(c["hab"])} €</b></td><td>{fmt(c["alquiler"] * M2T)} €</td><td>{fmt(c["alquiler"] * M2T / 3)} €</td></tr>' for k, c in sorted(C.items(), key=lambda kc: kc[1]["hab"]))
mb = min(C.values(), key=lambda c: c["hab"]); mc = max(C.values(), key=lambda c: c["hab"])
inp = "font:16px Inter,system-ui,sans-serif;min-height:44px;width:100%;box-sizing:border-box;padding:0 8px;border:1px solid #d6d0c4;border-radius:10px;background:#fff"
ra_html, ra_ld = faq([
    ("¿Cómo se reparte el alquiler en un piso compartido?",
     "Lo más justo suele ser pagar a partes iguales lo que todos usáis (cocina, salón, baño común, pasillo) y repartir el resto según el tamaño de cada habitación. Con esta calculadora la mitad del alquiler se reparte a partes iguales y la otra mitad según los metros, con un extra para quien tiene baño propio o balcón."),
    ("¿Quien tiene la habitación más grande paga más?",
     "Es lo habitual: tiene más espacio solo para él. Si las habitaciones son muy parecidas, pagar lo mismo es más sencillo; si una es claramente mayor, tiene baño propio o da a la calle, lo normal es que pague algo más."),
    ("¿Cómo se reparten la luz, el agua e internet?",
     "Normalmente a partes iguales, porque todos los usáis. Si alguien pasa mucho más tiempo en casa o tiene aparatos que gastan mucho (un radiador, por ejemplo), podéis acordar que ponga algo más."),
    ("¿Tenemos que firmar todos el contrato?",
     "Es lo más seguro: así todos tenéis los derechos de inquilino. Mira si el contrato dice que respondéis «solidariamente»: entonces el propietario puede reclamar a cualquiera de vosotros el alquiler entero si alguien deja de pagar."),
    ("¿Cuánto cuesta una habitación en piso compartido?",
     f"Depende mucho de la ciudad: de media, desde unos {fmt(mb['hab'])} € al mes en {mb['n']} hasta unos {fmt(mc['hab'])} € en {mc['n']}, sin gastos."),
])
body = f"""<h1>Cómo repartir el alquiler de un piso compartido: calculadora</h1>
<p>Si compartís piso y las habitaciones no son iguales, pagar lo mismo no siempre es justo. Escribe el alquiler y los metros de cada habitación: la calculadora reparte a partes iguales las zonas comunes y el resto según el tamaño, y te da lo que paga cada uno para enviarlo al grupo.</p>
<div class="card" id="rf"><b>Vuestro piso</b>
<div style="display:flex;flex-wrap:wrap;gap:10px;margin:10px 0 4px"><label class="m" style="flex:1 1 150px">Alquiler al mes (€)<br><input type="number" inputmode="decimal" min="0" id="ra" value="1200" style="{inp}"></label>
<label class="m" style="flex:1 1 150px">Gastos al mes (€, opcional)<br><input type="number" inputmode="decimal" min="0" id="rg" placeholder="Luz, agua, internet" style="{inp}"></label></div>
<div id="rh"></div>
<div style="display:flex;flex-wrap:wrap;gap:8px;margin-top:6px"><button type="button" id="rmas" class="vbt">+ Añadir habitación</button><button type="button" id="rmen" class="vbt">− Quitar la última</button></div></div>
<div class="card" aria-live="polite"><b>Lo que paga cada uno</b><div id="rr" class="m" style="margin-top:6px"></div>
<a id="rw" class="vbt" style="display:inline-flex;align-items:center;text-decoration:none;margin-top:10px" target="_blank" rel="noopener">Enviar el reparto por WhatsApp</a></div>
<p class="m">Cómo se calcula: la mitad del alquiler se reparte a partes iguales (cocina, salón, baño común) y la otra mitad según los metros de cada habitación; el baño propio suma un 15 % a sus metros y el balcón o la ventana a la calle, un 5 %. Los gastos van a partes iguales. Es una propuesta: lo importante es que todos estéis de acuerdo.</p>
<h2 style="font:700 21px/1.2 Fraunces,Georgia,serif;margin:24px 0 0">Habitación o piso entero entre tres, por ciudad</h2>
<div class="card"><table class="cmp"><caption class="m" style="text-align:left;padding-bottom:6px">Habitación media al mes frente a un piso de {M2T} m² (3 dormitorios) alquilado entero y dividido entre tres, sin gastos</caption><tr><th scope="col">Ciudad</th><th scope="col">Habitación</th><th scope="col">Piso de {M2T} m²</th><th scope="col">Entre 3</th></tr>{tr_r}</table>
<p class="m">Habitación: precio medio de cada ciudad. Piso: alquiler medio por m² de la ciudad × {M2T} m². Cifras orientativas (<a href="../como-calculamos/">cómo calculamos</a>).</p></div>
<style>.vbt{{font:600 14px Inter,system-ui,sans-serif;min-height:44px;padding:0 14px;border:1px solid #d6d0c4;border-radius:10px;background:#fff;color:#1d2321;cursor:pointer}}
.rhb{{display:flex;flex-wrap:wrap;gap:8px 12px;align-items:center;padding:10px 0;border-top:1px solid #f1ede6}}.rhb input[type=text]{{flex:1 1 130px}}.rhb input[type=number]{{flex:0 0 90px;width:90px}}
.rhb label{{display:flex;gap:6px;align-items:center;min-height:44px;cursor:pointer}}.rhb input[type=checkbox]{{width:22px;height:22px;margin:0;accent-color:#1f6f54}}
#rr table{{width:100%;border-collapse:collapse}}#rr td{{padding:6px 4px;border-top:1px solid #f1ede6;text-align:right}}#rr td:first-child{{text-align:left}}#rr b{{color:#1d2321}}</style>
<script>(function(){{var H=document.getElementById("rh"),A=document.getElementById("ra"),G=document.getElementById("rg"),R=document.getElementById("rr"),W=document.getElementById("rw"),IN="{inp}";
var D=[14,11,9];
function eur(x){{return Math.round(x).toLocaleString("es-ES")+" €"}}
function fila(n,m){{var d=document.createElement("div");d.className="rhb";
d.innerHTML='<input type="text" maxlength="30" aria-label="Nombre" style="'+IN+'"><input type="number" inputmode="decimal" min="1" aria-label="Metros" style="'+IN+'"><span class="m">m²</span><label class="m"><input type="checkbox" data-t="b">Baño propio</label><label class="m"><input type="checkbox" data-t="e">Balcón o exterior</label>';
var i=d.querySelectorAll("input");i[0].value="Habitación "+n;i[1].value=m;H.appendChild(d)}}
function calc(){{var fs=[].slice.call(H.querySelectorAll(".rhb")),a=Math.max(0,+A.value||0),g=Math.max(0,+G.value||0),n=fs.length,p=[],t=0;
fs.forEach(function(f){{var i=f.querySelectorAll("input"),m=Math.max(0,+i[1].value||0),w=m*(1+(i[2].checked?.15:0)+(i[3].checked?.05:0));p.push({{n:(i[0].value||"").trim()||"Habitación",w:w}});t+=w}});
if(!a||!n){{R.textContent="Escribe el alquiler y al menos una habitación.";W.style.display="none";return}}
var tb=document.createElement("table"),tx="Reparto del alquiler ("+eur(a)+(g?" + "+eur(g)+" de gastos":"")+"):";
var hd=tb.insertRow();["","Alquiler",g?"Con gastos":""].forEach(function(s){{var c=hd.insertCell();c.textContent=s}});
p.forEach(function(x){{var al=a/2/n+(t?a/2*x.w/t:a/2/n),r=tb.insertRow(),c=r.insertCell();c.textContent=x.n;c=r.insertCell();c.textContent=eur(al);c=r.insertCell();
var b=document.createElement("b");b.textContent=g?eur(al+g/n):"";c.appendChild(b);if(!g){{r.cells[1].innerHTML="";var bb=document.createElement("b");bb.textContent=eur(al);r.cells[1].appendChild(bb)}}
tx+="\\n· "+x.n+": "+eur(al+g/n)}});
R.innerHTML="";R.appendChild(tb);var q=document.createElement("p");q.textContent="A partes iguales serían "+eur((a+g)/n)+" cada uno.";R.appendChild(q);
W.style.display="";W.href="https://wa.me/?text="+encodeURIComponent(tx+"\\nCalculado con Vivible: "+location.href.split("#")[0])}}
D.forEach(function(m,i){{fila(i+1,m)}});
document.getElementById("rmas").addEventListener("click",function(){{var n=H.children.length;if(n<8){{fila(n+1,10);calc()}}}});
document.getElementById("rmen").addEventListener("click",function(){{if(H.children.length>1){{H.removeChild(H.lastChild);calc()}}}});
document.getElementById("rf").addEventListener("input",calc);document.getElementById("rf").addEventListener("change",calc);calc()}})();</script>
{ra_html}
<a class="cta" href="../">¿Has visto una habitación? Comprueba si el precio es justo</a>
<div class="card m"><b>Más guías:</b> <a href="../independizarse/">Cuánto cuesta independizarse</a> · <a href="../contrato-de-alquiler/">Contrato de alquiler: cuánto dura</a> · <a href="../papeles-para-alquilar/">Papeles para alquilar</a> · <a href="../gastos-de-alquiler/">Dinero para alquilar</a> · <a href="../visitar-un-piso/">Qué mirar al visitar un piso</a> · """ + " · ".join(f'<a href="../{k}/habitacion/">Habitación en {esc(c["n"])}</a>' for k, c in C.items()) + """</div>"""
os.makedirs(F("repartir-alquiler"), exist_ok=True)
open(F("repartir-alquiler", "index.html"), "w", encoding="utf-8").write(page(
    "Cómo repartir el alquiler de un piso compartido: calculadora",
    desc_corta("Calcula cuánto paga cada uno en un piso compartido según los metros de su habitación, el baño propio y el balcón, y envía el reparto por WhatsApp.", " Gratis."),
    "repartir-alquiler/", body, [("Vivible", "../"), ("Repartir el alquiler", None)], ra_ld))
urls.insert(13, BASE + "repartir-alquiler/")

# ---------- ahorrar para comprar (ahorrar-para-comprar/): «cuánto tiempo se tarda en ahorrar para comprar un piso», «cuánto hay
# que ahorrar para la entrada de un piso en <ciudad>». Ahorros con gastos() (20 % de entrada, ITP, NOT y TAS: las mismas cifras que
# gastos-de-compra/ y sueldo-para-comprar/) para el piso medio de M2A m² y el del distrito más barato; tiempo = ahorros ÷ lo que apartas al mes,
# sin intereses ni subidas de precio. Calculadora con lo que ahorras al mes y lo que ya tienes.
assert "ahorrar-para-comprar" not in C
AHM = [300, 500, 800]
def tiempo(m):
    m = max(0, math.ceil(m))
    a, r = divmod(m, 12)
    if not m: return "ya lo tienes"
    t = (f"{a} año{'s' if a != 1 else ''}" if a else "") + (" y " if a and r else "") + (f"{r} mes{'es' if r != 1 else ''}" if r else "")
    return t
fil = []
for k, c in C.items():
    pubs = [d for d in c["d"] if not dprice(c, d)[2]] or list(c["d"])  # distrito más barato con precio publicado, como barrios-baratos/
    bd = min(pubs, key=lambda d: dprice(c, d)[0])
    pm, pb = c["venta"] * M2A, dprice(c, bd)[0] * M2A
    fil.append((k, c, gastos(pm, c)[2], bd, gastos(pb, c)[2], pm, pb))
fil.sort(key=lambda x: x[2])
tr_a = "".join(f'<tr><td><a href="../{k}/sueldo-para-comprar/">{esc(c["n"])}</a></td><td>{fmt(a)} €</td>' + "".join(f"<td>{dec(a / m / 12)}</td>" for m in AHM) + "</tr>" for k, c, a, *_ in fil)
fb, fc = fil[0], fil[-1]
mad = next(x for x in fil if x[0] == "madrid") if "madrid" in C else fc
DA = json.dumps([[c["n"], k, round(a), bd, round(ab)] for k, c, a, bd, ab, *_ in fil], ensure_ascii=False).replace("</", "<\\/")
ah_html, ah_ld = faq([
    ("¿Cuánto hay que ahorrar para comprar un piso?",
     f"Lo normal es tener ahorrado entre un {round(20 + min(c['itp'] for c in C.values()) + NOT * 100)} % y un {round(20 + max(c['itp'] for c in C.values()) + NOT * 100)} % del precio: el 20 % de entrada que no financia el banco, el impuesto de compra (entre el {pct(min(c['itp'] for c in C.values()))} % y el {pct(max(c['itp'] for c in C.values()))} % de ITP según la comunidad, si es de segunda mano) y alrededor de un {dec(NOT * 100)} % de notaría, registro y gestoría más la tasación. "
     f"Para un piso medio de {M2A} m², desde unos {fmt(fb[2])} € en {fb[1]['n']} hasta unos {fmt(fc[2])} € en {fc[1]['n']}."),
    ("¿Cuánto tiempo se tarda en ahorrar para comprar un piso?",
     f"Ahorrando 500 € al mes, juntar lo necesario para un piso medio de {M2A} m² lleva {tiempo(fb[2] / 500)} en {fb[1]['n']} y {tiempo(fc[2] / 500)} en {fc[1]['n']}. "
     f"En el distrito más barato de cada ciudad se tarda menos; por ejemplo, {tiempo(fb[4] / 500)} en {fb[3]} ({fb[1]['n']})."),
    (f"¿Cuánto hay que ahorrar para comprar un piso en {mad[1]['n']}?",
     f"Para un piso medio de {M2A} m² (unos {fmt(mad[5])} €), unos {fmt(mad[2])} €. En {mad[3]}, el distrito más barato, unos {fmt(mad[4])} € (piso de unos {fmt(mad[6])} €). "
     f"Con 500 € al mes, {tiempo(mad[2] / 500)} y {tiempo(mad[4] / 500)} respectivamente."),
    ("¿Se puede comprar un piso sin tener el 20 % ahorrado?",
     "Para la primera vivienda de jóvenes y familias con hijos hay avales públicos que permiten que el banco financie hasta el 95 %: pregunta en tu banco o en tu comunidad. Aun así necesitas tener ahorrado el impuesto de compra y los gastos, que el banco no presta."),
    ("¿Cómo puedo tardar menos en ahorrar la entrada?",
     "Comprar entre dos reduce el tiempo a la mitad; mirar en los distritos más baratos baja mucho la cifra; y algunas comunidades rebajan el impuesto de compra a jóvenes o familias numerosas. Un piso algo más pequeño también cuenta: cada 10 m² menos es un 14 % menos de ahorros en un piso de 70 m²."),
])
body = f"""<h1>¿Cuánto tiempo tardo en ahorrar para comprar un piso? Calculadora</h1>
<p>Para comprar con hipoteca necesitas tener ahorrado el 20 % del precio más el impuesto y los gastos. Escribe cuánto puedes apartar al mes y lo que ya tienes, y verás cuánto tardarías en juntarlo en cada ciudad, para un piso medio de {M2A} m² y para uno en el distrito más barato.</p>
<div class="card"><form id="ahf" onsubmit="return false" style="display:flex;flex-wrap:wrap;gap:10px"><label class="m" style="flex:1 1 150px"><b>Ahorro al mes (€)</b><input id="ahm" type="number" inputmode="numeric" min="0" step="50" value="500"></label>
<label class="m" style="flex:1 1 150px"><b>Ya tengo ahorrado (€)</b><input id="ahy" type="number" inputmode="numeric" min="0" step="1000" placeholder="0"></label></form>
<div id="ahr" aria-live="polite" class="m" style="margin-top:10px"></div></div>
<h2 style="font:700 21px/1.2 Fraunces,Georgia,serif;margin:24px 0 0">Años ahorrando para un piso medio, por ciudad</h2>
<div class="card"><table class="cmp"><caption class="m" style="text-align:left;padding-bottom:6px">Ahorros necesarios para un piso de {M2A} m² de segunda mano al precio medio de cada ciudad y años que se tarda en juntarlos ahorrando 300, 500 u 800 € al mes</caption><tr><th scope="col">Ciudad</th><th scope="col">Ahorros</th>""" + "".join(f'<th scope="col">{m} €/mes<br>(años)</th>' for m in AHM) + f"""</tr>{tr_a}</table>
<p class="m">Ahorros: 20 % de entrada, ITP de la comunidad y notaría, registro, gestoría y tasación (<a href="../como-calculamos/">cómo calculamos</a>). Sin contar lo que rinda el dinero ahorrado ni lo que suban los precios mientras tanto. Cifras orientativas.</p></div>
{ah_html}
<a class="cta" href="../#op=venta">¿Has visto un piso en venta? Comprueba si su precio es justo</a>
<div class="card m"><b>Más guías:</b> <a href="../gastos-de-compra/">Gastos de comprar</a> · <a href="../hipoteca/">Cuota de la hipoteca</a> · <a href="../sueldo/">Qué piso puedo pagar con mi sueldo</a> · <a href="../barrios-baratos/">Barrios más baratos</a> · """ + " · ".join(f'<a href="../{k}/comprar-con-presupuesto/">Comprar en {esc(c["n"])}</a>' for k, c in C.items()) + f"""</div>
<style>#ahf input{{display:block;width:100%;box-sizing:border-box;margin-top:4px;font:16px Inter,system-ui,sans-serif;padding:10px;min-height:44px;border:1px solid #d6d0c4;border-radius:10px;background:#fff;color:#1d2321}}
#ahr table{{width:100%;border-collapse:collapse}}#ahr td,#ahr th{{padding:6px 4px;border-top:1px solid #f1ede6;text-align:right;vertical-align:top}}#ahr td:first-child,#ahr th:first-child{{text-align:left}}#ahr small{{display:block}}</style>
<script>(function(){{var D={DA},m=document.getElementById("ahm"),y=document.getElementById("ahy"),o=document.getElementById("ahr");
function f(n){{return String(Math.round(n)).replace(/\\B(?=(\\d{{3}})+(?!\\d))/g,".")}}
function t(x){{x=Math.max(0,Math.ceil(x-1e-9));if(!x)return"ya lo tienes";var a=Math.floor(x/12),r=x%12;return(a?a+(a==1?" año":" años"):"")+(a&&r?" y ":"")+(r?r+(r==1?" mes":" meses"):"")}}
function c(){{var a=+m.value||0,h=Math.max(0,+y.value||0);o.innerHTML="";if(a<0||a>100000||h>10000000){{o.textContent="Escribe cuánto ahorras al mes, por ejemplo 500.";return}}
var tb=document.createElement("table"),r=tb.insertRow();["Ciudad","Piso medio","Distrito más barato"].forEach(function(s){{var e=document.createElement("th");e.scope="col";e.textContent=s;r.appendChild(e)}});
D.forEach(function(d){{var r=tb.insertRow(),e=r.insertCell();e.textContent=d[0];[[d[2],""],[d[4],d[3]]].forEach(function(p){{var e=r.insertCell(),b=document.createElement("b"),s=document.createElement("small"),fal=Math.max(0,p[0]-h);
b.textContent=fal<=0?"ya lo tienes":a>0?t(fal/a):"—";e.appendChild(b);s.textContent=f(p[0])+" €"+(p[1]?" · "+p[1]:"");e.appendChild(s)}})}});
o.appendChild(tb);if(!(a>0))o.insertAdjacentHTML("afterbegin","<p>Escribe cuánto ahorras al mes para ver el tiempo.</p>")}}
m.addEventListener("input",c);y.addEventListener("input",c);c()}})()</script>"""
os.makedirs(F("ahorrar-para-comprar"), exist_ok=True)
open(F("ahorrar-para-comprar", "index.html"), "w", encoding="utf-8").write(page(
    "¿Cuánto tiempo tardo en ahorrar para comprar un piso? Calculadora",
    desc_corta(f"Ahorros para comprar un piso de {M2A} m²: desde {fmt(fb[2])} € en {fb[1]['n']} hasta {fmt(fc[2])} € en {fc[1]['n']}. Calcula en cuánto tiempo los juntas.", " Gratis."),
    "ahorrar-para-comprar/", body, [("Vivible", "../"), ("Ahorrar para comprar", None)], ah_ld))
urls.insert(14, BASE + "ahorrar-para-comprar/")

# ---------- cómo calculamos (como-calculamos/): de dónde salen los datos y qué fórmulas usa cada guía, para que quien
# lee una cifra sepa cuánto fiarse de ella (y Google vea las fuentes). Todo sale de precios.json y de las constantes de arriba.
assert "como-calculamos" not in C
pctx = lambda x: dec(x * 100, 1).rstrip("0").rstrip(",")
def n_pub(c, i): return sum(v[i] is not None for v in c["d"].values())
tr_m = "".join(f'<tr><td><a href="../{k}/">{esc(c["n"])}</a></td><td style="text-align:left;white-space:normal">{esc(c["mes"])}</td><td>{len(c["d"])}</td><td>{n_pub(c, 0)}</td><td>{n_pub(c, 1)}</td></tr>' for k, c in C.items())
nd = sum(len(c["d"]) for c in C.values()); nv = sum(n_pub(c, 0) for c in C.values()); na = sum(n_pub(c, 1) for c in C.values())
MET = [
    ("Precio por m² de cada distrito", f"Es el precio medio que publica idealista para ese distrito (venta en €/m² y alquiler en €/m² al mes), con el mes de cada ciudad que ves en la tabla. Cuando idealista no publica uno de los dos, lo estimamos a partir del otro y de la media de la ciudad, y lo marcamos con * o «estimado»."),
    ("Habitación", f"Precio medio de una habitación en piso compartido de cada ciudad. En cada distrito lo ajustamos según lo caro que es allí el alquiler respecto a la media de la ciudad, y redondeamos a 5 €."),
    ("Ahorros para comprar", f"El {pctx(1 - .8)} % de entrada, el impuesto de compra (ITP de la comunidad si es de segunda mano; 10 % de IVA más AJD si es nueva) y alrededor de un {pctx(NOT)} % más {fmt(TAS)} € de notaría, registro, gestoría y tasación."),
    ("Hipoteca", f"Préstamo del 80 % del precio a {ANOS} años con un tipo fijo del {pctx(TIN)} % y cuota constante (sistema francés). Tu banco puede ofrecerte otro tipo: en la calculadora de la hipoteca puedes cambiarlo."),
    ("Sueldo recomendado", f"Para alquilar, que el alquiler no pase del {pctx(ESF)} % de lo que ganas al mes (en habitación, sumando unos {fmt(GHAB)} € de gastos). Para comprar, que la cuota de la hipoteca no pase del {pctx(ESC)} % en las guías; el informe de un piso concreto admite hasta el 33 %. Hablamos siempre de sueldo neto."),
    ("Piso tipo", f"Para comparar ciudades y distritos usamos un piso de {M2A} m², que suele tener 2 dormitorios; un estudio, 40 m²; y uno de 3 dormitorios, 90 m²."),
    ("Rentabilidad del alquiler", "Rentabilidad bruta: lo que se cobraría de alquiler en un año dividido entre el precio de compra, sin restar impuestos, comunidad, IBI, seguros ni meses vacíos."),
    ("Análisis de un piso concreto", "Cuando pegas un anuncio o escribes una dirección, comparamos el precio con la media del distrito según los metros y lo que ofrece el piso, y buscamos en OpenStreetMap el transporte, los comercios, los colegios, los parques y el ruido de la zona. Si OpenStreetMap no responde, el informe lo dice y la nota no cuenta esos datos."),
]
mt_html = "".join(f'<h3 style="font-size:16px;margin:14px 0 2px">{esc(t)}</h3><p style="margin:0">{esc(x)}</p>' for t, x in MET)
cm_html, cm_ld = faq([
    ("¿De dónde salen los precios de Vivible?", f"De los precios medios por distrito que publica idealista ({mes_txt}) y del precio medio de una habitación en cada ciudad. Los impuestos de compra son el tipo general de cada comunidad autónoma."),
    ("¿Cada cuánto se actualizan los datos?", f"Revisamos los precios cada mes; la última revisión es del {int(P['actualizado'][8:])} de {MESES[int(P['actualizado'][5:7]) - 1]} de {P['actualizado'][:4]}. El mes de los datos de cada ciudad aparece en su página."),
    ("¿Es una tasación oficial?", "No. Son estimaciones orientativas con precios medios: sirven para saber si un piso está caro o barato y cuánto dinero necesitas, pero no sustituyen a una tasación ni al consejo de tu banco o tu gestor."),
    ("¿Qué significa «estimado»?", f"Que idealista no publica ese precio para ese distrito y lo calculamos a partir del otro precio del distrito y de la media de la ciudad. De los {nd} distritos, {nv} tienen precio de venta publicado y {na} de alquiler."),
])
body = f"""<h1>Cómo calculamos: de dónde salen los datos de Vivible</h1>
<p>Todas las cifras de Vivible salen de los mismos datos, en la portada y en cada guía. Aquí tienes de dónde vienen y cómo se calculan, para que sepas cuánto fiarte de cada número.</p>
<div class="card"><table class="cmp"><caption class="m" style="text-align:left;padding-bottom:6px">Mes de los precios de idealista y distritos con precio publicado en cada ciudad (el resto se estima)</caption><tr><th scope="col">Ciudad</th><th scope="col" style="text-align:left">Datos de</th><th scope="col">Distritos</th><th scope="col">Venta</th><th scope="col">Alquiler</th></tr>{tr_m}</table>
<p class="m">Habitaciones: precio medio de idealista (2.º trimestre de 2026); en Valencia, Sevilla, Alicante, Zaragoza y Murcia, media de idealista, Spotahome y Brains. Impuesto de compra: tipo general de cada comunidad (algunas tienen rebajas para jóvenes o familias). Barrios de Madrid, Barcelona y Valencia: división oficial de cada ayuntamiento.</p></div>
<div class="card"><h2 style="font:700 21px/1.2 Fraunces,Georgia,serif;margin:0 0 4px">Las fórmulas</h2>{mt_html}</div>
{cm_html}
<a class="cta" href="../">Analiza un piso concreto gratis</a>
<div class="card m"><b>Guías:</b> <a href="../precios/">Comparar las 10 ciudades</a> · <a href="../hipoteca/">Cuota de la hipoteca</a> · <a href="../gastos-de-compra/">Gastos de comprar</a> · <a href="../gastos-de-alquiler/">Dinero para alquilar</a> · <a href="../sueldo/">Qué piso puedo pagar</a> · <a href="../rentabilidad/">Rentabilidad del alquiler</a></div>"""
os.makedirs(F("como-calculamos"), exist_ok=True)
open(F("como-calculamos", "index.html"), "w", encoding="utf-8").write(page(
    "Cómo calculamos: fuentes y fórmulas de Vivible",
    "De dónde salen los precios por distrito, la habitación, los impuestos, la hipoteca y el sueldo recomendado de Vivible, y qué datos son estimados.",
    "como-calculamos/", body, [("Vivible", "../"), ("Cómo calculamos", None)], cm_ld))
urls.append(BASE + "como-calculamos/")

# ---------- pasos para comprar un piso (pasos-para-comprar/): «pasos para comprar un piso», «cómo comprar un piso paso a paso»,
# «qué es el contrato de arras», «cuánto se paga en las arras»; lista de pasos para marcar en el móvil y, por ciudad, cuánto dinero
# sale de tus ahorros en las arras y en la firma (mismas cifras que gastos-de-compra/: gastos(), M2A y precios.json)
assert "pasos-para-comprar" not in C
ARR = .10  # señal de arras habitual (no es obligatoria: se pacta)
PAS = [
    ("1. Antes de buscar", [
        "Calcula cuánto puedes pagar: la cuota de la hipoteca no debería pasar de un tercio de lo que ganas.",
        "Junta los ahorros: el banco suele prestar como mucho el 80 % del precio, así que pagas tú el 20 % más los impuestos y los gastos (alrededor de un 30 % en total).",
        "Pide a dos o tres bancos un estudio previo de la hipoteca para saber cuánto te prestarían.",
    ]),
    ("2. Buscar y elegir el piso", [
        "Compara el precio con lo que cuesta el m² en su distrito antes de hacer una oferta.",
        "Visita el piso con calma y vuelve a otra hora: humedades, ruido, luz, edificio y barrio.",
        "Pide la nota simple del Registro de la Propiedad: quién es el dueño y si tiene hipotecas o embargos.",
        "Pide el certificado de deudas con la comunidad, el último recibo del IBI y el certificado energético.",
    ]),
    ("3. Oferta y contrato de arras", [
        "Haz la oferta por escrito y negocia: el precio del anuncio no es el definitivo.",
        "Firma un contrato de arras con la señal pactada (suele ser un 10 %) y una fecha límite para firmar ante notario.",
        "Mejor arras penitenciales: si te echas atrás pierdes la señal; si se echa atrás el vendedor, te devuelve el doble.",
        "Si dependes de la hipoteca, intenta que el contrato diga qué pasa si el banco no te la concede.",
    ]),
    ("4. La hipoteca", [
        "El banco tasa el piso (la tasación la pagas tú) y presta sobre el precio o la tasación, el más bajo de los dos.",
        "Compara ofertas: tipo fijo o variable, comisiones y productos que te obligan a contratar (seguros, nómina).",
        "El banco te da la oferta vinculante (FEIN) al menos 10 días antes de firmar: léela con calma.",
        "Antes de firmar vas al notario, gratis, para que te explique la hipoteca y resuelva tus dudas.",
    ]),
    ("5. La firma ante notario", [
        "Se firman a la vez la compraventa y la hipoteca. Lleva el DNI y lo que te pida el notario o el banco.",
        "Pagas el resto del precio (normalmente con un cheque o transferencia del banco) y te dan las llaves.",
        "Comprueba antes que el piso está como lo viste y que no quedan deudas de comunidad.",
    ]),
    ("6. Después de firmar", [
        "Paga el impuesto de compra (ITP o IVA y AJD) en el plazo de tu comunidad; suele encargarse la gestoría.",
        "Inscribe la escritura en el Registro de la Propiedad a tu nombre.",
        "Cambia a tu nombre la luz, el agua, el gas e internet, y avisa a la comunidad de vecinos.",
        "Domicilia el IBI: desde el año siguiente lo pagas tú.",
    ]),
]
npas = sum(len(xs) for _, xs in PAS)
def pc_fila(k, c):
    med = c["venta"] * M2A
    imp, otros, tot = gastos(med, c)
    sen = med * ARR
    return f'<tr><td><a href="../{k}/gastos-de-compra/">{esc(c["n"])}</a></td><td>{fmt(med)} €</td><td>{fmt(sen)} €</td><td>{fmt(tot - sen)} €</td><td><b>{fmt(tot)} €</b></td></tr>'
mad = C.get("madrid") or next(iter(C.values()))
mm = mad["venta"] * M2A; mi, mo, mt = gastos(mm, mad)
pc_html, pc_ld = faq([
    ("¿Cuáles son los pasos para comprar un piso?",
     "Calcular cuánto puedes pagar y juntar los ahorros, buscar el piso y revisar sus papeles (nota simple, deudas de comunidad), hacer una oferta y firmar el contrato de arras, conseguir la hipoteca, firmar ante notario y, después, pagar el impuesto de compra, inscribir el piso en el Registro y cambiar los suministros a tu nombre."),
    ("¿Qué es el contrato de arras?",
     "Es el contrato que firmas al reservar el piso: pagas una señal (suele ser un 10 % del precio, pero se pacta) y fijáis una fecha para firmar ante notario. En las arras penitenciales, si el comprador se echa atrás pierde la señal y si se echa atrás el vendedor devuelve el doble."),
    ("¿Cuánto tiempo se tarda en comprar un piso?",
     "Desde que firmas las arras hasta la firma ante notario suelen pasar entre uno y tres meses: es el tiempo que necesita el banco para tasar el piso y aprobar la hipoteca, más los 10 días que la ley te da para leer la oferta vinculante."),
    ("¿Cuánto dinero necesito para comprar un piso?",
     f"Alrededor de un 30 % del precio: el 20 % que no cubre la hipoteca, el impuesto de compra y los gastos de notaría, registro, gestoría y tasación. En {mad['n']}, un piso medio de {M2A} m² (unos {fmt(mm)} €) pide unos {fmt(mt)} € de ahorros."),
    ("¿Quién paga la plusvalía y el IBI al comprar un piso?",
     "La plusvalía municipal la paga quien vende. El IBI del año de la compra lo paga quien era dueño el 1 de enero, aunque es habitual pactar repartirlo según los meses; desde el año siguiente lo pagas tú."),
])
ps_lis = "".join(f'<div class="card"><h2 class="vh">{esc(t)}</h2>' + "".join(
    f'<label class="vc"><input type="checkbox" data-k="{i}-{j}"><span>{esc(x)}</span></label>' for j, x in enumerate(xs)) + "</div>" for i, (t, xs) in enumerate(PAS))
body = f"""<h1>Pasos para comprar un piso (2026): de los ahorros a las llaves</h1>
<p>Comprar un piso lleva unos meses y varios papeles. Aquí tienes los {npas} pasos en orden, para marcar en el móvil a medida que avanzas, y cuánto dinero sale de tus ahorros en cada momento en las 10 ciudades. Lo que marques se queda guardado en este móvil.</p>
<div class="card" id="vp" aria-live="polite"><b id="vn">0 de {npas} hechos</b><div class="vb"><i id="vi"></i></div>
<button type="button" id="vr" class="vbt">Empezar de nuevo</button></div>
{ps_lis}
<div class="card"><table class="cmp"><caption class="m" style="text-align:left;padding-bottom:6px">Dinero de tus ahorros para un piso medio de {M2A} m² de segunda mano: la señal de arras (un {pctx(ARR)} %) y lo que pagas al firmar (el resto de la entrada del 20 %, el ITP y los gastos)</caption><tr><th scope="col">Ciudad</th><th scope="col">Precio</th><th scope="col">Arras</th><th scope="col">En la firma</th><th scope="col">Total</th></tr>{"".join(pc_fila(k, c) for k, c in C.items())}</table>
<p class="m">El resto del precio lo paga la hipoteca. Precios medios de idealista; impuesto: tipo general de cada comunidad. <a href="../como-calculamos/">Cómo calculamos</a>.</p></div>
<style>.vh{{font:700 19px/1.2 Fraunces,Georgia,serif;margin:0 0 6px}}.vc{{display:flex;gap:10px;align-items:flex-start;padding:9px 0;min-height:44px;box-sizing:border-box;border-top:1px solid #f1ede6;cursor:pointer}}.vc input{{width:22px;height:22px;margin:2px 0 0;flex:none;accent-color:#1f6f54}}.vc input:checked+span{{color:#5f6b66;text-decoration:line-through}}
.vb{{height:8px;background:#efebe4;border-radius:99px;margin:8px 0 10px;overflow:hidden}}.vb i{{display:block;height:100%;width:0;background:#1f6f54}}.vbt{{font:600 14px Inter,system-ui,sans-serif;min-height:44px;padding:0 14px;border:1px solid #d6d0c4;border-radius:10px;background:#fff;color:#1d2321;cursor:pointer}}
#vp{{position:sticky;top:0;z-index:1}}</style>
<script>(function(){{var K="vivible.compra",cs=[].slice.call(document.querySelectorAll(".vc input")),s={{}};
try{{s=JSON.parse(localStorage.getItem(K)||"{{}}")||{{}}}}catch(e){{}}
function pinta(){{var k=0;cs.forEach(function(c){{if(c.checked)k++}});document.getElementById("vn").textContent=k+" de "+cs.length+" hechos";document.getElementById("vi").style.width=(k*100/cs.length)+"%"}}
function guarda(){{var o={{}};cs.forEach(function(c){{if(c.checked)o[c.getAttribute("data-k")]=1}});try{{localStorage.setItem(K,JSON.stringify(o))}}catch(e){{}}}}
cs.forEach(function(c){{c.checked=!!s[c.getAttribute("data-k")];c.addEventListener("change",function(){{guarda();pinta()}})}});
document.getElementById("vr").addEventListener("click",function(){{if(cs.some(function(c){{return c.checked}})&&!confirm("¿Borrar lo que has marcado y empezar de cero?"))return;cs.forEach(function(c){{c.checked=false}});guarda();pinta()}});pinta()}})();</script>
{pc_html}
<a class="cta" href="../">¿Has visto un piso? Pega el anuncio y comprueba si el precio es justo</a>
<div class="card m"><b>Más guías:</b> <a href="../ahorrar-para-comprar/">Cuánto tardo en ahorrar</a> · <a href="../vender-un-piso/">Cuánto pagas al vender un piso</a> · <a href="../hipoteca/">Cuota de la hipoteca</a> · <a href="../gastos-de-compra/">Gastos de comprar</a> · <a href="../sueldo/">Qué piso puedo pagar con mi sueldo</a> · <a href="../mudanza/">Lista para la mudanza</a> · <a href="../visitar-un-piso/">Qué mirar al visitar un piso</a> · """ + " · ".join(f'<a href="../{k}/venta/">Comprar en {esc(c["n"])}</a>' for k, c in C.items()) + """</div>"""
os.makedirs(F("pasos-para-comprar"), exist_ok=True)
open(F("pasos-para-comprar", "index.html"), "w", encoding="utf-8").write(page(
    "Pasos para comprar un piso: arras, hipoteca, notario y gastos",
    desc_corta(f"Los {npas} pasos para comprar un piso en orden, del ahorro a las llaves: nota simple, arras, hipoteca, notario e impuestos, y cuánto pagas en cada momento.", " Gratis."),
    "pasos-para-comprar/", body, [("Vivible", "../"), ("Pasos para comprar", None)], pc_ld))
urls.insert(15, BASE + "pasos-para-comprar/")

# ---------- vender un piso (vender-un-piso/): «cuánto pago a Hacienda al vender un piso», «IRPF venta vivienda», «ganancia
# patrimonial venta piso», «quién paga la plusvalía». Calculadora con la escala del ahorro del IRPF (2025 en adelante, Ley 7/2024:
# 19 % hasta 6.000 €, 21 % hasta 50.000, 23 % hasta 200.000, 27 % hasta 300.000 y 30 % desde ahí) aplicada solo a esta ganancia;
# exenciones por reinversión en vivienda habitual y mayores de 65 (LIRPF art. 33.4 y 38). Precio medio por ciudad: precios.json.
assert "vender-un-piso" not in C
TRA = [(6000, .19), (50000, .21), (200000, .23), (300000, .27), (None, .30)]
def irpf_ahorro(g):
    t, ant = 0, 0
    for lim, p in TRA:
        tope = g if lim is None else min(g, lim)
        if tope > ant: t += (tope - ant) * p
        ant = lim if lim is not None else ant
        if lim is None or g <= lim: break
    return t
assert irpf_ahorro(6000) == 1140 and round(irpf_ahorro(50000)) == 1140 + 9240
ej_g = 60000; ej_t = irpf_ahorro(ej_g)
tv = "".join(f'<tr><td><a href="../{k}/venta/">{esc(c["n"])}</a></td><td>{fmt(c["venta"])} €</td><td><b>{fmt(c["venta"] * M2A)} €</b></td></tr>' for k, c in sorted(C.items(), key=lambda kc: -kc[1]["venta"]))
tt = "".join(f'<tr><td>{"Desde " + fmt(TRA[i-1][0]) + " €" if lim is None else ("Hasta " + fmt(lim) + " €" if i == 0 else fmt(TRA[i-1][0]) + " a " + fmt(lim) + " €")}</td><td><b>{round(p*100)} %</b></td></tr>' for i, (lim, p) in enumerate(TRA))
ve_html, ve_ld = faq([
    ("¿Cuánto se paga a Hacienda por vender un piso?",
     f"Se paga IRPF solo por lo que ganas: la diferencia entre lo que te pagan (menos los gastos de la venta) y lo que te costó (con los impuestos y gastos de la compra y las obras de mejora). Esa ganancia tributa del 19 % al 30 % por tramos. Por ejemplo, con {fmt(ej_g)} € de ganancia pagas unos {fmt(ej_t)} €."),
    ("¿Cuándo no hay que pagar IRPF al vender un piso?",
     "Si vendes tu vivienda habitual y reinviertes el dinero en otra vivienda habitual en dos años, la ganancia reinvertida no paga. Tampoco pagas si tienes 65 años o más y vendes tu vivienda habitual, ni si vendes por menos de lo que te costó (entonces tienes una pérdida)."),
    ("¿Qué gastos se pueden restar al vender un piso?",
     "Del precio de compra puedes sumar el impuesto que pagaste (ITP o IVA y AJD), notaría, registro, gestoría y las obras de mejora con factura. Del precio de venta puedes restar la comisión de la inmobiliaria, el certificado energético y la plusvalía municipal. Si el piso estuvo alquilado, hay que restar lo que se amortizó."),
    ("¿Quién paga la plusvalía municipal al vender un piso?",
     "La paga quien vende, al ayuntamiento, normalmente en 30 días hábiles desde la firma. Depende del valor catastral del suelo y de los años que lo has tenido, y no se paga si has vendido sin ganancia."),
    ("¿Cuándo se paga el IRPF de la venta de un piso?",
     "En la declaración de la renta del año siguiente a la venta. Hacienda no te lo retiene al vender, así que conviene guardar ese dinero aparte."),
])
body = f"""<h1>¿Cuánto pago a Hacienda al vender un piso? Calculadora 2026</h1>
<p>Al vender un piso solo pagas IRPF por lo que <b>ganas</b>, no por el precio entero. Pon lo que te costó y por cuánto lo vendes y te decimos la ganancia, cuánto le toca a Hacienda y lo que te queda.</p>
<div class="card" id="vc"><b>Calcula el IRPF de tu venta</b>
<div style="display:flex;flex-wrap:wrap;gap:10px;margin:10px 0 4px">
<label class="m" style="flex:1 1 150px">Lo compré por (€)<br><input type="number" id="vq" inputmode="decimal" min="0" step="1000" placeholder="Por ejemplo, 180000" class="vin"></label>
<label class="m" style="flex:1 1 150px">Impuestos, gastos y obras de la compra (€)<br><input type="number" id="vg" inputmode="decimal" min="0" step="100" placeholder="Vacío = 10 %" class="vin"></label>
<label class="m" style="flex:1 1 150px">Lo vendo por (€)<br><input type="number" id="vv" inputmode="decimal" min="0" step="1000" placeholder="Por ejemplo, 250000" class="vin"></label>
<label class="m" style="flex:1 1 150px">Gastos de la venta (€)<br><input type="number" id="vx" inputmode="decimal" min="0" step="100" placeholder="Agencia…" class="vin"></label></div>
<div id="vr" aria-live="polite" class="m">Escribe el precio de compra y el de venta.</div></div>
<style>.vin{{font:16px Inter,system-ui,sans-serif;min-height:44px;width:100%;box-sizing:border-box;padding:0 8px;border:1px solid #d6d0c4;border-radius:10px}}</style>
<h2 style="font:700 21px/1.2 Fraunces,Georgia,serif;margin:24px 0 0">Cuánto se paga por la ganancia</h2>
<div class="card"><table class="cmp"><caption class="m" style="text-align:left;padding-bottom:6px">Escala del ahorro del IRPF (estatal y autonómica juntas) desde 2025. Cada tramo de la ganancia paga su porcentaje.</caption><tr><th scope="col">Ganancia</th><th scope="col">Tipo</th></tr>{tt}</table>
<p class="m">Si en el mismo año tienes otras ganancias o intereses, se suman y pueden subir de tramo. Es una estimación: la cifra exacta te la da la declaración de la renta.</p></div>
<h2 style="font:700 21px/1.2 Fraunces,Georgia,serif;margin:24px 0 0">Cuándo no pagas</h2>
<div class="card"><ul style="margin:0;padding-left:20px"><li><b>Reinviertes en tu nueva casa:</b> si vendes tu vivienda habitual y metes el dinero en otra vivienda habitual en los dos años siguientes (o los dos anteriores), esa parte no paga.</li>
<li><b>Tienes 65 años o más</b> y vendes tu vivienda habitual.</li>
<li><b>Vendes sin ganar:</b> si te costó más de lo que te pagan, no hay IRPF y la pérdida puede compensar otras ganancias.</li></ul>
<p class="m">Vivienda habitual: donde has vivido al menos tres años seguidos (o hasta ahora, si la vendes por una causa que lo justifique).</p></div>
<h2 style="font:700 21px/1.2 Fraunces,Georgia,serif;margin:24px 0 0">Cuánto vale hoy un piso en cada ciudad</h2>
<div class="card"><table class="cmp"><caption class="m" style="text-align:left;padding-bottom:6px">Precio medio de venta por m² y de un piso de {M2A} m² ({esc(mes_txt)}, idealista)</caption><tr><th scope="col">Ciudad</th><th scope="col">€/m²</th><th scope="col">Piso de {M2A} m²</th></tr>{tv}</table>
<p class="m">Cada ciudad por distritos en su página. <a href="../como-calculamos/">Cómo calculamos</a>.</p></div>
<script>(function(){{var T=[[6000,.19],[50000,.21],[200000,.23],[300000,.27],[1/0,.30]];
function n(id){{var v=parseFloat((document.getElementById(id).value||"").replace(",","."));return v>0?v:0}}
function eur(x){{return Math.round(x).toString().replace(/\\B(?=(\\d{{3}})+(?!\\d))/g,".")+" €"}}
function irpf(g){{var t=0,a=0;for(var i=0;i<T.length;i++){{var l=T[i][0];if(g>a)t+=(Math.min(g,l)-a)*T[i][1];a=l;if(g<=l)break}}return t}}
var r=document.getElementById("vr");
function calc(){{var q=n("vq"),v=n("vv");if(!q||!v){{r.textContent="Escribe el precio de compra y el de venta.";return}}
var gv=(document.getElementById("vg").value||"").trim(),g=gv===""?q*.10:n("vg"),x=n("vx"),c=q+g,s=v-x,ga=s-c,h;
var p="Te costó <b>"+eur(c)+"</b>"+(gv===""?" (contamos un 10 % de impuestos y gastos de la compra)":"")+" y recibes <b>"+eur(s)+"</b> después de los gastos de la venta. ";
if(ga<=0){{r.innerHTML=p+"No hay ganancia, así que <b>no pagas IRPF</b>"+(ga<0?" y la pérdida de "+eur(-ga)+" puede compensar otras ganancias del año":"")+".";return}}
h=irpf(ga);r.innerHTML=p+"Ganas <b>"+eur(ga)+"</b>: a Hacienda le tocan unos <b>"+eur(h)+"</b> ("+(h*100/ga).toFixed(1).replace(".",",")+" % de la ganancia) y te quedan <b>"+eur(s-h)+"</b>. Si es tu vivienda habitual y reinviertes en otra, o tienes 65 años o más, puede que no pagues nada."}}
["vq","vg","vv","vx"].forEach(function(i){{document.getElementById(i).addEventListener("input",calc)}});calc()}})();</script>
{ve_html}
<a class="cta" href="../">¿Vas a comprar otro? Comprueba si el precio es justo</a>
<div class="card m"><b>Más guías:</b> <a href="../cuanto-vale-mi-piso/">¿Cuánto vale mi piso?</a> · <a href="../gastos-de-compra/">Gastos de comprar</a> · <a href="../pasos-para-comprar/">Pasos para comprar un piso</a> · <a href="../hipoteca/">Cuota de la hipoteca</a> · <a href="../rentabilidad/">Rentabilidad del alquiler</a> · """ + " · ".join(f'<a href="../{k}/venta/">Comprar en {esc(c["n"])}</a>' for k, c in C.items()) + """</div>"""
os.makedirs(F("vender-un-piso"), exist_ok=True)
open(F("vender-un-piso", "index.html"), "w", encoding="utf-8").write(page(
    "¿Cuánto pago a Hacienda al vender un piso? Calculadora IRPF 2026",
    desc_corta("Calcula el IRPF de vender un piso: la ganancia tributa del 19 % al 30 %. Qué gastos restar, cuándo no se paga (reinversión, mayores de 65) y la plusvalía.", " Gratis."),
    "vender-un-piso/", body, [("Vivible", "../"), ("Vender un piso", None)], ve_ld))
urls.insert(16, BASE + "vender-un-piso/")

# ---------- ¿Cuánto vale mi piso? (cuanto-vale-mi-piso/): «cuánto vale mi piso», «calcular valor de mi vivienda», «tasar piso gratis».
# Solo precios.json (precio medio de venta y alquiler por m² del distrito; si idealista no lo publica, la estimación de dprice, avisándolo).
assert "cuanto-vale-mi-piso" not in C
VM = {k: [c["n"], [[d, round(s), round(r, 1), int(es or er), slug(d)] for d, (s, r, es, er) in sorted(((d, dprice(c, d)) for d in c["d"]), key=lambda x: x[0])]] for k, c in C.items()}
VMJ = json.dumps(VM, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
tvm = "".join(f'<tr><td><a href="../{k}/">{esc(c["n"])}</a></td><td>{fmt(c["venta"] * 60)} €</td><td><b>{fmt(c["venta"] * 80)} €</b></td><td>{fmt(c["venta"] * 100)} €</td><td>{fmt(c["alquiler"] * 80)} €/mes</td></tr>' for k, c in sorted(C.items(), key=lambda kc: -kc[1]["venta"]))
mx = max(C.values(), key=lambda c: c["venta"]); mn = min(C.values(), key=lambda c: c["venta"])
vm_html, vm_ld = faq([
    ("¿Cómo sé cuánto vale mi piso?",
     "Multiplica los metros cuadrados por el precio medio por m² de tu distrito: es lo que piden de media por pisos parecidos al tuyo. Luego ajústalo: suben el precio la planta alta con ascensor, la terraza, la reforma reciente y la luz; lo bajan un bajo interior, no tener ascensor o necesitar obra. La calculadora de arriba hace la cuenta con los datos de tu distrito."),
    (f"¿Cuánto vale un piso de 80 m² en {mx['n']}?",
     f"Con el precio medio de {mx['n']} ({fmt(mx['venta'])} €/m², {mes_txt}), un piso de 80 m² vale unos {fmt(mx['venta'] * 80)} €. En {mn['n']}, la más barata de las 10 ciudades, el mismo piso vale unos {fmt(mn['venta'] * 80)} €. En cada distrito cambia mucho: mira el tuyo en la calculadora."),
    ("¿El precio medio es lo que me pagarán?",
     "No exactamente: es el precio que se pide en los anuncios. Al final se suele cerrar algo por debajo tras negociar, y el banco del comprador tasará el piso para darle la hipoteca. Úsalo como punto de partida para poner un precio razonable."),
    ("¿Cuánto podría cobrar si alquilo mi piso?",
     "Multiplica los metros por el alquiler medio por m² al mes de tu distrito. La calculadora te lo da junto al precio de venta, para que compares vender o alquilar."),
    ("¿Cuánto me cuesta una tasación oficial?",
     "Una tasación hecha por una sociedad de tasación homologada la pide el banco cuando hay hipoteca. Si solo quieres orientarte para vender, basta con comparar con el precio medio del distrito y con anuncios de pisos parecidos cerca del tuyo."),
])
body = f"""<h1>¿Cuánto vale mi piso? Calcula su precio gratis</h1>
<p>Elige tu ciudad, tu distrito y los metros. Te decimos cuánto vale tu piso según el <b>precio medio de los pisos en venta</b> en tu distrito y cuánto podrías cobrar si lo alquilas. Sin registrarte y sin dar tu teléfono.</p>
<div class="card" id="mc"><b>Calcula el valor de tu piso</b>
<div style="display:flex;flex-wrap:wrap;gap:10px;margin:10px 0 4px">
<label class="m" style="flex:1 1 140px">Ciudad<br><select id="mk" class="vin"></select></label>
<label class="m" style="flex:1 1 180px">Distrito<br><select id="md" class="vin"></select></label>
<label class="m" style="flex:1 1 110px">Metros (m²)<br><input type="number" id="mm" inputmode="decimal" min="10" max="1000" step="1" placeholder="Por ejemplo, 80" class="vin"></label></div>
<div id="mr" aria-live="polite" class="m">Escribe los metros de tu piso.</div></div>
<style>.vin{{font:16px Inter,system-ui,sans-serif;min-height:44px;width:100%;box-sizing:border-box;padding:0 8px;border:1px solid #d6d0c4;border-radius:10px;background:#fff}}</style>
<h2 style="font:700 21px/1.2 Fraunces,Georgia,serif;margin:24px 0 0">Qué sube y qué baja el precio</h2>
<div class="card"><ul style="margin:0;padding-left:20px"><li><b>Suben:</b> planta alta con ascensor, exterior y con luz, terraza o balcón, reforma reciente, garaje o trastero incluidos, buen certificado energético.</li>
<li><b>Bajan:</b> bajo o interior, sin ascensor a partir de un segundo, necesita reforma, mucho ruido, gastos de comunidad altos o una derrama pendiente.</li></ul>
<p class="m">Compara también con anuncios de pisos parecidos en tu calle: si el tuyo es mejor, puedes pedir algo más que la media; si necesita obra, algo menos.</p></div>
<h2 style="font:700 21px/1.2 Fraunces,Georgia,serif;margin:24px 0 0">Cuánto vale un piso en cada ciudad</h2>
<div class="card"><table class="cmp"><caption class="m" style="text-align:left;padding-bottom:6px">Con el precio medio de venta y de alquiler por m² de cada ciudad ({esc(mes_txt)}, idealista)</caption><tr><th scope="col">Ciudad</th><th scope="col">60 m²</th><th scope="col">80 m²</th><th scope="col">100 m²</th><th scope="col">Alquiler 80 m²</th></tr>{tvm}</table>
<p class="m">Cada ciudad por distritos en su página. <a href="../como-calculamos/">Cómo calculamos</a>.</p></div>
<script>(function(){{var V={VMJ};
var k=document.getElementById("mk"),d=document.getElementById("md"),m=document.getElementById("mm"),r=document.getElementById("mr");
function eur(x){{return Math.round(x).toString().replace(/\\B(?=(\\d{{3}})+(?!\\d))/g,".")+" €"}}
function esc(s){{return String(s).replace(/[&<>"']/g,function(c){{return"&#"+c.charCodeAt(0)+";"}})}}
Object.keys(V).forEach(function(c){{k.add(new Option(V[c][0],c))}});
function dis(sel){{d.innerHTML="";V[k.value][1].forEach(function(x){{d.add(new Option(x[0],x[4]))}});if(sel)d.value=sel;if(d.selectedIndex<0)d.selectedIndex=0}}
function calc(){{var t=parseFloat((m.value||"").replace(",",".")),c=V[k.value],x=c[1][d.selectedIndex];
if(!(t>=10&&t<=1000)){{r.textContent="Escribe los metros de tu piso.";return}}
r.innerHTML="Un piso de <b>"+Math.round(t)+" m²</b> en "+esc(x[0])+" ("+esc(c[0])+") vale unos <b>"+eur(t*x[1])+"</b> ("+eur(x[1])+"/m²). Si lo alquilas, podrías cobrar unos <b>"+eur(t*x[2])+" al mes</b>."+(x[3]?" <i>idealista no publica todos los precios de este distrito: parte de la cifra es una estimación a partir de la otra.</i>":"")+" <a href=\\"../"+k.value+"/"+x[4]+"/\\">Ver precios de "+esc(x[0])+"</a>"}}
var q=new URLSearchParams(location.search);if(V[q.get("c")])k.value=q.get("c");dis(q.get("d"));if(+q.get("m"))m.value=+q.get("m");
k.addEventListener("change",function(){{dis();calc()}});d.addEventListener("change",calc);m.addEventListener("input",calc);calc()}})();</script>
{vm_html}
<a class="cta" href="../">¿Has visto un anuncio? Comprueba si su precio es justo</a>
<div class="card m"><b>Más guías:</b> <a href="../precio-metro-cuadrado/">Precio por metro cuadrado</a> · <a href="../vender-un-piso/">Cuánto pago a Hacienda al vender</a> · <a href="../rentabilidad/">Rentabilidad del alquiler</a> · <a href="../barrios/">¿En qué distrito está mi barrio?</a> · <a href="../precios/">Comparar las 10 ciudades</a> · """ + " · ".join(f'<a href="../{k}/venta/">Precio de la vivienda en {esc(c["n"])}</a>' for k, c in C.items()) + """</div>"""
os.makedirs(F("cuanto-vale-mi-piso"), exist_ok=True)
open(F("cuanto-vale-mi-piso", "index.html"), "w", encoding="utf-8").write(page(
    "¿Cuánto vale mi piso? Calculadora gratis por distritos (2026)",
    desc_corta("Calcula cuánto vale tu piso con el precio medio por m² de tu distrito en 10 ciudades, y cuánto cobrarías de alquiler. Sin registro.", " Gratis."),
    "cuanto-vale-mi-piso/", body, [("Vivible", "../"), ("¿Cuánto vale mi piso?", None)], vm_ld))
urls.insert(17, BASE + "cuanto-vale-mi-piso/")

# ---------- Precio por metro cuadrado (precio-metro-cuadrado/): «calcular precio metro cuadrado piso», «precio m2 vivienda».
# Solo precios.json (VM, el mismo dato por distrito que cuanto-vale-mi-piso/): divide precio entre metros y lo compara con la media del distrito.
assert "precio-metro-cuadrado" not in C
tpm = "".join(f'<tr><td><a href="../{k}/">{esc(c["n"])}</a></td><td><b>{fmt(c["venta"])} €/m²</b></td><td>{dec(c["alquiler"])} €/m² al mes</td></tr>' for k, c in sorted(C.items(), key=lambda kc: -kc[1]["venta"]))
pm_html, pm_ld = faq([
    ("¿Cómo se calcula el precio por metro cuadrado?",
     "Divide el precio del piso entre sus metros cuadrados. Por ejemplo, un piso de 240.000 € con 80 m² sale a 3.000 €/m². En alquiler es igual: 1.200 € al mes entre 80 m² son 15 €/m² al mes."),
    ("¿Qué metros uso, los útiles o los construidos?",
     "Los anuncios suelen dar los metros construidos (incluyen paredes y, a veces, parte de las zonas comunes), y los precios medios por m² también se calculan así. Si el anuncio solo da los útiles, el precio por m² te saldrá algo más alto de lo que es."),
    (f"¿Cuál es el precio medio del metro cuadrado en {mx['n']}?",
     f"Según idealista ({mes_txt}), {fmt(mx['venta'])} €/m² en venta y {dec(mx['alquiler'])} €/m² al mes en alquiler. En {mn['n']}, la más barata de las 10 ciudades, {fmt(mn['venta'])} €/m² en venta. Cada distrito cambia mucho: elígelo en la calculadora."),
    ("¿Un precio por m² más alto que la media es caro?",
     "No siempre. Un piso reformado, exterior, con ascensor o terraza suele estar por encima de la media; uno que necesita obra, por debajo. Si está más de un 15 % por encima y no tiene nada especial, merece la pena negociar."),
])
body = f"""<h1>Precio por metro cuadrado: calcúlalo y compáralo</h1>
<p>Escribe el precio y los metros del piso que has visto. Te decimos cuánto sale el <b>metro cuadrado</b> y si está por encima o por debajo de la media de su distrito, en venta o en alquiler.</p>
<div class="card" id="pc"><b>Calcula el precio por m²</b>
<div style="display:flex;flex-wrap:wrap;gap:10px;margin:10px 0 4px">
<label class="m" style="flex:1 1 130px">¿Venta o alquiler?<br><select id="po" class="vin"><option value="1">Venta</option><option value="2">Alquiler (al mes)</option></select></label>
<label class="m" style="flex:1 1 130px">Precio (€)<br><input type="number" id="pp" inputmode="decimal" min="1" step="1" placeholder="Por ejemplo, 240000" class="vin"></label>
<label class="m" style="flex:1 1 110px">Metros (m²)<br><input type="number" id="pm" inputmode="decimal" min="10" max="1000" step="1" placeholder="Por ejemplo, 80" class="vin"></label>
<label class="m" style="flex:1 1 140px">Ciudad<br><select id="pk" class="vin"></select></label>
<label class="m" style="flex:1 1 180px">Distrito<br><select id="pd" class="vin"></select></label></div>
<div id="pr" aria-live="polite" class="m">Escribe el precio y los metros.</div></div>
<style>.vin{{font:16px Inter,system-ui,sans-serif;min-height:44px;width:100%;box-sizing:border-box;padding:0 8px;border:1px solid #d6d0c4;border-radius:10px;background:#fff}}</style>
<h2 style="font:700 21px/1.2 Fraunces,Georgia,serif;margin:24px 0 0">Precio medio del metro cuadrado por ciudad</h2>
<div class="card"><table class="cmp"><caption class="m" style="text-align:left;padding-bottom:6px">Precio medio por m² en los anuncios ({esc(mes_txt)}, idealista)</caption><tr><th scope="col">Ciudad</th><th scope="col">Venta</th><th scope="col">Alquiler</th></tr>{tpm}</table>
<p class="m">Cada distrito en la página de su ciudad. <a href="../como-calculamos/">Cómo calculamos</a>.</p></div>
<script>(function(){{var V={VMJ};
var o=document.getElementById("po"),p=document.getElementById("pp"),m=document.getElementById("pm"),k=document.getElementById("pk"),d=document.getElementById("pd"),r=document.getElementById("pr");
function num(x,dd){{return x.toFixed(dd).replace(".",",").replace(/\\B(?=(\\d{{3}})+(?!\\d))/g,".")}}
function esc(s){{return String(s).replace(/[&<>"']/g,function(c){{return"&#"+c.charCodeAt(0)+";"}})}}
Object.keys(V).forEach(function(c){{k.add(new Option(V[c][0],c))}});
function dis(sel){{d.innerHTML="";V[k.value][1].forEach(function(x){{d.add(new Option(x[0],x[4]))}});if(sel)d.value=sel;if(d.selectedIndex<0)d.selectedIndex=0}}
function calc(){{var al=o.value==="2",pr=parseFloat((p.value||"").replace(",",".")),t=parseFloat((m.value||"").replace(",",".")),c=V[k.value],x=c[1][d.selectedIndex];
if(!(pr>0&&t>=10&&t<=1000)){{r.textContent="Escribe el precio y los metros.";return}}
var u=pr/t,med=al?x[2]:x[1],dd=al?1:0,ud=al?" €/m² al mes":" €/m²",dif=Math.round((u/med-1)*100);
var v=Math.abs(dif)<=5?"está <b>en la media</b> del distrito":dif>0?"está un <b>"+dif+" % por encima</b> de la media del distrito":"está un <b>"+(-dif)+" % por debajo</b> de la media del distrito";
r.innerHTML="Sale a <b>"+num(u,dd)+ud+"</b>. La media en "+esc(x[0])+" ("+esc(c[0])+") es "+num(med,dd)+ud+": "+v+"."+(dif>15?" Si no tiene nada especial (reforma, terraza, vistas), hay margen para negociar.":"")+(x[3]?" <i>idealista no publica todos los precios de este distrito: parte de la media es una estimación.</i>":"")+" <a href=\\"../"+k.value+"/"+x[4]+"/\\">Ver precios de "+esc(x[0])+"</a>"}}
var q=new URLSearchParams(location.search);if(V[q.get("c")])k.value=q.get("c");dis(q.get("d"));
[o,p,m,d].forEach(function(e){{e.addEventListener("input",calc);e.addEventListener("change",calc)}});k.addEventListener("change",function(){{dis();calc()}});calc()}})();</script>
{pm_html}
<a class="cta" href="../">Pega el anuncio y te decimos si su precio es justo</a>
<div class="card m"><b>Más guías:</b> <a href="../cuanto-vale-mi-piso/">¿Cuánto vale mi piso?</a> · <a href="../gastos-de-compra/">Gastos de comprar</a> · <a href="../barrios-baratos/">Barrios más baratos</a> · <a href="../precios/">Comparar las 10 ciudades</a> · """ + " · ".join(f'<a href="../{k}/venta/">Precio de la vivienda en {esc(c["n"])}</a>' for k, c in C.items()) + """</div>"""
os.makedirs(F("precio-metro-cuadrado"), exist_ok=True)
open(F("precio-metro-cuadrado", "index.html"), "w", encoding="utf-8").write(page(
    "Precio por metro cuadrado: calculadora y media por distrito (2026)",
    desc_corta("Calcula el precio por m² de un piso en venta o alquiler y compáralo con la media de su distrito en 10 ciudades (datos de idealista).", " Gratis."),
    "precio-metro-cuadrado/", body, [("Vivible", "../"), ("Precio por metro cuadrado", None)], pm_ld))
urls.insert(18, BASE + "precio-metro-cuadrado/")

# ---------- ¿Cuánto cuesta independizarse? (independizarse/): «cuánto dinero necesito para independizarme», «cuánto cuesta independizarse en <ciudad>».
# Solo precios.json y las reglas de las guías: habitación (hab + GHAB de gastos) o estudio de M2E m² (alquiler €/m²); al entrar, primer mes + fianza de un mes
# (garantía adicional de hasta dos meses más); sueldo neto para que no pase del 33 % (ESF).
assert "independizarse" not in C
IND = sorted(C.items(), key=lambda kc: kc[1]["hab"])
INJ = json.dumps([[k, c["n"], round(c["hab"]), round(c["alquiler"] * M2E)] for k, c in IND], ensure_ascii=False).replace("</", "<\\/")
tin = "".join(f'<tr><td><a href="../{k}/habitacion/">{esc(c["n"])}</a></td><td>{fmt(c["hab"])} €</td><td>{fmt(c["hab"] * 2)} €</td><td>{fmt((c["hab"] + GHAB) / ESF)} €</td><td>{fmt(c["alquiler"] * M2E)} €</td><td>{fmt(c["alquiler"] * M2E * 2)} €</td><td><b>{fmt(c["alquiler"] * M2E / ESF)} €</b></td></tr>' for k, c in IND)
ib, ic = IND[0][1], IND[-1][1]
eb = min(C.values(), key=lambda c: c["alquiler"]); ec = max(C.values(), key=lambda c: c["alquiler"])
in_html, in_ld = faq([
    ("¿Cuánto dinero necesito para independizarme?",
     f"Para entrar, lo normal es pagar el primer mes y un mes de fianza: el doble del alquiler. Una habitación en piso compartido te pide de {fmt(ib['hab'] * 2)} € en {ib['n']} a {fmt(ic['hab'] * 2)} € en {ic['n']}; un estudio de {M2E} m², de {fmt(eb['alquiler'] * M2E * 2)} € en {eb['n']} a {fmt(ec['alquiler'] * M2E * 2)} € en {ec['n']}. "
     "Si el propietario pide garantía adicional (hasta dos meses más), cuenta con hasta cuatro meses. Suma algo para muebles, menaje y las altas de luz e internet."),
    ("¿Cuánto tengo que ganar para independizarme?",
     f"Lo recomendable es que la vivienda no se lleve más del 33 % de lo que cobras al mes. Para una habitación (con unos {GHAB} € de gastos de luz, agua e internet) necesitas de {fmt((ib['hab'] + GHAB) / ESF)} € netos en {ib['n']} a {fmt((ic['hab'] + GHAB) / ESF)} € en {ic['n']}. "
     f"Para un estudio de {M2E} m², de {fmt(eb['alquiler'] * M2E / ESF)} € en {eb['n']} a {fmt(ec['alquiler'] * M2E / ESF)} € en {ec['n']}."),
    ("¿Habitación o estudio?",
     "La habitación es más barata y casi siempre incluye muebles, pero compartes cocina, baño y normas. El estudio te da intimidad, aunque pagas solo el alquiler y los gastos. Si tu sueldo no llega al del estudio en tu ciudad, empezar en una habitación te deja ahorrar para dar el salto."),
    ("¿Hay ayudas para jóvenes que se independizan?",
     "Existe el Bono Alquiler Joven y planes de vivienda de cada comunidad, con requisitos de edad e ingresos y plazos que cambian cada año. Consulta la web de vivienda de tu comunidad autónoma antes de firmar."),
])
body = f"""<h1>¿Cuánto cuesta independizarse? Habitación o estudio en 10 ciudades</h1>
<p>Lo que pagas al mes, lo que necesitas para entrar y lo que deberías ganar para irte a vivir solo o a un piso compartido. Con los precios medios de idealista ({esc(mes_txt)}).</p>
<div class="card" id="ic"><b>¿Dónde me llega con mi sueldo?</b>
<div style="display:flex;flex-wrap:wrap;gap:10px;margin:10px 0 4px">
<label class="m" style="flex:1 1 150px">Lo que cobras al mes, neto (€)<br><input type="number" id="is" inputmode="decimal" min="0" step="50" placeholder="Por ejemplo, 1300" class="vin"></label>
<label class="m" style="flex:1 1 150px">Ahorros para entrar (€, opcional)<br><input type="number" id="ia" inputmode="decimal" min="0" step="100" placeholder="Por ejemplo, 2000" class="vin"></label></div>
<div id="ir" aria-live="polite" class="m">Escribe lo que cobras al mes.</div></div>
<style>.vin{{font:16px Inter,system-ui,sans-serif;min-height:44px;width:100%;box-sizing:border-box;padding:0 8px;border:1px solid #d6d0c4;border-radius:10px;background:#fff}}#ir ul{{margin:6px 0 0;padding-left:20px}}</style>
<h2 style="font:700 21px/1.2 Fraunces,Georgia,serif;margin:24px 0 0">Habitación o estudio: lo que cuesta en cada ciudad</h2>
<div class="card" style="overflow-x:auto"><table class="cmp" style="font-size:13px"><caption class="m" style="text-align:left;padding-bottom:6px">Al mes, para entrar (primer mes + fianza) y sueldo neto recomendado (33 %). Estudio de {M2E} m².</caption><tr><th scope="col">Ciudad</th><th scope="col">Habitación</th><th scope="col">Entrar</th><th scope="col">Sueldo</th><th scope="col">Estudio</th><th scope="col">Entrar</th><th scope="col">Sueldo</th></tr>{tin}</table>
<p class="m">Si te piden garantía adicional, suma hasta dos meses más. Cada ciudad por distritos en su página de habitación. <a href="../como-calculamos/">Cómo calculamos</a>.</p></div>
<h2 style="font:700 21px/1.2 Fraunces,Georgia,serif;margin:24px 0 0">Antes de irte, ten en cuenta</h2>
<div class="card"><ul style="margin:0;padding-left:20px"><li><b>Gastos del mes:</b> en un estudio pagas tú la luz, el agua, el gas e internet; en una habitación se reparten (unos {GHAB} € al mes por persona).</li>
<li><b>Entrada:</b> primer mes y fianza; la inmobiliaria no te puede cobrar sus honorarios (los paga el propietario).</li>
<li><b>Colchón:</b> intenta tener ahorrados uno o dos meses de gastos por si surge algo.</li>
<li><b>Papeles:</b> nóminas, contrato de trabajo o un avalista si estudias. <a href="../papeles-para-alquilar/">Lista completa</a>.</li></ul></div>
<script>(function(){{var C={INJ},G={GHAB},E={ESF},M={M2E};
var s=document.getElementById("is"),a=document.getElementById("ia"),r=document.getElementById("ir");
function eur(x){{return Math.round(x).toString().replace(/\\B(?=(\\d{{3}})+(?!\\d))/g,".")+" €"}}
function y(l){{return l.length<2?l.join(""):l.slice(0,-1).join(", ")+" y "+l[l.length-1]}}
function calc(){{var sv=parseFloat((s.value||"").replace(",",".")),av=parseFloat((a.value||"").replace(",","."));
if(!(sv>0)){{r.textContent="Escribe lo que cobras al mes.";return}}
var tope=sv*E,es=[],hb=[],no=[];
C.forEach(function(c){{if(c[3]<=tope)es.push(['<a href="../'+c[0]+'/alquiler/">'+c[1]+'</a>',c[3]]);else if(c[2]+G<=tope)hb.push(['<a href="../'+c[0]+'/habitacion/">'+c[1]+'</a>',c[2]]);else no.push(c[1])}});
var h="Con "+eur(sv)+" al mes, lo recomendable es no pasar de <b>"+eur(tope)+"</b> en vivienda.<ul>";
if(es.length)h+="<li><b>Estudio de "+M+" m²:</b> te llega en "+y(es.map(function(x){{return x[0]}}))+".</li>";
if(hb.length)h+="<li><b>Habitación:</b> en "+y(hb.map(function(x){{return x[0]}}))+" (el estudio se te iría de presupuesto).</li>";
if(no.length)h+="<li><b>Justo:</b> en "+y(no)+" incluso una habitación pasa del 33 %.</li>";
h+="</ul>";
if(av>0){{var ok=C.filter(function(c){{return c[3]*2<=av}}).length,okh=C.filter(function(c){{return c[2]*2<=av}}).length;
h+="Con "+eur(av)+" ahorrados cubres la entrada (primer mes + fianza) de un estudio en "+ok+" de las 10 ciudades y de una habitación en "+okh+"."}}
r.innerHTML=h}}
var q=new URLSearchParams(location.search);if(+q.get("s"))s.value=+q.get("s");
[s,a].forEach(function(e){{e.addEventListener("input",calc)}});calc()}})();</script>
{in_html}
<a class="cta" href="../">¿Has visto un piso o una habitación? Comprueba si su precio es justo</a>
<div class="card m"><b>Más guías:</b> <a href="../gastos-de-alquiler/">Dinero para alquilar</a> · <a href="../repartir-alquiler/">Repartir el alquiler</a> · <a href="../papeles-para-alquilar/">Papeles para alquilar</a> · <a href="../sueldo/">Qué piso puedo pagar con mi sueldo</a> · <a href="../mudanza/">Lista para la mudanza</a> · <a href="../visitar-un-piso/">Qué mirar al visitar un piso</a> · """ + " · ".join(f'<a href="../{k}/habitacion/">Habitación en {esc(c["n"])}</a>' for k, c in C.items()) + """</div>"""
os.makedirs(F("independizarse"), exist_ok=True)
open(F("independizarse", "index.html"), "w", encoding="utf-8").write(page(
    "¿Cuánto cuesta independizarse? Habitación o estudio (2026)",
    desc_corta(f"Lo que cuesta independizarse en 10 ciudades: habitación desde {fmt(ib['hab'])} € al mes, cuánto necesitas para entrar y cuánto ganar. Con calculadora.", " Gratis."),
    "independizarse/", body, [("Vivible", "../"), ("Independizarse", None)], in_ld))
urls.insert(19, BASE + "independizarse/")

# ---------- mudanza (mudanza/): «qué hacer al mudarse de piso», «checklist mudanza», «a quién avisar del cambio de domicilio»;
# lista para marcar en el móvil antes, durante y después de la mudanza (sin cifras: solo trámites y consejos)
assert "mudanza" not in C
MUD = [
    ("Antes: dos o tres semanas", [
        "Si dejas un alquiler, avisa al propietario por escrito con 30 días de antelación como mínimo (o lo que diga tu contrato).",
        "Pide presupuesto a dos o tres empresas de mudanzas, o reserva una furgoneta y pide ayuda con tiempo.",
        "Pregunta en el ayuntamiento si hace falta permiso para aparcar el camión delante del portal.",
        "Deshazte de lo que no vas a llevar: véndelo, regálalo o llévalo al punto limpio.",
        "Pide ya el traslado o el alta de internet en la casa nueva: la instalación puede tardar días. Pregunta si tienes permanencia.",
    ]),
    ("Luz, agua, gas y seguro", [
        "Casa vieja: haz foto de los contadores el día que sales y da de baja o cambia de titular lo que esté a tu nombre.",
        "Casa nueva: haz foto de los contadores el día que entras y pon a tu nombre la luz, el gas y el agua (o pregunta al propietario cómo se pagan).",
        "Revisa la potencia de luz contratada y la tarifa: es buen momento para cambiar si pagas de más.",
        "Seguro de hogar: cambia la dirección del que tienes o contrata uno para la casa nueva.",
    ]),
    ("Cambiar la dirección", [
        "Empadrónate en el ayuntamiento de tu casa nueva: te lo piden para el centro de salud, el colegio y muchas ayudas.",
        "Pide centro de salud y médico nuevos si cambias de zona.",
        "Hacienda: cambia tu domicilio fiscal en la web de la Agencia Tributaria.",
        "Tráfico (DGT): cambia la dirección del carné de conducir y del coche si tienes.",
        "Avisa al banco, a tu trabajo y a la Seguridad Social si te escriben por carta.",
        "Cambia la dirección de entrega en las tiendas por internet y en tus suscripciones.",
        "Si te preocupa perder cartas, Correos tiene un servicio de pago para reenviártelas un tiempo.",
    ]),
    ("El día que dejas el piso de alquiler", [
        "Haz fotos y vídeo con fecha de cómo dejas cada habitación: te servirán para recuperar la fianza.",
        "Déjalo limpio y como lo recibiste; el desgaste normal por el uso no te lo pueden descontar.",
        "Entrega todas las llaves y pide un papel o un mensaje con la fecha: desde ese día cuenta el mes para devolverte la fianza.",
        "Deja al propietario una cuenta bancaria para que te devuelva la fianza.",
    ]),
    ("El día que entras en tu casa nueva", [
        "Haz fotos con fecha de cómo está todo, también de los desperfectos, y mándaselas al propietario por correo o mensaje.",
        "Prueba el agua caliente, la calefacción, los enchufes y los electrodomésticos; avisa por escrito de lo que no funcione.",
        "Localiza la llave de paso del agua, el cuadro eléctrico y la llave del gas.",
        "Si has comprado, cambia el bombín de la cerradura: no sabes cuántas copias de las llaves hay.",
        "Pon tu nombre en el buzón y preséntate a los vecinos.",
    ]),
]
nmud = sum(len(xs) for _, xs in MUD)
mu_html, mu_ld = faq([
    ("¿Qué hay que hacer al mudarse de piso?",
     "Antes: avisar al propietario si dejas un alquiler, organizar el transporte y pedir el alta de internet. Después: cambiar la luz, el agua y el gas, empadronarte en tu nueva dirección y avisar del cambio a Hacienda, Tráfico, el banco y tu trabajo. Y hacer fotos con fecha al salir y al entrar."),
    ("¿Es obligatorio empadronarse al cambiar de casa?",
     "Sí. Todas las personas que viven en España tienen que estar inscritas en el padrón del municipio donde viven habitualmente. Además, el padrón te lo piden para el centro de salud, el colegio, muchas ayudas y para votar donde vives."),
    ("¿Puedo empadronarme en un piso de alquiler sin permiso del propietario?",
     "Sí. Normalmente basta con tu DNI o NIE y el contrato de alquiler; el propietario no tiene que dar permiso. Si vives en una habitación, el contrato de la habitación sirve igual."),
    ("¿Con cuánta antelación tengo que avisar si dejo el piso de alquiler?",
     "Con la ley de alquileres puedes irte a partir de los seis meses avisando con 30 días de antelación como mínimo. Si tu contrato lo dice, pagarás un mes de alquiler por cada año que quede, o la parte proporcional."),
    ("¿Qué hago con la luz y el agua cuando me mudo?",
     "En el piso que dejas, apunta (con foto) la lectura de los contadores y da de baja o cambia de titular lo que esté a tu nombre. En el nuevo, haz lo mismo al entrar y pon los contratos a tu nombre, o acuerda con el propietario cómo se pagan."),
])
lis = "".join(f'<div class="card"><h2 class="vh">{esc(t)}</h2>' + "".join(
    f'<label class="vc"><input type="checkbox" data-k="{i}-{j}"><span>{esc(x)}</span></label>' for j, x in enumerate(xs)) + "</div>" for i, (t, xs) in enumerate(MUD))
body = f"""<h1>Mudanza: lista de todo lo que hay que hacer al cambiarte de piso</h1>
<p>Con las cajas es fácil olvidar un trámite y darte cuenta meses después. Esta lista tiene {nmud} cosas que hacer antes, durante y después de mudarte, si alquilas o si has comprado. Márcalas en el móvil según las haces: se quedan guardadas en este móvil.</p>
<div class="card" id="vp" aria-live="polite"><b id="vn">0 de {nmud} hechas</b><div class="vb"><i id="vi"></i></div>
<button type="button" id="vr" class="vbt">Empezar otra mudanza</button></div>
{lis}
<style>.vh{{font:700 19px/1.2 Fraunces,Georgia,serif;margin:0 0 6px}}.vc{{display:flex;gap:10px;align-items:flex-start;padding:9px 0;min-height:44px;box-sizing:border-box;border-top:1px solid #f1ede6;cursor:pointer}}.vc input{{width:22px;height:22px;margin:2px 0 0;flex:none;accent-color:#1f6f54}}.vc input:checked+span{{color:#5f6b66;text-decoration:line-through}}
.vb{{height:8px;background:#efebe4;border-radius:99px;margin:8px 0 10px;overflow:hidden}}.vb i{{display:block;height:100%;width:0;background:#1f6f54}}.vbt{{font:600 14px Inter,system-ui,sans-serif;min-height:44px;padding:0 14px;border:1px solid #d6d0c4;border-radius:10px;background:#fff;color:#1d2321;cursor:pointer}}
#vp{{position:sticky;top:0;z-index:1}}</style>
<script>(function(){{var K="vivible.mudanza",cs=[].slice.call(document.querySelectorAll(".vc input")),s={{}};
try{{s=JSON.parse(localStorage.getItem(K)||"{{}}")||{{}}}}catch(e){{}}
function pinta(){{var k=0;cs.forEach(function(c){{if(c.checked)k++}});document.getElementById("vn").textContent=k+" de "+cs.length+" hechas";document.getElementById("vi").style.width=(k*100/cs.length)+"%"}}
function guarda(){{var o={{}};cs.forEach(function(c){{if(c.checked)o[c.getAttribute("data-k")]=1}});try{{localStorage.setItem(K,JSON.stringify(o))}}catch(e){{}}}}
cs.forEach(function(c){{c.checked=!!s[c.getAttribute("data-k")];c.addEventListener("change",function(){{guarda();pinta()}})}});
document.getElementById("vr").addEventListener("click",function(){{if(cs.some(function(c){{return c.checked}})&&!confirm("¿Borrar lo que has marcado y empezar de cero?"))return;cs.forEach(function(c){{c.checked=false}});guarda();pinta()}});pinta()}})();</script>
<p class="m">¿Dejas un alquiler? Avisa al propietario con el <a href="../dejar-el-piso/">modelo de carta para dejar el piso</a> y mira <a href="../devolver-fianza/">cuándo te tienen que devolver la fianza</a> y <a href="../contrato-de-alquiler/">cuánto dura tu contrato</a>. ¿Aún buscas casa? <a href="../visitar-un-piso/">Qué mirar al visitar un piso</a>.</p>
{mu_html}
<a class="cta" href="../">¿Aún no tienes piso? Pega el anuncio y comprueba si el precio es justo</a>
<div class="card m"><b>Más guías:</b> <a href="../devolver-fianza/">Cuándo te devuelven la fianza</a> · <a href="../contrato-de-alquiler/">Contrato de alquiler: cuánto dura</a> · <a href="../papeles-para-alquilar/">Papeles para alquilar</a> · <a href="../pasos-para-comprar/">Pasos para comprar un piso</a> · <a href="../independizarse/">Cuánto cuesta independizarse</a> · <a href="../visitar-un-piso/">Qué mirar al visitar un piso</a> · """ + " · ".join(f'<a href="../{k}/">Vivir en {esc(c["n"])}</a>' for k, c in C.items()) + """</div>"""
os.makedirs(F("mudanza"), exist_ok=True)
open(F("mudanza", "index.html"), "w", encoding="utf-8").write(page(
    "Mudanza: lista de qué hacer al cambiarte de piso (2026)",
    desc_corta(f"Checklist de mudanza con {nmud} pasos: avisar al casero, luz, agua e internet, empadronarte, cambiar la dirección en Hacienda y Tráfico y la fianza.", " Gratis."),
    "mudanza/", body, [("Vivible", "../"), ("Mudanza", None)], mu_ld))
urls.insert(20, BASE + "mudanza/")

# ---------- dejar el piso (dejar-el-piso/): «carta para dejar el piso de alquiler», «modelo carta preaviso alquiler»,
# «cuánto tiempo antes hay que avisar para dejar un piso». Generador de la carta (solo en el navegador: no se guarda ni se envía nada)
# con los plazos de la LAU: art. 11 (irte antes, desde los 6 meses y con 30 días), art. 9.1 (no renovar: 30 días antes del fin del
# contrato o de cada prórroga), art. 10.1 (tras los 5 o 7 años: 2 meses; en la prórroga de hasta 3 años, 1 mes) y art. 36.4 (fianza).
assert "dejar-el-piso" not in C
DPZ = [
    ("Irte antes de que acabe el contrato", "30 días", "Desde los 6 meses. Si el contrato lo dice, puede pedirte un mes de alquiler por cada año que falte (la parte proporcional si es menos)."),
    ("No renovar al acabar el contrato o una prórroga anual", "30 días antes", "Hasta llegar a los 5 años (7 si el propietario es una empresa). Sin indemnización."),
    ("Al cumplir los 5 (o 7) años", "2 meses antes", "Si nadie avisa, se alarga año a año hasta 3 años más; en ese tiempo, avisa 1 mes antes de que acabe cada año."),
]
dj_html, dj_ld = faq([
    ("¿Con cuánta antelación tengo que avisar para dejar el piso de alquiler?",
     "Con 30 días como mínimo, tanto si te vas antes de que acabe el contrato (a partir de los seis meses) como si no quieres renovarlo. Si ya has cumplido los cinco años (siete si el propietario es una empresa), avisa con dos meses."),
    ("¿Tengo que pagar algo si me voy antes de que acabe el contrato?",
     "Solo si el contrato lo dice: como mucho, un mes de alquiler por cada año que falte para que acabe el contrato, y la parte proporcional si falta menos de un año. Si el contrato no dice nada, no hay indemnización."),
    ("¿Puedo irme antes de los seis meses?",
     "La ley no te deja irte por tu cuenta antes de los seis meses. Lo mejor es pactarlo por escrito con el propietario, por ejemplo buscándole tú un nuevo inquilino."),
    ("¿Cómo entrego la carta para que tenga validez?",
     "De forma que quede prueba de la fecha y del contenido: por burofax con acuse de recibo y certificación de contenido, o en mano con una copia que el propietario te firme y feche. Un correo o un WhatsApp sirve si el propietario te contesta confirmando que lo ha recibido."),
    ("¿Qué pasa con la fianza cuando dejo el piso?",
     "El propietario tiene un mes desde que le entregas las llaves para devolvértela, descontando solo lo que debas o los daños que hayas causado, justificados. Pásale por escrito la cuenta donde quieres recibirla."),
])
tdp = "".join(f'<tr><td style="text-align:left;white-space:normal">{esc(a)}</td><td><b>{esc(b)}</b></td><td style="text-align:left;white-space:normal" class="m">{esc(x)}</td></tr>' for a, b, x in DPZ)
IN = "font:16px Inter,system-ui,sans-serif;min-height:44px;width:100%;box-sizing:border-box;padding:0 8px;border:1px solid #d6d0c4;border-radius:10px;background:#fff"
def campo(i, et, extra="", tipo="text"):
    return f'<label class="m" style="flex:1 1 150px">{et}<br><input type="{tipo}" id="{i}" style="{IN}" {extra}></label>'
body = f"""<h1>Carta para dejar el piso de alquiler: modelo y plazos</h1>
<p>Para irte de un piso de alquiler tienes que avisar al propietario <b>por escrito y con 30 días de antelación</b> como mínimo. Rellena los datos y te preparamos la carta para copiarla o enviarla, y te avisamos si la fecha no cumple los plazos de la ley. Lo que escribas se queda en tu móvil: no lo guardamos ni lo enviamos a nadie.</p>
<div class="card" id="dj"><b>Tus datos</b>
<div style="display:flex;flex-wrap:wrap;gap:10px;margin:10px 0 4px">
{campo("dn", "Tu nombre", 'autocomplete="name" placeholder="Nombre y apellidos"')}
{campo("dp", "Nombre del propietario", 'placeholder="O de la agencia"')}
{campo("dd", "Dirección del piso", 'autocomplete="street-address" placeholder="Calle, número, piso"')}
{campo("dc", "Ciudad", 'placeholder="Por ejemplo, Madrid"')}
{campo("di", "El contrato empezó el", "", "date")}
{campo("ds", "Dejo el piso el", "", "date")}
<label class="m" style="flex:1 1 150px">Me voy<br><select id="dm" style="{IN}"><option value="a">Antes de que acabe</option><option value="r">Al acabar (no renuevo)</option></select></label>
{campo("df", "Fianza (€, opcional)", 'inputmode="decimal" min="0" step="10" placeholder="Por ejemplo, 900"', "number")}
</div>
<div id="dr" aria-live="polite" class="m" style="margin:8px 0"></div>
<label class="m" for="dt">Tu carta (puedes retocarla antes de copiarla)</label>
<textarea id="dt" rows="16" style="font:15px/1.45 Inter,system-ui,sans-serif;width:100%;box-sizing:border-box;padding:10px;border:1px solid #d6d0c4;border-radius:10px;margin-top:4px;resize:vertical"></textarea>
<div style="display:flex;flex-wrap:wrap;gap:8px;margin-top:10px"><button type="button" id="dcp" class="vbt">Copiar la carta</button><a id="dwa" class="vbt" target="_blank" rel="noopener">Enviar por WhatsApp</a><a id="dml" class="vbt">Enviar por correo</a></div>
<p class="m" style="margin-bottom:0">Para que quede prueba, mándala por <b>burofax con acuse de recibo y certificación de contenido</b> o entrégala en mano y pide que te firmen una copia con la fecha.</p></div>
<h2 style="font:700 21px/1.2 Fraunces,Georgia,serif;margin:24px 0 0">Con cuánta antelación hay que avisar</h2>
<div class="card"><table class="cmp"><caption class="m" style="text-align:left;padding-bottom:6px">Plazos de la Ley de Arrendamientos Urbanos para un piso en el que vives (contratos desde marzo de 2019)</caption><tr><th scope="col" style="text-align:left">Cuándo te vas</th><th scope="col">Aviso</th><th scope="col" style="text-align:left">Detalle</th></tr>{tdp}</table>
<p class="m">Si alquilas una habitación o un piso de temporada, manda lo que diga tu contrato. Calcula las fechas de tu contrato en <a href="../contrato-de-alquiler/">cuánto dura un contrato de alquiler</a>.</p></div>
<style>.vbt{{display:inline-flex;align-items:center;font:600 14px Inter,system-ui,sans-serif;min-height:44px;padding:0 14px;border:1px solid #d6d0c4;border-radius:10px;background:#fff;color:#1d2321;cursor:pointer;text-decoration:none;box-sizing:border-box}}#dr b{{color:#1d2321}}#dr .av{{color:#9a3b1c}}</style>
<script>""" + r"""(function(){var M=["enero","febrero","marzo","abril","mayo","junio","julio","agosto","septiembre","octubre","noviembre","diciembre"],K="vivible.dejar",$=function(i){return document.getElementById(i)},ids=["dn","dp","dd","dc","di","ds","dm","df"],t=$("dt"),r=$("dr"),s={};
try{s=JSON.parse(localStorage.getItem(K)||"{}")||{}}catch(e){}
ids.forEach(function(i){if(s[i]!=null)$(i).value=s[i]});
function mas(f,a,m){var x=new Date(f.getFullYear()+a,f.getMonth()+m,1),u=new Date(x.getFullYear(),x.getMonth()+1,0).getDate();x.setDate(Math.min(f.getDate(),u));return x}
function fe(v){v=/^(\d{4})-(\d{2})-(\d{2})$/.exec(v||"");return v?new Date(+v[1],v[2]-1,+v[3]):null}
function txt(x){return x.getDate()+" de "+M[x.getMonth()]+" de "+x.getFullYear()}
function eur(n){return Math.round(n).toString().replace(/\B(?=(\d{3})+(?!\d))/g,".")+" €"}
function v(i){return ($(i).value||"").trim()}
function calc(){var o={};ids.forEach(function(i){o[i]=$(i).value});try{localStorage.setItem(K,JSON.stringify(o))}catch(e){}
var h=new Date(),hoy=new Date(h.getFullYear(),h.getMonth(),h.getDate()),fi=fe(v("di")),fs=fe(v("ds")),m=v("dm"),q=parseFloat(v("df").replace(",",".")),av=[];
var sal=fs?"el "+txt(fs):"el [día en que dejas el piso]",dias=fs?Math.round((fs-hoy)/864e5):null;
if(!fs)av.push("Elige el día en que dejas el piso y te decimos si cumples el plazo.");
else if(dias<30)av.push('<span class="av"><b>Avisas con '+(dias<0?0:dias)+(dias===1?" día":" días")+'.</b> La ley pide 30 como mínimo: si mandas la carta hoy, la primera fecha que lo cumple es el <b>'+txt(new Date(hoy.getFullYear(),hoy.getMonth(),hoy.getDate()+30))+'</b>. Si quieres irte antes, pacta la fecha por escrito con el propietario.</span>');
else av.push("Avisas con <b>"+dias+" días</b>: cumples los 30 que pide la ley"+(m==="r"?" (si ya has cumplido los 5 años de contrato, o 7 si el propietario es una empresa, hacen falta 2 meses).":"."));
if(m==="r"&&fi&&fs&&fs>=mas(fi,5,0)&&dias!=null&&dias<61)av.push('<span class="av">Tu contrato ya tiene 5 años o más: si es el fin de la prórroga obligatoria, hacen falta <b>2 meses</b> de aviso (y 1 mes en cada año de la prórroga de hasta 3 años).</span>');
if(m==="r")av.push("Esta opción es para irte el día en que acaba el contrato o una de sus prórrogas anuales; si te vas en otra fecha, elige «Antes de que acabe».");
if(m==="a"){if(fi&&fs&&fs<mas(fi,0,6))av.push('<span class="av"><b>Aún no habrán pasado 6 meses</b> (se cumplen el '+txt(mas(fi,0,6))+'): la ley no te deja irte antes por tu cuenta. Pacta la salida por escrito con el propietario.</span>');
av.push("Si tu contrato lo dice, puede pedirte un mes de alquiler por cada año que falte para que acabe (la parte proporcional si es menos). Si no dice nada, no pagas indemnización.")}
r.innerHTML=av.join("<br>");
var ley=m==="r"?"no renovaré el contrato a su vencimiento, según los artículos 9 y 10 de la Ley de Arrendamientos Urbanos":"desisto del contrato, según el artículo 11 de la Ley de Arrendamientos Urbanos";
t.value=(v("dc")||"[Ciudad]")+", a "+txt(hoy)+"\n\nA la atención de "+(v("dp")||"[nombre del propietario]")+"\n\nAsunto: aviso de que dejo la vivienda alquilada\n\n"+
"Yo, "+(v("dn")||"[tu nombre]")+", con DNI o NIE ____________, que tengo alquilada la vivienda situada en "+(v("dd")||"[dirección del piso]")+(fi?" según el contrato firmado el "+txt(fi):"")+", le comunico por escrito"+(dias!=null&&dias>=0?", con "+dias+(dias===1?" día":" días")+" de antelación,":"")+" que dejaré la vivienda "+sal+" y que "+ley+".\n\n"+
"Le propongo quedar ese día para entregarle las llaves, leer los contadores y revisar juntos el estado de la vivienda. Le ruego que me devuelva la fianza"+(q>0?" de "+eur(q):"")+" en el plazo de un mes desde la entrega de las llaves, como marca el artículo 36.4 de la misma ley, en la cuenta que le indicaré.\n\nAtentamente,\n\n"+(v("dn")||"[tu nombre]")+"\nFirma:";
enl()}
function enl(){$("dwa").href="https://wa.me/?text="+encodeURIComponent(t.value);$("dml").href="mailto:?subject="+encodeURIComponent("Aviso de que dejo la vivienda alquilada")+"&body="+encodeURIComponent(t.value)}
ids.forEach(function(i){$(i).addEventListener("input",calc);$(i).addEventListener("change",calc)});t.addEventListener("input",enl);
$("dcp").addEventListener("click",function(){var b=this,ok=function(){b.textContent="Copiada";setTimeout(function(){b.textContent="Copiar la carta"},2000)};
if(navigator.clipboard&&navigator.clipboard.writeText)navigator.clipboard.writeText(t.value).then(ok,function(){t.select();try{document.execCommand("copy");ok()}catch(e){}});else{t.select();try{document.execCommand("copy");ok()}catch(e){}}});calc()})();</script>""" + f"""
{dj_html}
<a class="cta" href="../">¿Buscas piso nuevo? Pega el anuncio y comprueba si el precio es justo</a>
<div class="card m"><b>Más guías:</b> <a href="../devolver-fianza/">Cuándo te devuelven la fianza</a> · <a href="../reparaciones-alquiler/">Quién paga las reparaciones</a> · <a href="../mudanza/">Lista para la mudanza</a> · <a href="../contrato-de-alquiler/">Contrato de alquiler: cuánto dura</a> · <a href="../gastos-de-alquiler/">Dinero para alquilar</a> · <a href="../visitar-un-piso/">Qué mirar al visitar un piso</a> · """ + " · ".join(f'<a href="../{k}/alquiler/">Alquiler en {esc(c["n"])}</a>' for k, c in C.items()) + """</div>"""
os.makedirs(F("dejar-el-piso"), exist_ok=True)
open(F("dejar-el-piso", "index.html"), "w", encoding="utf-8").write(page(
    "Carta para dejar el piso de alquiler: modelo y plazos (2026)",
    desc_corta("Modelo de carta para avisar al propietario de que dejas el piso de alquiler: rellénala y cópiala o envíala. Con cuánta antelación avisar.", " Gratis."),
    "dejar-el-piso/", body, [("Vivible", "../"), ("Dejar el piso", None)], dj_ld))
urls.insert(21, BASE + "dejar-el-piso/")

# ---------- reparaciones (reparaciones-alquiler/): «quién paga las reparaciones en un piso de alquiler», «avería caldera alquiler
# quién paga», «pequeñas reparaciones inquilino». LAU art. 21.1 (las necesarias para la habitabilidad, el propietario, salvo daño
# del inquilino), 21.2 (obra de más de 20 días: baja el alquiler), 21.3 (avisar cuanto antes; urgentes: las haces y te las paga),
# 21.4 (pequeñas reparaciones por el desgaste del uso ordinario, el inquilino), art. 27 (resolver el contrato si no repara) y
# Código Civil art. 1561-1563 (devolver el piso como se recibió, salvo el desgaste por el tiempo). Sin cifras.
assert "reparaciones-alquiler" not in C
RPK = {"p": ("Propietario", "#1f6f54"), "i": ("Tú (inquilino)", "#9a3b1c"), "d": ("Depende", "#6b5a12"), "c": ("Comunidad", "#2d5a8a")}
REP = [
    ("Caldera o calentador que se estropea", "p", "Es una avería de una instalación del piso. Si se rompe porque la has usado mal, la pagas tú."),
    ("Revisión periódica de la caldera", "d", "Es mantenimiento: la paga quien diga el contrato, y muchos se la ponen al inquilino. Si el contrato no dice nada, pregunta antes de llamar al técnico."),
    ("Termo eléctrico que deja de calentar", "p", "Avería por el uso o la edad del aparato: propietario."),
    ("Grifo que gotea o cambiar la goma", "i", "Es una pequeña reparación por el desgaste del uso diario."),
    ("Bombillas y fluorescentes", "i", "Desgaste normal por el uso: te toca a ti."),
    ("Enchufe o interruptor roto", "i", "Pequeña reparación. Si falla la instalación (el cuadro, el cableado, saltan los plomos sin motivo), es del propietario."),
    ("Instalación eléctrica, cuadro o cableado", "p", "Es necesaria para que el piso se pueda habitar."),
    ("Atasco del fregadero, la ducha o el váter", "i", "Si es por el uso (pelos, restos, toallitas), lo pagas tú. Si viene de la tubería general del edificio, es de la comunidad."),
    ("Tubería rota o fuga de agua", "p", "Tuberías del piso: propietario. Si la fuga sale de una bajante o tubería común del edificio, la arregla la comunidad. Avisa enseguida y da parte al seguro."),
    ("Humedades y filtraciones", "p", "Si vienen del tejado, la fachada o las tuberías, las arregla el propietario o la comunidad."),
    ("Moho por condensación", "d", "Si es por no ventilar ni secar, te toca limpiarlo. Si el piso tiene un defecto de aislamiento o ventilación, es del propietario."),
    ("Cinta de la persiana", "i", "Se desgasta con el uso: pequeña reparación."),
    ("Persiana atascada, motor o lamas rotas", "p", "Avería de un elemento del piso por la edad o el uso normal. Si la rompes tú, la pagas tú."),
    ("Lavadora, frigorífico u horno del piso", "p", "Si venían con el piso y se estropean por la edad o el uso normal, propietario. Si es por mal uso, tú."),
    ("Aire acondicionado que no enfría", "p", "Avería del aparato: propietario. Limpiar los filtros es cosa tuya."),
    ("Vitrocerámica o placa rota por un golpe", "i", "Los daños que causas tú (o tus visitas) los pagas tú. Si deja de calentar por una avería, es del propietario."),
    ("Cerradura que falla por el desgaste", "p", "Si falla por el uso o la edad, propietario. Si pierdes las llaves o rompes la cerradura, tú."),
    ("Bisagras o tiradores de armarios y puertas", "i", "Ajustes pequeños por el uso diario: te tocan a ti."),
    ("Cristal roto", "d", "Si lo rompes tú o tus visitas, tú. Si se rompe por un fallo de la ventana o un temporal, el propietario (o su seguro)."),
    ("Plagas: cucarachas, chinches, carcoma", "d", "Si ya estaban al entrar o vienen del edificio, propietario o comunidad. Si aparecen por falta de limpieza, tú."),
    ("Pintar el piso al irte", "d", "El desgaste normal por el paso del tiempo no se paga. Manchas, agujeros grandes o colores que pusiste tú, sí: pueden descontarlos de la fianza."),
    ("Agujeros de cuadros y estanterías", "d", "Lo prudente es taparlos al irte. Pregunta antes de taladrar y guarda por escrito el permiso."),
    ("Ascensor, portal, fachada o tejado", "c", "Son elementos comunes: los paga la comunidad con las cuotas del propietario."),
    ("Antena, portero automático o bajantes", "c", "Son instalaciones del edificio: comunidad. El telefonillo de dentro de tu piso, si se estropea, propietario."),
    ("Daños que causas tú o tus visitas", "i", "Siempre los pagas tú, aunque sean grandes. Mira si tu seguro de hogar o de responsabilidad civil los cubre."),
]
def rep_fila(n, k, x):
    et, col = RPK[k]
    return (f'<div class="rpi" data-k="{k}"><div class="rpt"><b>{esc(n)}</b><span class="rpb" style="background:{col}">{esc(et)}</span></div>'
            f'<p class="m">{esc(x)}</p><button type="button" class="rpa" data-n="{esc(n)}">Avisar al propietario de esto</button></div>')
rpn = {k: sum(1 for _, kk, _ in REP if kk == k) for k in RPK}
rp_html, rp_ld = faq([
    ("¿Quién paga las reparaciones en un piso de alquiler?",
     "El propietario paga las reparaciones necesarias para que el piso se pueda habitar (caldera, tuberías, instalación eléctrica, humedades), salvo que el daño lo hayas causado tú. Tú pagas las pequeñas reparaciones por el desgaste del uso diario, como una bombilla, un grifo que gotea o la cinta de la persiana. Lo dice el artículo 21 de la Ley de Arrendamientos Urbanos."),
    ("¿Qué son las pequeñas reparaciones que paga el inquilino?",
     "Las que hacen falta por el desgaste normal del uso del día a día: cambiar bombillas, gomas de grifos, la cinta de una persiana, un enchufe o un tirador. La ley no da una lista ni un importe máximo, así que si dudas, mira tu contrato o pregúntale al propietario por escrito."),
    ("¿El contrato puede decir que pago yo todas las reparaciones?",
     "En el alquiler de tu vivienda habitual, no puede quitarte derechos que te da la ley: las reparaciones necesarias para habitar el piso siguen siendo del propietario aunque el contrato diga otra cosa. Sí puede decir quién paga el mantenimiento, como la revisión de la caldera."),
    ("¿Qué hago si el propietario no quiere arreglar una avería?",
     "Avísale por escrito cuanto antes y guarda la prueba. Si es urgente para evitar un daño mayor (una fuga, quedarte sin agua caliente), puedes arreglarlo tú avisándole y pedirle después lo que pagaste con la factura. Si se niega a hacer reparaciones necesarias, puedes pedirlo en el juzgado o incluso dar por terminado el contrato."),
    ("¿Me bajan el alquiler si la obra dura mucho?",
     "Sí: si la reparación dura más de 20 días, el alquiler baja en proporción a la parte del piso que no puedes usar mientras dura la obra."),
    ("¿Me pueden descontar las reparaciones de la fianza?",
     "Solo los daños que hayas causado tú y lo que debas, y justificándolo. El desgaste normal por el paso del tiempo y el uso no se descuenta. Haz fotos con fecha al entrar y al salir."),
])
body = f"""<h1>¿Quién paga las reparaciones en un piso de alquiler?</h1>
<p>La regla corta: lo que hace falta para que el piso se pueda habitar lo paga <b>el propietario</b>; las <b>pequeñas reparaciones por el desgaste del uso diario</b> las pagas <b>tú</b>, y lo que rompas, también. Busca tu avería en la lista y, si le toca al propietario, prepárale el aviso con un toque.</p>
<div class="card"><label class="m" for="rq">Busca la avería</label>
<input id="rq" type="search" placeholder="Por ejemplo, caldera, persiana, grifo" autocomplete="off" style="font:16px Inter,system-ui,sans-serif;min-height:44px;width:100%;box-sizing:border-box;padding:0 10px;border:1px solid #d6d0c4;border-radius:10px;background:#fff;margin-top:4px">
<div id="rf" role="group" aria-label="Filtrar por quién paga" style="display:flex;flex-wrap:wrap;gap:6px;margin-top:10px"><button type="button" class="rpf" data-k="" aria-pressed="true">Todas ({len(REP)})</button>""" + "".join(f'<button type="button" class="rpf" data-k="{k}" aria-pressed="false">{esc(et)} ({rpn[k]})</button>' for k, (et, _) in RPK.items()) + f"""</div>
<p id="rn" class="m" aria-live="polite" style="margin:10px 0 0"></p></div>
<div id="rl">{"".join(rep_fila(*x) for x in REP)}</div>
<div class="card" id="rav" hidden><b>Aviso al propietario</b>
<p class="m" style="margin:4px 0 8px">La ley te pide avisar cuanto antes de cualquier avería. Hazlo por escrito para que quede prueba.</p>
<label class="m" for="rt">Tu mensaje (puedes retocarlo)</label>
<textarea id="rt" rows="8" style="font:15px/1.45 Inter,system-ui,sans-serif;width:100%;box-sizing:border-box;padding:10px;border:1px solid #d6d0c4;border-radius:10px;margin-top:4px;resize:vertical"></textarea>
<div style="display:flex;flex-wrap:wrap;gap:8px;margin-top:10px"><button type="button" id="rcp" class="vbt">Copiar el mensaje</button><a id="rwa" class="vbt" target="_blank" rel="noopener">Enviar por WhatsApp</a></div></div>
<h2 style="font:700 21px/1.2 Fraunces,Georgia,serif;margin:24px 0 0">Lo que dice la ley</h2>
<div class="card"><ul style="margin:0;padding-left:20px">
<li><b>El propietario</b> hace las reparaciones necesarias para que el piso se pueda habitar, sin subirte el alquiler por ello, salvo que el daño lo hayas causado tú (artículo 21.1 de la Ley de Arrendamientos Urbanos).</li>
<li><b>Tú</b> pagas las pequeñas reparaciones por el desgaste del uso ordinario (21.4) y los daños que causes tú o quien viva o te visite.</li>
<li><b>Avisa cuanto antes</b> de cualquier avería. Si es urgente para evitar un daño mayor, puedes arreglarla tú y pedirle después lo que pagaste (21.3).</li>
<li>Si la obra dura <b>más de 20 días</b>, el alquiler baja en proporción a la parte del piso que no puedes usar (21.2).</li>
<li>Al irte, devuelves el piso como lo recibiste, salvo el <b>desgaste normal por el tiempo</b>, que no se paga.</li>
</ul><p class="m" style="margin-bottom:0">Es para el alquiler de tu vivienda habitual. En una habitación o un piso de temporada, mira también lo que diga tu contrato. Esto es orientativo: ante un conflicto, consulta la oficina de vivienda o de consumo de tu ayuntamiento.</p></div>
<style>.vbt{{display:inline-flex;align-items:center;font:600 14px Inter,system-ui,sans-serif;min-height:44px;padding:0 14px;border:1px solid #d6d0c4;border-radius:10px;background:#fff;color:#1d2321;cursor:pointer;text-decoration:none;box-sizing:border-box}}.rpf{{font:600 14px Inter,system-ui,sans-serif;min-height:44px;padding:0 12px;border:1px solid #d6d0c4;border-radius:22px;background:#fff;color:#1d2321;cursor:pointer}}.rpf[aria-pressed=true]{{background:#1d2321;color:#fff;border-color:#1d2321}}.rpi{{background:#fff;border:1px solid #e6e0d4;border-radius:14px;padding:12px 14px;margin:10px 0}}.rpt{{display:flex;justify-content:space-between;align-items:flex-start;gap:10px}}.rpb{{flex:none;color:#fff;font:600 12px Inter,system-ui,sans-serif;border-radius:12px;padding:3px 9px;white-space:nowrap}}.rpi p{{margin:6px 0 0}}.rpa{{font:600 13px Inter,system-ui,sans-serif;min-height:44px;margin-top:4px;padding:0;border:0;background:none;color:#1f6f54;text-decoration:underline;cursor:pointer}}.rpi[data-k=i] .rpa,.rpi[data-k=c] .rpa{{display:none}}</style>
<script>""" + r"""(function(){var $=function(i){return document.getElementById(i)},q=$("rq"),it=[].slice.call(document.querySelectorAll(".rpi")),fs=[].slice.call(document.querySelectorAll(".rpf")),k="",t=$("rt");
function n(s){return (s||"").toLowerCase().normalize("NFD").replace(/[̀-ͯ]/g,"")}
function fil(){var w=n(q.value).split(/\s+/).filter(Boolean),c=0;it.forEach(function(e){var x=n(e.textContent),ok=(!k||e.getAttribute("data-k")===k)&&w.every(function(p){return x.indexOf(p)>=0});e.hidden=!ok;if(ok)c++});
$("rn").textContent=c?c+(c===1?" avería":" averías"):"No la encontramos. Regla general: si hace falta para vivir en el piso, propietario; si es pequeña y por el uso diario, tú."}
q.addEventListener("input",fil);
fs.forEach(function(b){b.addEventListener("click",function(){k=b.getAttribute("data-k");fs.forEach(function(o){o.setAttribute("aria-pressed",o===b?"true":"false")});fil()})});
function enl(){$("rwa").href="https://wa.me/?text="+encodeURIComponent(t.value)}
[].slice.call(document.querySelectorAll(".rpa")).forEach(function(b){b.addEventListener("click",function(){var a=b.getAttribute("data-n").toLowerCase();
t.value="Hola. Le escribo para avisarle de una avería en el piso que le tengo alquilado: "+a+". Lo noto desde el día [fecha]."+(b.parentNode.getAttribute("data-k")==="p"?" Según el artículo 21 de la Ley de Arrendamientos Urbanos, las reparaciones necesarias para habitar la vivienda corren a cargo del propietario.":"")+" ¿Cuándo podría venir alguien a arreglarlo? Puedo mandarle fotos. Gracias.";
enl();$("rav").hidden=false;$("rav").scrollIntoView({behavior:"smooth",block:"start"});t.focus({preventScroll:true})})});
t.addEventListener("input",enl);
$("rcp").addEventListener("click",function(){var b=this,ok=function(){b.textContent="Copiado";setTimeout(function(){b.textContent="Copiar el mensaje"},2000)};
if(navigator.clipboard&&navigator.clipboard.writeText)navigator.clipboard.writeText(t.value).then(ok,function(){t.select();try{document.execCommand("copy");ok()}catch(e){}});else{t.select();try{document.execCommand("copy");ok()}catch(e){}}});
var u=new URLSearchParams(location.search).get("q");if(u)q.value=u;fil()})();</script>""" + f"""
{rp_html}
<a class="cta" href="../">¿Buscas piso nuevo? Pega el anuncio y comprueba si el precio es justo</a>
<div class="card m"><b>Más guías:</b> <a href="../contrato-de-alquiler/">Contrato de alquiler: cuánto dura</a> · <a href="../devolver-fianza/">Cuándo te devuelven la fianza</a> · <a href="../dejar-el-piso/">Carta para dejar el piso</a> · <a href="../reparaciones-alquiler/">Quién paga las reparaciones</a> · <a href="../visitar-un-piso/">Qué mirar al visitar un piso</a> · <a href="../papeles-para-alquilar/">Papeles para alquilar</a> · """ + " · ".join(f'<a href="../{k}/alquiler/">Alquiler en {esc(c["n"])}</a>' for k, c in C.items()) + """</div>"""
os.makedirs(F("reparaciones-alquiler"), exist_ok=True)
open(F("reparaciones-alquiler", "index.html"), "w", encoding="utf-8").write(page(
    "¿Quién paga las reparaciones en un alquiler? Lista 2026",
    desc_corta(f"Caldera, persiana, grifo, humedades, electrodomésticos: quién paga cada una de {len(REP)} averías en un piso de alquiler, según la ley, y aviso al propietario.", " Gratis."),
    "reparaciones-alquiler/", body, [("Vivible", "../"), ("Reparaciones del alquiler", None)], rp_ld))
urls.insert(22, BASE + "reparaciones-alquiler/")

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
