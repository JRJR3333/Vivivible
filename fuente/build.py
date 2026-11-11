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

FAV = "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 32 32'%3E%3Crect width='32' height='32' rx='8' fill='%231f6f54'/%3E%3Cpath d='M8 16l8-7 8 7v8h-5v-5h-6v5H8z' fill='%23fff'/%3E%3C/svg%3E"
HEADX = f'<link rel="icon" href="{FAV}"><meta name="theme-color" content="#1f6f54"><meta property="og:type" content="website"><meta property="og:site_name" content="Vivible"><meta property="og:locale" content="es_ES"><meta name="twitter:card" content="summary_large_image"><meta property="og:image" content="{BASE}assets/og.png"><meta property="og:image:width" content="1200"><meta property="og:image:height" content="630"><meta property="og:image:alt" content="Vivible: ¿se vive bien en ese piso?">\n'

meses = sorted({c["mes"] for c in C.values()})
mes_txt = "julio–octubre 2026"

# ---------- index.html
ciudades_links = "".join(f'<a href="{k}/">Vivir en {esc(c["n"])}</a>' for k, c in C.items())
t = open(F("fuente", "template.html"), encoding="utf-8").read()
idx = (t.replace("__PRECIOS__", json.dumps(P, ensure_ascii=False, separators=(",", ":")))
        .replace("__MADRID__", MAD).replace("__HEADX__", HEADX).replace("__MESES__", mes_txt).replace("__CIUDADES__", ciudades_links))
open(F("index.html"), "w", encoding="utf-8").write(idx)

# ---------- static pages
CSS = """body{margin:0;background:#f6f3ee;color:#1d2321;font:16px/1.6 Inter,system-ui,sans-serif}.w{max-width:760px;margin:0 auto;padding:20px 16px 60px}
a{color:#1f6f54}h1{font:700 30px/1.15 Fraunces,Georgia,serif;margin:10px 0}.b{display:inline-block;font-size:12px;font-weight:600;color:#1f6f54;background:#e8f2ec;padding:3px 10px;border-radius:99px;text-decoration:none}
.card{background:#fff;border:1px solid #e4dfd6;border-radius:16px;padding:18px;margin-top:16px}.g{display:grid;grid-template-columns:1fr 1fr;gap:12px}.k{background:#faf8f4;border:1px solid #e4dfd6;border-radius:12px;padding:12px}
.k small{display:block;color:#5f6b66;font-size:12px}.k b{font:700 24px Fraunces,serif}.cta{display:block;text-align:center;background:#1f6f54;color:#fff;text-decoration:none;font-weight:700;padding:15px;border-radius:12px;margin-top:18px}
table{width:100%;border-collapse:collapse;font-size:14px}td,th{padding:7px 4px;border-top:1px solid #f1ede6;text-align:left}td:last-child,th:last-child{text-align:right}.m{color:#5f6b66;font-size:13px}
@media(max-width:480px){.g{grid-template-columns:1fr}h1{font-size:26px}}"""

def page(title, desc, path, body, crumbs):
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
<script type="application/ld+json">{ld}</script>
<link rel="preconnect" href="https://fonts.googleapis.com"><link href="https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,700&family=Inter:wght@400;600;700&display=swap" rel="stylesheet">
<style>{CSS}</style></head><body><div class="w"><div class="m">{bc}</div>{body}
<p class="m" style="margin-top:28px">Datos: precios medios de idealista ({esc(mes_txt)}); habitaciones: precio medio de la ciudad. Estimaciones orientativas, no tasaciones oficiales. Hecho por <a href="{"../" * path.count("/")}">Vivible</a>.</p></div></body></html>"""

urls = [BASE]
for ck, c in C.items():
    rows = sorted(((d, *dprice(c, d)) for d in c["d"]), key=lambda x: -x[1])
    n = len(rows)
    os.makedirs(F(ck), exist_ok=True)
    # city page
    tr = "".join(f'<tr><td><a href="{slug(d)}/">{esc(d)}</a></td><td>{fmt(s)} €/m²{"*" if es else ""}</td><td>{dec(r)} €/m²{"*" if er else ""}</td></tr>' for d, s, r, es, er in rows)
    nota = '<p class="m">* Estimado a partir del otro precio del distrito: idealista no publica ese dato.</p>' if any(x[3] or x[4] for x in rows) else ""
    body = f"""<h1>Vivir en {esc(c["n"])}: precio por distritos ({esc(c["mes"])})</h1>
