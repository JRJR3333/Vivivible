// Vivible · núcleo común a todos los formatos (web, conversación, app, WhatsApp…).
// Aquí viven los datos y los cálculos. No toca la pantalla: nada de document ni window.
// Los datos (precios y barrios de Madrid) los inserta fuente/build.py al generar assets/vivible.js.
const P = __PRECIOS__;
const MAD = __MADRID__;
const C = P.ciudades;
const fmt=n=>{const r=Math.round(n),a=String(Math.abs(r)).replace(/\B(?=(\d{3})+(?!\d))/g,".");return (r<0?"-":"")+a;};
const eur=n=>fmt(n)+" €";
const dec=(n,d=1)=>n.toFixed(d).replace(".",",");
const norm=s=>(s||"").toLowerCase().normalize("NFD").replace(/[\u0300-\u036f]/g,"").replace(/[^a-z0-9 ]/g," ").replace(/\s+/g," ").trim();
function hav(a,b){const R=6371,r=Math.PI/180,dl=(b[0]-a[0])*r,dn=(b[1]-a[1])*r,x=Math.sin(dl/2)**2+Math.cos(a[0]*r)*Math.cos(b[0]*r)*Math.sin(dn/2)**2;return 2*R*Math.asin(Math.sqrt(x));}
const walkMin=km=>Math.max(1,Math.round(km*1.25*1000/80));
const esc=t=>String(t==null?"":t).replace(/[&<>"']/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));
const score=v=>Math.max(1,Math.min(10,v));
const dist=km=>{const m=Math.max(50,Math.round(km*20)*50);return m<1000?m+" m":dec(km)+" km";};


// ---------- prices
function dPrice(ck,d){
  const c=C[ck];let p=c.d[d];let es=false,er=false;
  if(!p)return {s:c.venta,r:c.alquiler,est:false,es:false,er:false,city:true};
  let [s,r]=p;
  if(s==null){s=c.venta*Math.pow(r/c.alquiler,1.5);es=true;}
  if(r==null){r=c.alquiler*Math.pow(s/c.venta,.5);er=true;}
  return {s,r,est:es||er,es,er,city:false};
}
const roomBase=(ck,d)=>{const p=dPrice(ck,d);return Math.round(C[ck].hab*Math.pow(p.r/C[ck].alquiler,.8)/5)*5;};


// Madrid: barrio exacto con polígonos
function inPoly(pt,ring){let c=false;for(let i=0,j=ring.length-1;i<ring.length;j=i++){const [xi,yi]=ring[i],[xj,yj]=ring[j];if(((yi>pt[1])!=(yj>pt[1]))&&(pt[0]<(xj-xi)*(pt[1]-yi)/(yj-yi)+xi))c=!c;}return c;}
function madBarrio(lat,lon){return MAD.barrios.find(b=>b.r.some(r=>inPoly([lon,lat],r)));}
function nearestCity(lat,lon){let best=null,bd=1e9;for(const [k,c] of Object.entries(C)){const d=hav([lat,lon],c.centro);if(d<bd){bd=d;best=k;}}return bd<25?best:null;}
function matchDistrict(ck,names){
  const ds=Object.keys(C[ck].d);const cand=names.map(norm).filter(n=>n.length>2).map(n=>" "+n+" ");
  for(const d of ds)if(cand.some(n=>n.trim()===norm(d)))return d;
  for(const d of ds){const parts=d.split(/ - |-/).map(norm).filter(x=>x.length>2);if(cand.some(n=>parts.some(p=>n.includes(" "+p+" "))))return d;}
  return "";
}
// dónde cae un punto: ciudad, distrito y barrio (Madrid con polígonos; el resto con Nominatim)
async function locate(lat,lon){
  const ck=nearestCity(lat,lon);if(!ck)return null;
  let d="",auto="";
  if(ck==="madrid"){const b=madBarrio(lat,lon);if(b){d=b.d;auto=b.n;}}
  if(!d){
    try{const r=await fetch(`https://nominatim.openstreetmap.org/reverse?format=jsonv2&zoom=17&addressdetails=1&lat=${lat}&lon=${lon}`,{headers:{"Accept-Language":"es"}});const j=await r.json();const a=j.address||{};
      auto=a.suburb||a.quarter||a.neighbourhood||"";
      d=matchDistrict(ck,[a.city_district,a.borough,a.suburb,a.quarter,a.neighbourhood]);
    }catch(e){}
  }
  return {ck,d,auto};
}

const GEO={};
async function geocode(q){
  if(q in GEO)return GEO[q];
  return GEO[q]=fetch("https://nominatim.openstreetmap.org/search?format=jsonv2&limit=1&countrycodes=es&q="+encodeURIComponent(q),{headers:{"Accept-Language":"es"}})
    .then(r=>r.json()).then(j=>j.length?[+j[0].lat,+j[0].lon]:null).catch(e=>{delete GEO[q];throw e;});
}

// ---------- paste an ad
// zonas de Madrid que la gente nombra y no son distrito ni barrio oficial
const ZONAS_MADRID=[["la latina","Centro"],["lavapies","Centro"],["malasana","Centro"],["chueca","Centro"],["huertas","Centro"],["barrio de las letras","Centro"],["opera","Centro"]];
function parseAd(t){
  const T=t.replace(/ /g," "),L=T.toLowerCase(),out={},got=[];
  const num=s=>+String(s).replace(/[.\s]/g,"").replace(",",".");
  // --- qué es: manda el titular («piso en alquiler», «habitación en…»), no las palabras sueltas del menú del portal
  const roomH=/habitaci[oó]n (en|de|para)[^.\n]{0,25}(piso|vivienda) compartid|alquiler de habitaci[oó]n\b|habitaci[oó]n en alquiler|(alquilo|se alquila|alquiler)\s+(una\s+)?habitaci[oó]n\b/.test(L);
  const rentH=/(piso|[aá]tico|estudio|apartamento|d[uú]plex|loft|casa|chalet|vivienda)\s+(en|de)\s+alquiler|alquiler de (piso|[aá]tico|estudio|apartamento|d[uú]plex|loft|casa|chalet|vivienda)|se alquila|alquilo\b/.test(L);
  const saleH=/(piso|[aá]tico|estudio|apartamento|d[uú]plex|loft|casa|chalet|vivienda)\s+en\s+venta|\ben venta\b|se vende|vendo\b|venta (de )?(piso|[aá]tico|estudio|apartamento)/.test(L);
  const mes=/€\s*\/\s*mes|euros?\s*\/\s*mes|al mes|\/mes|mensual/.test(L);
  out.op=roomH?"habitacion":rentH&&!saleH?"alquiler":saleH&&!rentH?"venta":mes||(/alquiler|alquila/.test(L)&&!/\bventa\b/.test(L))?"alquiler":"venta";
  // --- precio: fuera comunidad, fianza, IBI y precios tachados; el primero que tenga sentido
  const prices=[...T.matchAll(/(?<![\d.,])(\d{1,3}(?:\.\d{3})+|\d{1,3}(?: \d{3})+|\d{3,7})(?:,\d{1,2})?\s*(?:€|eur)/gi)]
    .filter(m=>!/(?<![a-záéíóúñ])(comunidad|fianza|ibi|gastos|antes|dep[oó]sito|garant[ií]a)(?![a-záéíóúñ])[^\d\n]{0,25}$/i.test(T.slice(Math.max(0,m.index-40),m.index))).map(m=>num(m[1]));
  const okP={venta:p=>p>=30000,alquiler:p=>p>=300&&p<20000,habitacion:p=>p>=150&&p<=2000};
  let precio=prices.find(okP[out.op]);
  if(precio==null&&prices.length&&!roomH){const alt=modoPorPrecio(out.op,prices[0]);if(alt&&alt!=="habitacion"&&okP[alt](prices[0])){out.op=alt;precio=prices[0];}}
  got.push({habitacion:"habitación",alquiler:"alquiler",venta:"compra"}[out.op]);
  if(precio!=null){out.precio=precio;got.push("precio");}
  const room=out.op==="habitacion";
  // --- metros: los de la vivienda (no terraza, patio…); en habitación, los de la habitación
  const M2=/(?<![\d.,])(\d{1,4})\s*(?:m²|m2\b|mts?\b|metros(?: cuadrados)?)(\s*(?:construidos|const\b))?/g;
  const ms=[...L.matchAll(M2)].map(m=>({n:+m[1],c:!!m[2],pre:L.slice(Math.max(0,m.index-30),m.index)})).filter(m=>!/(terraza|balc[oó]n|patio|parcela|jard[ií]n|trastero|garaje)[^\d.\n]{0,20}$/.test(m.pre));
  if(room){const h=ms.find(m=>m.n>=4&&m.n<=40&&/habitaci[oó]n[^.\n]{0,25}$/.test(m.pre))||ms.find(m=>m.n>=4&&m.n<=40&&!/piso[^.\n]{0,15}$/.test(m.pre));if(h){out.rm2=h.n;got.push("m² de la habitación");}}
  else{const big=ms.filter(m=>m.n>=15&&m.n<=600),c=big.find(m=>m.c)||big.sort((a,b)=>b.n-a.n)[0];if(c){out.m2=c.n;got.push("m²");}}
  let m;
  if(/\bestudio\b/.test(L)&&!room)out.hab=0;
  m=L.match(/(?<![\w².,])(\d)\s*(?:habs?\b\.?|habitaci[oó]n(?:es)?|dormitorios?)/);if(m&&!room&&+m[1]>0){out.hab=Math.min(5,+m[1]);got.push("habitaciones");}
  m=L.match(/(?<![\w².,])(\d)\s*baños?/);if(m){out.ban=Math.min(3,+m[1]);got.push("baños");}
  // --- planta
  const ORD={primera:1,primer:1,segunda:2,segundo:2,tercera:3,tercer:3,cuarta:4,cuarto:4,quinta:5,quinto:5,sexta:6,sexto:6,septima:6,octava:6,novena:6,decima:6};
  if(/semis[oó]tano/.test(L))out.planta=-1;else if(/[aá]tico/.test(L))out.planta=99;else if(/\bbajo\b(?! cubierta)|planta baja/.test(L))out.planta=0;
  else{m=L.match(/planta\s*(\d{1,2})(?!\d)|(?<![\d.,])(\d{1,2})\s*[ºªo°a]?\s*planta(?!s)/);if(m)out.planta=Math.min(6,+(m[1]||m[2]));
    else{m=norm(L).match(/\b(primera?|segund[ao]|tercera?|cuart[ao]|quint[ao]|sext[ao]|septima|octava|novena|decima)\s+planta(?!s)/);if(m)out.planta=ORD[m[1]];}}
  if(out.planta!=null)got.push("planta");
  if(/sin ascensor|no (tiene|dispone de|hay|cuenta con) ascensor/.test(L)){out.asc=0;got.push("ascensor");}else if(/ascensor/.test(L)){out.asc=1;got.push("ascensor");}
  if(/\binterior\b/.test(L)){out.ext=0;}else if(/\bexterior\b/.test(L)){out.ext=1;}
  if(/a reformar|para reformar|(?<!no )necesita reforma/.test(L))out.estado="reformar";else if(/(?<!alquilar )obra nueva(?!\s*\n)|a estrenar/.test(L))out.estado="nuevo";else if(/reformad[oa]|reci[eé]n reformad/.test(L))out.estado="reformado";else if(/buen estado|segunda mano/.test(L))out.estado="bueno";
  if(out.estado)got.push("estado");
  m=L.match(/(?:construid[oa] en|a[nñ]o de construcci[oó]n:?|del a[nñ]o)\s*(1[89]\d\d|20\d\d)/);if(m){const y=+m[1];out.anio=y<1950?1940:y<1970?1960:y<1980?1975:y<2000?1990:y<2015?2005:2020;got.push("año");}
  m=L.match(/orientaci[oó]n\s*(sur|norte|este|oeste)/);if(m){out.ori={sur:"S",norte:"N",este:"E",oeste:"O"}[m[1]];got.push("orientación");}
  if(/terraza|balc[oó]n/.test(L))out.ter=1;
  if(/garaje incluid|plaza de garaje incluid|parking incluid/.test(L))out.gar=1;
  if(/trastero/.test(L))out.tra=1;
  if(/aire acondicionado|climatizaci/.test(L))out.aa=1;
  if(/calefacci[oó]n central/.test(L))out.cal="cen";else if(/no dispone de calefacci|sin calefacci/.test(L))out.cal="no";else if(/calefacci[oó]n/.test(L))out.cal="ind";
  m=L.match(/(?:gastos de )?comunidad[^0-9\n]{0,20}(\d{1,4})\s*€/);if(m){out.com=+m[1];got.push("comunidad");}
  if(/baño privado|ba[nñ]o propio|ba[nñ]o en suite/.test(L))out.rban="priv";
  if(/gastos incluidos|suministros incluidos/.test(L))out.gastos="inc";
  m=L.match(/(?<![\w².,])(\d)\s*(?:compa[nñ]eros|inquilinos|personas)/);if(m){out.pers=Math.min(6,+m[1]+(/compa[nñ]eros/.test(m[0])?1:0));}
  m=T.match(/(?:en |, )((?:calle|c\/|avenida|avda\.?|paseo|plaza|pza\.?|camino|ronda|glorieta|traves[ií]a|carrer|passeig|avinguda|kalea)\s+(?!tranquil|peatonal|principal|comercial|de garaje|mar[ií]tim|sin salida|muy |con |sin )[^,\n·|.;]{2,60}?(?:,?\s*(?:n[ºo°]\s*)?\d{1,4}(?![\d.]|\s*(?:€|eur|m²|m2|hab)))?)(?=\s*(?:[,\n·|.;]|$))/i);
  if(m){out.dir=m[1].trim();got.push("dirección");}
  // ciudad: fuera de la dirección («avenida de Madrid» no es Madrid); si hay varias, la última
  const sinDir=out.dir?T.replace(out.dir," "):T,NS=norm(sinDir);let pos=-1;
  for(const [k,c] of Object.entries(C)){const alt=k==="valencia"?"valencia|valencia":k==="alicante"?"alicante|alacant":norm(c.n);
    for(const mm of NS.matchAll(new RegExp("\\b(?:"+alt+")\\b","g")))if(mm.index>pos){pos=mm.index;out.ck=k;}}
  const STOP=new Set(["centro","este","norte","sur","oeste","jesus","universidad","miraflores"]);
  const busca=txt=>{const NT=" "+norm(txt)+" ",hits=[];
    if(!out.ck||out.ck==="madrid")for(const [n,d] of ZONAS_MADRID)if(NT.includes(" "+n+" "))hits.push({k:"madrid",d,len:n.length+.5});
    if(!out.ck||out.ck==="madrid")for(const b of MAD.barrios){const n=norm(b.n);if(n.length>=4&&!STOP.has(n)&&NT.includes(" "+n+" "))hits.push({k:"madrid",d:b.d,len:n.length+.5});}
    for(const [k,c] of Object.entries(C)){if(out.ck&&k!==out.ck)continue;
      for(const d of Object.keys(c.d))for(const part of new Set([d,...d.split(/\s*-\s*/)])){const n=norm(part).replace(/^l /,"");
        if(n.length>=4&&!STOP.has(n)&&NT.includes(" "+n+" "))hits.push({k,d,len:n.length});}}
    if(!hits.length)return false;hits.sort((a,b)=>b.len-a.len);const top=hits.filter(h=>h.len===hits[0].len);
    if(!top.every(h=>h.k===top[0].k&&h.d===top[0].d))return false;out.ck=top[0].k;out.d=top[0].d;got.push("distrito");return true;};
  busca(sinDir);
  return {out,got};
}

// ---------- environment from OpenStreetMap
const OVERPASS=["https://overpass-api.de/api/interpreter","https://overpass.kumi.systems/api/interpreter"];
async function overpass(lat,lon){
  const a=`(around:%R,${lat},${lon})`;const R=(r,s)=>s.replace("%R",r);
  const q=`[out:json][timeout:20];(`+
   `node${R(1200,a)}[railway~"^(station|halt|tram_stop)$"];node${R(1200,a)}[public_transport=station];`+
   `node${R(400,a)}[highway=bus_stop];`+
   `node${R(600,a)}[shop~"^(supermarket|convenience|greengrocer|bakery)$"];way${R(600,a)}[shop=supermarket];`+
   `node${R(1500,a)}[amenity~"^(pharmacy|clinic|doctors|hospital)$"];way${R(1500,a)}[amenity~"^(clinic|hospital)$"];node${R(1500,a)}[healthcare~"^(centre|clinic|hospital)$"];way${R(1500,a)}[healthcare~"^(centre|clinic|hospital)$"];`+
   `node${R(1000,a)}[amenity~"^(school|kindergarten)$"];way${R(1000,a)}[amenity~"^(school|kindergarten)$"];`+
   `way${R(1200,a)}[leisure~"^(park|garden)$"];relation${R(1200,a)}[leisure=park];`+
   `node${R(250,a)}[amenity~"^(bar|pub|nightclub)$"];`+
   `way${R(70,a)}[highway~"^(motorway|trunk|primary)$"];way${R(150,a)}[railway=rail];`+
   `);out center tags;`;
  let last;
  for(const url of OVERPASS){
    try{const ctl=new AbortController();const to=setTimeout(()=>ctl.abort(),14000);
      const r=await fetch(url,{method:"POST",body:"data="+encodeURIComponent(q),signal:ctl.signal,headers:{"Content-Type":"application/x-www-form-urlencoded"}});clearTimeout(to);
      if(r.ok)return (await r.json()).elements||[];last=r.status;}catch(e){last=e;}
  }
  throw last;
}
function classify(els,pt){
  const o={st:[],bus:0,shops:[],farm:[],salud:[],hosp:[],cole:0,parks:[],bars:0,road:null,rail:false};
  const pos=e=>e.center?[e.center.lat,e.center.lon]:[e.lat,e.lon];
  const seen=new Set();
  for(const e of els){const t=e.tags||{},p=pos(e);if(!p[0])continue;const km=hav(pt,p);
    if(t.railway==="station"||t.railway==="halt"||t.railway==="tram_stop"||t.public_transport==="station"){
      if(!t.name)continue;
      let typ=t.station==="subway"||t.subway==="yes"?"Metro":(t.railway==="tram_stop"||t.station==="light_rail"||t.tram==="yes"||t.light_rail==="yes")?"Tranvía":(t.train==="yes"||t.station==="train"||t.railway==="halt"||t.railway==="station")?"Tren":"Estación";
      const key=norm(t.name)+typ;if(seen.has(key))continue;seen.add(key);
      o.st.push({n:t.name,typ,km,l:(t.line||t.ref||"").split(/[;,]/).map(s=>s.trim()).filter(s=>s&&s.length<5).slice(0,4)});}
    else if(t.highway==="bus_stop")o.bus++;
    else if(t.shop)o.shops.push({n:t.name||{supermarket:"Supermercado",convenience:"Tienda de alimentación",greengrocer:"Frutería",bakery:"Panadería"}[t.shop]||"Tienda",km,s:t.shop});
    else if(t.amenity==="pharmacy")o.farm.push({n:t.name||"Farmacia",km});
    else if(t.amenity==="hospital"||t.healthcare==="hospital")o.hosp.push({n:t.name||"Hospital",km});
    else if(t.amenity==="clinic"||t.amenity==="doctors"||t.healthcare==="centre"||t.healthcare==="clinic")o.salud.push({n:t.name||"Centro de salud",km});
    else if(t.amenity==="school"||t.amenity==="kindergarten")o.cole++;
    else if(t.leisure)o.parks.push({n:t.name||"Parque",km});
    else if(t.amenity==="bar"||t.amenity==="pub"||t.amenity==="nightclub")o.bars++;
    else if(t.highway){if(!o.road||km<o.road.km)o.road={n:t.name||t.ref||"una vía principal",km};}
    else if(t.railway==="rail")o.rail=true;
  }
  const by=a=>a.sort((x,y)=>x.km-y.km);[o.st,o.shops,o.farm,o.salud,o.hosp,o.parks].forEach(by);
  o.st=o.st.slice(0,5);o.named=o.parks.filter(p=>p.n!=="Parque");
  return o;
}
function madFallback(pt){
  const st=MAD.stations.map(s=>({n:s.n,typ:s.t==="ML"?"Metro ligero":"Metro",l:s.l,km:hav(pt,[s.y,s.x])})).sort((a,b)=>a.km-b.km).filter(s=>s.km<=1.2).slice(0,5);
  return {st,bus:null,shops:[],farm:[],salud:[],hosp:[],cole:null,parks:[],named:[],bars:null,road:null,rail:false,partial:true};
}
const ENV={};
async function environment(pt,ck){
  const key=pt.join(",");if(ENV[key])return ENV[key];
  try{return ENV[key]=classify(await overpass(pt[0],pt[1]),pt);}
  catch(e){return ck==="madrid"?madFallback(pt):null;}
}
async function commute(pt,w0,q,ck){
  q=(q||"").trim();if(!q)return null;
  try{let p=await geocode(/,/.test(q)?q:q+", "+C[ck].n);if(!p)return {n:q,err:true};
    const km=hav(pt,p);if(km>60)return {n:q,far:true,km};return {n:q,km,min:km<1.2?walkMin(km):Math.round(Math.min(w0,15)+4+km*2.7+(km>4?5:0)+6)};}
  catch(e){return {n:q,err:true};}
}

// ---------- valoración
const M2HAB={0:40,1:55,2:75,3:95,4:115,5:140};
function valuation(f,ck,d){
  let k=1;const why=[];const add=(v,t)=>{if(v){k*=1+v;why.push([t,v]);}};
  if(f.planta===-1)add(-.18,"Semisótano");else if(f.planta===0)add(-.10,"Planta baja");
  else if(f.planta===99)add(.06,"Ático");else if(f.planta>=4&&f.ex.asc)add(.03,"Planta alta con ascensor");
  if(!f.ex.asc&&f.planta>=3)add(-.14,f.planta===99?"Ático sin ascensor":"Sin ascensor en planta "+f.planta);else if(!f.ex.asc&&f.planta>=1)add(-.06,"Sin ascensor");
  add(f.ex.ext?.03:-.08,f.ex.ext?"Exterior":"Interior");
  add({reformar:-.15,bueno:0,reformado:.07,nuevo:.12}[f.estado],{reformar:"A reformar",reformado:"Reformado",nuevo:"Obra nueva"}[f.estado]);
  if(f.ex.ter)add(.04,"Terraza o balcón");
  if(f.ex.gar&&f.op==="venta")add(.05,"Garaje incluido");
  if(f.ex.tra)add(.01,"Trastero");
  if(f.ori==="S")add(.02,"Orientación sur");else if(f.ori==="N")add(-.02,"Orientación norte");
  if(f.m2<45)add(.07,"Piso pequeño (el €/m² sube)");else if(f.m2>130)add(-.05,"Piso grande (el €/m² baja)");
  if(f.anio<1960&&f.estado!=="reformado"&&f.estado!=="nuevo")add(-.03,"Edificio antiguo");
  k=Math.min(1.45,Math.max(.6,k));
  const p=dPrice(ck,d);
  return {k,why,sale:p.s*k*f.m2,rent:p.r*k*f.m2*(f.m2<45?1.04:1),baseS:p.s,baseR:p.r,est:p.est,es:p.es,er:p.er,city:p.city};
}
function verdict(dev,fem){
  if(dev===null)return ["Sin precio","pw",6.5];
  const a=fem?"a":"o";
  if(dev>.15)return [fem?"Cara":"Caro","pb",score(7-dev*20)];
  if(dev>.06)return ["Algo car"+a,"pw",score(7-dev*20)];
  if(dev>=-.06)return ["En precio de mercado","pg",score(7-dev*20)];
  if(dev>=-.18)return ["Buen precio","pg",score(7-dev*20)];
  return ["Muy barat"+a+": revisa por qué","pw",6.5];
}
function envScores(env,f,pt){
  const pros=[],cons=[],info=[];
  let tr=3,ent=6,q={tranq:8.5,normal:6.5,ruido:3.5,peat:7.5}[f.calle];
  if(env){
    const s0=env.st[0];const w0=s0?walkMin(s0.km):30;
    tr=w0<=5?10:w0<=8?8.5:w0<=12?7:w0<=18?5:3;
    tr+=Math.min(1.5,Math.max(0,env.st.filter(s=>walkMin(s.km)<=10).length-1)*.5);
    if(env.bus!=null)tr+=env.bus>=4?.5:env.bus===0?-1:0;
    if(!env.partial){
      const sh=env.shops.find(s=>s.s==="supermarket")||env.shops[0];
      ent=5;if(sh&&sh.km<.35)ent+=1.5;else if(!sh)ent-=1;
      if(env.farm[0]&&env.farm[0].km<.4)ent+=.5;
      const sal=env.salud[0]||env.hosp[0];if(sal&&sal.km<1)ent+=.75;
      const pk=env.parks[0];if(pk&&pk.km<.3)ent+=1.5;else if(pk&&pk.km<.8)ent+=.75;
      if(env.cole>=2)ent+=.5;
      if(env.road&&env.road.km<.07){q-=2;cons.push(`Junto a ${esc(env.road.n)}: ruido de tráfico. Pide ver el piso con las ventanas abiertas.`);}
      if(env.rail){q-=1;info.push("Hay una vía de tren cerca: comprueba si se oye el paso de los trenes.");}
      if(env.bars>=8){q-=1.5;cons.push(`Zona de bares y ocio (${env.bars} locales a menos de 250 m): ruido por la noche, sobre todo los fines de semana.`);}
      else if(env.bars>=3){q-=.5;info.push(`Hay ${env.bars} bares a menos de 250 m: ambiente, pero mira el ruido nocturno.`);}
      else if(env.bars===0)pros.push("Sin bares justo al lado: suele ser más tranquilo de noche.");
    }
  }
  if(!f.ex.ext)q+=1.5;if(f.planta>=4&&f.planta!==99)q+=1;if(f.planta<=0&&f.ex.ext)q-=1.5;if(f.anio>=2005)q+=.5;
  return {tr:score(tr),ent:score(ent),q:score(q),pros,cons,info};
}
function flatReport(r){
  const {f,ck,d,es}=r;const pros=[...es.pros],cons=[...es.cons],info=[...es.info];
  const rooms=Math.max(1,f.hab),m2r=f.m2/(rooms+1);let lay=6.5;
  if(f.hab===0)info.push(`Estudio de ${f.m2} m²: ideal para una persona.`);
  else if(m2r>=24){lay+=1.5;pros.push(`Amplio: ${Math.round(f.m2/rooms)} m² por habitación.`);}
  else if(m2r<17){lay-=2;cons.push(`Justo de espacio: ${Math.round(f.m2/rooms)} m² por habitación. Comprueba que el salón no sea un pasillo.`);}
  if(f.hab>=3&&f.ban<2){lay-=1.5;cons.push(`${f.hab} habitaciones con un solo baño: incómodo para familias o pisos compartidos.`);}
  if(f.ban>=2&&f.hab>=2){lay+=1;pros.push("Dos baños o más: punto muy a favor.");}
  if(f.ex.ext){lay+=.5;pros.push("Exterior: más luz natural.");}else{lay-=1.5;cons.push("Interior: menos luz. Visítalo de día y mira a qué da cada ventana.");}
  if(f.ori==="S"){lay+=1;pros.push("Orientación sur: sol en invierno y ahorro en calefacción.");}else if(f.ori==="N"){lay-=.5;cons.push("Orientación norte: poco sol directo; más frío en invierno.");}
  else if(f.ori==="O")info.push("Orientación oeste: mucho sol por la tarde; en verano puede dar calor.");else if(f.ori==="E")pros.push("Orientación este: sol de mañana, fresco por la tarde.");
  if(f.ex.ter){lay+=.75;pros.push("Terraza o balcón: muy valorado (y se revaloriza).");}
  if(f.planta===-1){lay-=2;cons.push("Semisótano: riesgo de humedad y poca luz; se revende peor.");}
  else if(f.planta===0){lay-=1;cons.push("Planta baja: revisa humedades, ruido de la calle y seguridad.");}
  if(f.planta===99){lay+=.5;pros.push("Ático: más luz y sin vecinos encima.");info.push("Ático: pregunta por el aislamiento del techo y si ha habido goteras.");}
  let cf=6+{reformar:-2.5,bueno:0,reformado:1.5,nuevo:2.5}[f.estado];
  if(!f.ex.asc&&f.planta>=2){cf-=2;cons.push(`Sin ascensor en un ${f.planta===99?"ático":f.planta+"º"}: cuesta con la compra, con niños y a largo plazo.`);}else if(f.ex.asc)pros.push("Con ascensor.");
  if(f.cal==="no"){cf-=2;cons.push("Sin calefacción: suma el coste de instalarla.");}else if(f.cal==="cen")info.push("Calefacción central: cómoda, pero va en la comunidad y no controlas el horario. Pregunta cuánto suma al año.");
  if(f.ex.aa){cf+=1;pros.push("Aire acondicionado.");}else{cf-=.5;info.push("Sin aire acondicionado: piensa en el verano de tu ciudad.");}
  if(f.com>0){const pm=f.com/f.m2;if(pm>1.6)cons.push(`Comunidad alta: ${eur(f.com)} al mes (${dec(pm)} €/m²). Pregunta qué incluye.`);else pros.push(`Comunidad razonable: ${eur(f.com)} al mes.`);}
  const v=valuation(f,ck,d),est=f.op==="venta"?v.sale:v.rent;
  const dev=f.precio>0?(f.precio-est)/est:null;let [ver,cls,pr]=verdict(dev,false);if(f.m2est&&dev!==null){ver="Precio orientativo";cls="pw";pr=6.5;}
  const parts=[["Transporte",es.tr,.25],["Precio",pr,.2],["Distribución",score(lay),.2],["Tranquilidad",es.q,.15],["Confort",score(cf),.1],["Servicios y verde",es.ent,.1]];
  const chk=["Visítalo de día y, si puedes, otra vez de noche: luz, ruido y ambiente cambian mucho.","Abre grifos y ducha a la vez: presión y tiempo que tarda el agua caliente.","Mira techos, esquinas y detrás de muebles: manchas de humedad o pintura reciente sospechosa.","Comprueba la cobertura del móvil y pregunta si hay fibra en el edificio.","Cierra las ventanas y escucha: ¿se oye la calle, el ascensor o los vecinos?"];
  if(f.anio<1980)chk.push("Edificio anterior a 1980: pide la inspección técnica del edificio y pregunta por derramas aprobadas o previstas (fachada, bajantes, ascensor).");
  if(f.anio<2002&&f.anio>=1950)chk.push("Edificio construido antes de 2002: pregunta si hay amianto en bajantes o cubiertas.");
  if(f.op==="venta")chk.push("Pide la nota simple del Registro de la Propiedad: titular real y si tiene cargas o hipotecas.","Pide el certificado de la comunidad de que no hay deudas y el último recibo del IBI.","Pide el certificado energético (es obligatorio para vender).");
  else chk.push("Por ley (Ley 12/2023), los honorarios de la inmobiliaria los paga el propietario, no tú.","La fianza legal es 1 mes; como garantía adicional te pueden pedir como máximo 2 meses más.","Haz fotos y un inventario el día de la entrega y adjúntalo al contrato.","Pide el certificado energético y confirma quién paga la comunidad y el IBI.");
  return ({...r,v,est,dev,ver,cls,parts,pros,cons,info,chk,title:`${f.hab?f.hab+" hab · ":"Estudio · "}${f.m2est?"≈ ":""}${f.m2} m²`});
}
function roomReport(r){
  const {f,ck,d,es}=r;const pros=[...es.pros],cons=[...es.cons],info=[...es.info];
  let k=1;const why=[];const add=(v,t)=>{if(v){k*=1+v;why.push([t,v]);}};
  if(f.rm2<8)add(-.12,"Habitación pequeña");else if(f.rm2>=14)add(.08,"Habitación grande");
  if(f.rban==="priv")add(.18,"Baño privado");
  if(f.pers>=5)add(-.06,f.pers>=6?"Piso de 6 o más":"Piso de 5 personas");else if(f.pers===2)add(.05,"Solo 2 personas");
  if(f.vent==="no")add(-.2,"Sin ventana");else if(f.vent==="patio")add(-.05,"Ventana a patio");
  if(f.cama==="ind")add(-.04,"Cama individual");
  if(f.gastos==="inc")add(.09,"Gastos incluidos");
  if(f.ex.aa)add(.03,"Aire acondicionado");if(f.ex.ter)add(.02,"Terraza o balcón");
  if(!f.ex.asc&&f.planta>=3)add(-.05,"Sin ascensor");
  k=Math.min(1.5,Math.max(.6,k));
  const base=roomBase(ck,d),est=base*k;
  const dev=f.precio>0?(f.precio-est)/est:null;const [ver,cls,pr]=verdict(dev,true);
  const perBath=f.rban==="priv"?1:f.pers/(+f.rban);let cv=7;
  if(f.rban==="priv"){cv+=2;pros.push("Baño privado: la mayor ventaja en un piso compartido.");}
  else if(perBath>=4){cv-=2.5;cons.push(`${f.pers} personas para ${f.rban} baño${f.rban==="1"?"":"s"}: habrá colas por las mañanas.`);}
  else if(perBath>=3){cv-=1;cons.push(`${f.pers} personas para ${f.rban} baño${f.rban==="1"?"":"s"}: justo.`);}
  else pros.push(`Buena proporción de baños: ${f.pers} personas para ${f.rban} baño${f.rban==="1"?"":"s"}.`);
  if(f.pers>=5){cv-=1;cons.push("Piso con muchas personas: más ruido, cocina y nevera más llenas.");}else if(f.pers<=3)pros.push("Pocos compañeros: más fácil convivir y organizarse.");
  if(f.rm2<7){cv-=2;cons.push(`Habitación muy pequeña (${f.rm2} m²): comprueba que entran cama, armario y mesa.`);}
  else if(f.rm2<9){cv-=.5;info.push(`Habitación justa (${f.rm2} m²): mira si tiene armario empotrado.`);}else if(f.rm2>=12)pros.push(`Habitación amplia (${f.rm2} m²).`);
  if(f.vent==="no"){cv-=3;cons.push("Sin ventana: sin luz ni ventilación; muchas veces ni siquiera cuenta como dormitorio. Mejor evitarla.");}
  else if(f.vent==="patio")info.push("Ventana a patio: más tranquila pero con menos luz.");else pros.push("Ventana a la calle: luz natural.");
  if(f.cama==="doble")pros.push("Cama doble.");
  if(f.gastos==="inc")pros.push("Gastos incluidos: sabes lo que pagas. Pregunta si hay un tope de luz.");else info.push("Gastos aparte: suma unos 40–70 € al mes (luz, agua, gas e internet a repartir).");
  if(f.ex.cer)pros.push("Cerradura en la habitación.");if(f.ex.lav)pros.push("Lavavajillas: menos discusiones por la cocina.");
  let cf=6.5;if(!f.ex.asc&&f.planta>=2){cf-=1.5;cons.push(`Sin ascensor en un ${f.planta===99?"ático":f.planta+"º"}.`);}
  if(f.cal==="no"){cf-=2;cons.push("Sin calefacción: pregunta qué hay para el invierno (radiador eléctrico = factura más alta).");}
  if(f.ex.aa){cf+=1.5;pros.push("Aire acondicionado.");}else{cf-=1;info.push("Sin aire acondicionado: en verano las habitaciones pequeñas se calientan mucho.");}
  let q=es.q;if(f.vent==="patio")q=score(q+1.5);if(f.pers>=5)q=score(q-1);
  const parts=[["Transporte",es.tr,.25],["Precio",pr,.25],["Convivencia",score(cv),.2],["Tranquilidad",q,.1],["Confort",score(cf),.1],["Servicios y verde",es.ent,.1]];
  const chk=["Pide contrato por escrito, aunque sea una habitación: precio, fianza, duración, preaviso y qué gastos se pagan.","Pregunta si te puedes empadronar: lo necesitas para la tarjeta sanitaria y muchos trámites.","La fianza de una habitación se pacta (lo normal es 1 mes): que conste en el contrato y paga siempre por transferencia.","Si quien alquila es otro inquilino y no el dueño, pide ver la autorización por escrito del propietario para subarrendar.","Conoce a tus compañeros antes de decidir: horarios, si trabajan o estudian, visitas, mascotas, tabaco.","Pregunta las normas de la casa: limpieza, espacio en la nevera, visitas que se quedan a dormir.","Haz fotos de la habitación y de los muebles el día que entres y mándalas por escrito al casero."];
  return ({...r,room:true,base,est,dev,ver,cls,parts,pros,cons,info,chk,v:{why},title:`Habitación de ${f.rm2est?"≈ ":""}${f.rm2} m² · piso de ${f.pers} personas`});
}


// ---------- informe completo: lo usan todos los formatos (web, conversación, app, WhatsApp…)
// f: datos del piso (ver LEEME.md) · lugar: {ck,d,pt,auto} · trabajo: texto libre o ""
const FALLOS={m2:"Los metros del piso deben estar entre 15 y 600 m².",rm2:"Los m² de la habitación deben estar entre 4 y 40 m².",precioBajo:"Ese precio es muy poco para comprar un piso.",precioAlto:"Ese precio al mes parece un precio de venta.",lugar:"Falta saber dónde está el piso."};
// si el precio no cuadra con el modo, devuelve el modo que toca (o null)
function modoPorPrecio(op,p){if(op==="venta"&&p>0&&p<5000)return p<900?"habitacion":"alquiler";if(op!=="venta"&&p>=20000)return "venta";return null;}
// pone los valores que faltan (y lo apunta en f.m2est / f.rm2est)
function completar(f){
  f=Object.assign({op:"venta",precio:0,m2:0,hab:2,ban:1,planta:2,estado:"bueno",anio:1975,ori:"?",cal:"ind",calle:"normal",com:0,rm2:0,pers:3,rban:"1",gastos:"no",vent:"calle",cama:"doble"},f);
  f.ex=Object.assign({asc:1,ext:1},f.ex||{});
  if(f.op!=="habitacion"&&!f.m2){f.m2=M2HAB[f.hab]||75;f.m2est=true;}
  if(f.op==="habitacion"&&!f.rm2){f.rm2=10;f.rm2est=true;}
  return f;
}
// devuelve el código del fallo (clave de FALLOS) o null si se puede hacer el informe
function fallo(f,lugar){
  if(lugar&&(!C[lugar.ck]||(!lugar.pt&&!lugar.d&&!lugar.media)))return "lugar";
  if(f.op!=="habitacion"&&(f.m2<15||f.m2>600))return "m2";
  if(f.op==="habitacion"&&(f.rm2<4||f.rm2>40))return "rm2";
  if(f.op==="venta"&&f.precio>0&&f.precio<30000)return "precioBajo";
  if(f.op!=="venta"&&f.precio>=20000)return "precioAlto";
  return null;
}
async function informe(f,lugar,trabajo){
  f=completar(f);const {ck,d,pt}=lugar;
  const err=fallo(f,lugar);if(err)return {error:err,mensaje:FALLOS[err]};
  const env=pt?await environment(pt,ck):null;
  const w0=env&&env.st[0]?walkMin(env.st[0].km):env?30:12;
  const work=pt?await commute(pt,w0,trabajo,ck):null;
  const es=envScores(env,f,pt);
  if(work&&!work.err&&!work.far){if(work.min>45)es.tr=score(es.tr-1.5);else if(work.min<=25)es.tr=score(es.tr+.5);}
  if(f.m2est)es.info.unshift(`No sé los metros: he supuesto ${f.m2} m², lo normal con ${f.hab?f.hab+" habitaci"+(f.hab>1?"ones":"ón"):"un estudio"}. Dime los metros para afinar.`);
  if(f.rm2est)es.info.unshift("No sé los m² de la habitación: he supuesto 10 m², lo habitual. Dime los metros para afinar.");
  const r={f,ck,d:C[ck].d[d]?d:"",pt:pt||null,auto:lugar.auto||"",env,work,es};
  const x=f.op==="habitacion"?roomReport(r):flatReport(r);
  const c=C[ck];x.room=!!x.room;
  // Sin datos de la zona (sin punto exacto u OpenStreetMap caído) no se puntúan transporte ni servicios: la nota sale de lo que sí se sabe.
  if(!env)x.parts=x.parts.filter(p=>p[0]!=="Transporte"&&p[0]!=="Servicios y verde");
  x.tot=x.parts.reduce((s,p)=>s+p[1]*p[2],0)/x.parts.reduce((s,p)=>s+p[2],0);
  x.tv=x.tot>=7.5?(x.room?"Buena habitación 👍":"Se vive bien aquí 👍"):x.tot>=6?"Está bien, con matices":"Piénsatelo dos veces";
  x.place=(x.auto?x.auto+", ":"")+(d||"")+(d?", ":"")+c.n;
  x.sum=`${dec(x.tot)}/10 · ${x.tv.replace(/ 👍/,"")} · ${x.title} · ${x.place}${f.precio?` · ${eur(f.precio)}${f.op==="venta"?"":"/mes"}`:""}`;
  return x;
}