<p>Comprar en {esc(c["n"])} cuesta de media <b>{fmt(c["venta"])} €/m²</b> y alquilar <b>{dec(c["alquiler"])} €/m² al mes</b>. Una habitación en piso compartido ronda los <b>{fmt(c["hab"])} € al mes</b>. Estos son los {n} distritos, del más caro al más barato.</p>
<div class="card"><table><tr><th>Distrito</th><th>Venta</th><th>Alquiler/mes</th></tr>{tr}</table>{nota}</div>
<a class="cta" href="../#c={ck}">Analiza un piso concreto en {esc(c["n"])}</a>
<div class="card m"><b>Otras ciudades:</b> {" · ".join(f'<a href="../{k2}/">{esc(c2["n"])}</a>' for k2, c2 in C.items() if k2 != ck)}</div>"""
    open(F(ck, "index.html"), "w", encoding="utf-8").write(page(
        f"Vivir en {c['n']}: precio de la vivienda por distritos (2026) | Vivible",
        f"Precio medio de compra, alquiler y habitación en los {n} distritos de {c['n']}. Compara barrios y analiza un piso gratis.",
        f"{ck}/", body, [("Vivible", "../"), (c["n"], None)]))
    urls.append(BASE + ck + "/")
    # district pages
    for i, (d, s, r, es, er) in enumerate(rows):
        sd = slug(d); os.makedirs(F(ck, sd), exist_ok=True)
        vs = (s / c["venta"] - 1) * 100
        tier = "de los más caros" if i < n / 3 else ("de precio medio" if i < 2 * n / 3 else "de los más asequibles")
        buy70 = s * 70; rent70 = r * 70
        room = round(c["hab"] * (r / c["alquiler"]) ** .8 / 5) * 5
        ahorro = buy70 * (.2 + c["itp"] / 100 + .015) + 400
        cuota = buy70 * .8 * (.028 / 12) / (1 - (1 + .028 / 12) ** -360)
        yld = rent70 * 12 / buy70 * 100
        consejo = {
            "de los más caros": f"Es una zona cara de {c['n']}: aquí se paga la ubicación. Fíjate en que el piso justifique el precio (ascensor, luz, estado) y compara con distritos vecinos.",
            "de precio medio": f"Está en la franja media de {c['n']}: suele haber buen equilibrio entre precio y servicios. Revisa el transporte hasta tu trabajo antes de decidir.",
            "de los más asequibles": f"Es de las zonas más asequibles de {c['n']}. Puede ser una buena oportunidad, pero revisa con calma el estado del edificio, el transporte y el ambiente de la calle de día y de noche.",
        }[tier]
        otros = " · ".join(f'<a href="../{slug(o)}/">{esc(o)}</a>' for o, *_ in rows if o != d)
        body = f"""<h1>Vivir en {esc(d)} ({esc(c["n"])}): precio, alquiler y habitación</h1>
<p>{esc(d)} es {"el <b>distrito más caro</b>" if i == 0 else ("el <b>distrito más asequible</b>" if i == n - 1 else f"el <b>{i+1}º distrito más caro</b>")} de {n} en {esc(c["n"])}: {tier}. {"Comprar cuesta lo mismo que la media de la ciudad" if round(abs(vs)) == 0 else f'Comprar cuesta un {dec(abs(vs),0)} % {"más" if vs >= 0 else "menos"} que la media de la ciudad'}{" (dato estimado)" if es else ""}.</p>
<div class="g"><div class="k"><small>Comprar{" (estimado)" if es else ""}</small><b>{fmt(s)} €/m²</b><small>Media de {esc(c["n"])}: {fmt(c["venta"])} €/m²</small></div>
<div class="k"><small>Alquilar{" (estimado)" if er else ""}</small><b>{dec(r)} €/m²/mes</b><small>Media: {dec(c["alquiler"])} €/m²/mes</small></div>
<div class="k"><small>Piso de 70 m² en venta</small><b>≈ {fmt(buy70)} €</b><small>Ahorros necesarios: ≈ {fmt(ahorro)} €</small></div>
<div class="k"><small>Piso de 70 m² en alquiler</small><b>≈ {fmt(rent70)} €/mes</b><small>Ingresos recomendados: ≈ {fmt(rent70/.33)} €/mes</small></div>
<div class="k"><small>Habitación en piso compartido</small><b>≈ {fmt(room)} €/mes</b><small>Media de la ciudad: {fmt(c["hab"])} €</small></div>
<div class="k"><small>Hipoteca de ese piso (80 %, 30 años, 2,8 %)</small><b>≈ {fmt(cuota)} €/mes</b><small>Rentabilidad bruta si se alquila: {dec(yld)} %</small></div></div>
<div class="card"><b>Lo que debes saber</b><p>{esc(consejo)} El impuesto de compra de segunda mano en {esc(c["ccaa"])} es del {str(c["itp"]).replace(".", ",")} % (tipo general).</p></div>
<a class="cta" href="../../#c={ck}&d={quote(d)}">¿Tienes un piso en {esc(d)}? Analízalo gratis</a>
<div class="card m"><b>Otros distritos de {esc(c["n"])}:</b> {otros}</div>"""
        open(F(ck, sd, "index.html"), "w", encoding="utf-8").write(page(
            f"Vivir en {d}, {c['n']}: precio por m², alquiler y habitación (2026) | Vivible",
            f"{d} ({c['n']}): {fmt(s)} €/m² en venta, {dec(r)} €/m² de alquiler y habitación por unos {fmt(room)} €. Cuánto necesitas para comprar o alquilar.",
            f"{ck}/{sd}/", body, [("Vivible", "../../"), (c["n"], "../"), (d, None)]))
        urls.append(BASE + f"{ck}/{sd}/")

open(F("sitemap.xml"), "w").write('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' +
    "".join(f"<url><loc>{u}</loc><lastmod>{P['actualizado']}</lastmod></url>\n" for u in urls) + "</urlset>\n")
open(F("robots.txt"), "w").write(f"User-agent: *\nAllow: /\nSitemap: {BASE}sitemap.xml\n")
print(len(urls), "páginas")
