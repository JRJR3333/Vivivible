// Vivible · la ficha del piso en el navegador: campos, mapa, pegar anuncio, pedir el informe al núcleo,
// pintarlo, compartir y recuperar. La comparten los formatos de navegador (web, conversación, app con WebView…).
// Necesita en la página los campos de fuente/navegador/campos.html y los de lugar, modo, precio y trabajo.
// Cada formato puede cambiar FORMATO.* antes de llamar a iniciarFicha().
const FORMATO={
  // llevar la vista a donde se indica el lugar (dirección o mapa)
  irAlLugar(){const e=$("#dir");e.scrollIntoView({behavior:"smooth",block:"center"});}
};
const $=s=>document.querySelector(s);
// ---------- state & selects
let state={ck:"madrid",d:"",pt:null,op:"venta",ex:{asc:1,ext:1},auto:""};
const selC=$("#ciudad"),selD=$("#distrito");
selC.innerHTML=Object.entries(C).map(([k,c])=>`<option value="${k}">${c.n}</option>`).join("");
function fillD(ck){selD.innerHTML=`<option value="">Media de la ciudad</option>`+Object.keys(C[ck].d).sort((a,b)=>a.localeCompare(b,"es")).map(d=>`<option>${d}</option>`).join("");}
function setCity(ck,keepView){state.ck=ck;selC.value=ck;fillD(ck);state.d="";if(!keepView&&map)map.setView(C[ck].centro,13);}
selC.onchange=()=>{state.media=true;setCity(selC.value);state.pt=null;marker&&marker.remove();marker=null;where();};
selD.onchange=()=>{state.d=selD.value;state.media=true;where();liveUpdate();};
function where(){const c=C[state.ck];$("#where").innerHTML=state.pt?`📍 ${state.auto?esc(state.auto)+" · ":""}${esc(state.d)||"distrito sin identificar"} <small>· ${c.n}</small>`:(state.d?`📍 ${esc(state.d)} <small>· ${c.n} (sin punto exacto)</small>`:state.media?`📍 Media de ${c.n} <small>(sin punto exacto)</small>`:"");}

// ---------- map
let map=null,marker=null;
try{
  map=L.map("map",{scrollWheelZoom:false}).setView(C.madrid.centro,12);
  L.tileLayer("https://tile.openstreetmap.org/{z}/{x}/{y}.png",{maxZoom:19,attribution:"© OpenStreetMap"}).addTo(map);
  map.on("click",async e=>{await setPoint(e.latlng.lat,e.latlng.lng);if(state.pt){liveUpdate();if(state.onPick){const f=state.onPick;state.onPick=null;f();}}else if(state.onPickErr)state.onPickErr($("#dirErr").textContent);});
}catch(e){$("#map").style.display="none";}
function placeMarker(lat,lon){if(!map)return;if(marker)marker.setLatLng([lat,lon]);else marker=L.marker([lat,lon]).addTo(map);}

async function setPoint(lat,lon){
  state.pt=[lat,lon];placeMarker(lat,lon);
  const ck=nearestCity(lat,lon);
  if(!ck){state.pt=null;$("#dirErr").textContent="Ese punto queda fuera de las 10 ciudades disponibles.";marker&&marker.remove();marker=null;return;}
  $("#dirErr").textContent="";
  if(ck!==state.ck)setCity(ck,true);
  state.auto="";state.d="";selD.value="";where();
  const l=await locate(lat,lon);
  if(l&&state.pt&&state.pt[0]===lat&&state.pt[1]===lon){state.d=l.d;state.auto=l.auto;selD.value=state.d;where();}
}
async function buscarDir0(){
  const q=$("#dir").value.trim(),e=$("#dirErr");e.textContent="";if(q.length<4)return;
  e.style.color="var(--mute)";e.textContent="Buscando…";
  try{
    let p=await geocode(/,/.test(q)?q:q+", "+C[state.ck].n);
    if(!p){e.style.color="var(--bad)";e.textContent="No encuentro esa dirección. Prueba con «calle, número, ciudad» o toca en el mapa.";return;}
    e.textContent="";e.style.color="";map&&map.setView(p,16);await setPoint(p[0],p[1]);
  }catch(x){e.style.color="var(--bad)";e.textContent="No he podido buscar ahora. Toca en el mapa o elige ciudad y distrito.";}
}
let lastDir="";
async function buscarDir(){const q=$("#dir").value.trim();lastDir=q;await buscarDir0();if(state.pt)liveUpdate();}
$("#buscar").onclick=buscarDir;$("#dir").addEventListener("keydown",ev=>{if(ev.key==="Enter"){ev.preventDefault();buscarDir();}});
$("#dir").addEventListener("change",()=>{const q=$("#dir").value.trim();if(q.length>=4&&q!==lastDir)buscarDir();});
$("#aqui").onclick=()=>{const e=$("#dirErr");if(!navigator.geolocation){e.textContent="Tu navegador no deja usar la ubicación. Escribe la dirección o toca en el mapa.";return;}
  e.style.color="var(--mute)";e.textContent="Buscando dónde estás…";
  navigator.geolocation.getCurrentPosition(async g=>{e.textContent="";e.style.color="";const la=g.coords.latitude,lo=g.coords.longitude;map&&map.setView([la,lo],16);await setPoint(la,lo);if(state.pt)liveUpdate();},
    ()=>{e.style.color="var(--bad)";e.textContent="No he podido saber dónde estás. Escribe la dirección o toca en el mapa.";},{enableHighAccuracy:true,timeout:10000});};

// ---------- form controls
function setOp(v){state.op=v;[...$("#op").children].forEach(b=>{const on=b.dataset.v===v;b.classList.toggle("on",on);b.setAttribute("aria-pressed",on);});
  $("#precioLbl").textContent={venta:"Precio que piden (€)",alquiler:"Alquiler que piden (€/mes)",habitacion:"Precio de la habitación (€/mes)"}[v];
  $("#precio").placeholder={venta:"p. ej. 320000",alquiler:"p. ej. 1400",habitacion:"p. ej. 550"}[v];
  const room=v==="habitacion";$("#roomFields").style.display=room?"":"none";$("#t3").textContent=room?"La habitación y el piso":"El piso";
  document.querySelectorAll(".po").forEach(e=>e.style.display=room?"none":"");document.querySelectorAll(".ro").forEach(e=>e.style.display=room?"":"none");}
$("#op").onclick=e=>{const v=e.target.dataset.v;if(v)setOp(v);};
function setEx(k,on){state.ex[k]=on?1:0;const b=document.querySelector(`#extras [data-k=${k}]`);if(b){b.classList.toggle("on",!!on);b.setAttribute("aria-pressed",!!on);}}
$("#extras").onclick=e=>{const k=e.target.dataset.k;if(k)setEx(k,!state.ex[k]);};

let lastAd="";
// lee el anuncio y rellena la ficha; devuelve qué ha pasado
async function applyAd(t){
  t=t.trim();
  if(/^https?:\/\/\S+$/.test(t))return {kind:"url"};
  if(t.length<20)return {kind:"corto"};
  const {out,got}=parseAd(t);
  if(got.length<=1)return {kind:"poco"};
  setOp(out.op);
  const setV=(id,v)=>{if(v!=null)$("#"+id).value=v;};
  setV("precio",out.precio);setV("m2",out.m2);setV("hab",out.hab);setV("ban",out.ban);setV("planta",out.planta);setV("estado",out.estado);setV("anio",out.anio);setV("ori",out.ori);setV("cal",out.cal);setV("com",out.com);setV("rm2",out.rm2);setV("rban",out.rban);setV("gastos",out.gastos);setV("pers",out.pers);
  for(const k of ["asc","ext","ter","gar","tra","aa"])if(out[k]!=null)setEx(k,out[k]);
  if(out.ck&&out.ck!==state.ck)setCity(out.ck);
  if(out.d&&C[state.ck].d[out.d]){state.d=out.d;selD.value=out.d;where();}
  if(out.dir){$("#dir").value=out.dir+", "+C[state.ck].n;lastDir=$("#dir").value;await buscarDir0();}
  return {kind:"ok",out,got};
}
const AD_URL="Los portales no dejan leer sus enlaces desde otra web. Abre el anuncio, copia su texto (mantén pulsado → Seleccionar todo → Copiar) y pégamelo.";
async function readAd(auto){
  const t=$("#anuncio").value.trim(),msg=$("#anuncioMsg");
  if(auto&&t===lastAd)return;lastAd=t;
  const r=await applyAd(t);
  if(r.kind==="url"){msg.className="err";msg.textContent=AD_URL;return;}
  if(r.kind==="corto"){if(!auto){msg.className="err";msg.textContent="Pega el texto del anuncio primero.";}return;}
  if(r.kind==="poco"){msg.className="err";msg.textContent="No he sacado casi nada del texto. ¿Has copiado el anuncio entero?";return;}
  msg.className="ok";msg.textContent="He leído: "+r.got.join(", ")+".";
  if(state.pt||state.d){msg.textContent+=" Aquí tienes el informe; si algo no cuadra, cámbialo y se actualiza.";await analyze();}
  else{msg.textContent+=" Me falta dónde está: escribe la dirección o toca en el mapa.";FORMATO.irAlLugar();}
}
$("#rellenar").onclick=()=>readAd(false);
$("#anuncio").addEventListener("paste",()=>setTimeout(()=>readAd(true),50));
let adT;$("#anuncio").addEventListener("input",()=>{clearTimeout(adT);adT=setTimeout(()=>{if($("#anuncio").value.trim().length>=60)readAd(true);},1500);});

// mientras se escribe el trabajo, el cálculo usa lo último confirmado (no busca palabras a medias)
let trabajoOk=null;["focus","change"].forEach(ev=>$("#trabajo").addEventListener(ev,()=>{trabajoOk=$("#trabajo").value;}));
function trabajoTxt(){const tEl=$("#trabajo");return (document.activeElement===tEl&&trabajoOk!==null?trabajoOk:tEl.value).trim();}

// ---------- analysis
function readForm(){
  return {op:state.op,precio:+$("#precio").value||0,m2:+$("#m2").value||0,hab:+$("#hab").value,ban:+$("#ban").value,planta:+$("#planta").value,estado:$("#estado").value,anio:+$("#anio").value,ori:$("#ori").value,cal:$("#cal").value,calle:$("#calle").value,com:+$("#com").value||0,ex:{...state.ex},
    rm2:+$("#rm2").value||0,pers:+$("#pers").value,rban:$("#rban").value,gastos:$("#gastos").value,vent:$("#vent").value,cama:$("#cama").value};
}
let busy=false,again=false;
async function analyze(quiet,typing){
  if(busy){again=[quiet,typing];return;}
  const err=$("#err");err.textContent="";
  let notes=[];
  if(!typing){const p=+$("#precio").value||0,m=modoPorPrecio(state.op,p);
    if(m){setOp(m);notes.push(m==="venta"?`${eur(p)} parece un precio de venta: lo he tratado como compra.`:`${eur(p)} parece un precio al mes: lo he tratado como ${m==="habitacion"?"habitación":"alquiler"}.`);}}
  const f=completar(readForm()),lugar={ck:state.ck,d:state.d,pt:state.pt,auto:state.auto,media:!!state.media};
  const mal=fallo(f,lugar);
  if(mal==="lugar"){if(!quiet)err.textContent="Dime dónde está el piso: dirección, mapa o distrito.";return;}
  if(mal){if(typing)return;
    err.textContent=mal==="m2"?"Revisa los metros del piso: entre 15 y 600 m².":mal==="rm2"?"Revisa los m² de la habitación: entre 4 y 40 m².":mal==="precioBajo"?`${eur(f.precio)} es muy poco para comprar un piso. Si es un alquiler, elige «Alquilar piso»; si es una venta, escribe el precio entero sin puntos (p. ej. 320000).`:FALLOS[mal];
    if(/^precio/.test(mal))$("#precio").focus();return;}
  const btn=$("#go");btn.disabled=true;btn.textContent="Analizando la zona…";busy=true;
  let x;try{x=await informe(f,lugar,trabajoTxt());}finally{btn.disabled=false;btn.textContent="Ver informe";busy=false;}
  if(x.error){err.textContent=x.mensaje;return;}
  render(x,quiet);
  if(notes.length)$("#res").insertAdjacentHTML("afterbegin",`<p class="note" role="status">↺ ${notes.join(" ")}</p>`);
  state.done=true;saveHash();
  try{localStorage.setItem("viv.trabajo",$("#trabajo").value.trim());localStorage.setItem("viv.op",state.op);}catch(e){}
  if(again){const a=again;again=false;analyze(...a);}
}
// tras el primer informe, cualquier cambio lo actualiza solo
let liveT;function liveUpdate(){if(!state.done)return;clearTimeout(liveT);liveT=setTimeout(()=>analyze(true),500);}
document.querySelectorAll(".wrap input:not(#dir):not(#anuncio),.wrap select").forEach(el=>{if(el.id==="ciudad")return;el.addEventListener("change",liveUpdate);});
["precio","m2","rm2","com"].forEach(id=>{const el=$("#"+id);if(el)el.addEventListener("input",()=>{if(!state.done)return;clearTimeout(liveT);liveT=setTimeout(()=>analyze(true,true),800);});});
$("#op").addEventListener("click",liveUpdate);$("#extras").addEventListener("click",liveUpdate);
// ---------- pintar el informe (el HTML lo da informeHTML, común a todos los formatos)
function render(x,quiet){
  state.sum=x.sum;
  const res=$("#res");res.innerHTML=informeHTML(x);res.style.display="block";if(!quiet)res.scrollIntoView({behavior:"smooth",block:"start"});
  $("#pdf").onclick=()=>{try{window.print();}catch(e){}};
  $("#share").onclick=share;
  const tm=$("#toMap");if(tm)tm.onclick=()=>{FORMATO.irAlLugar();setTimeout(()=>$("#dir").focus({preventScroll:true}),400);};
}

// ---------- share & restore
const IDS=["precio","m2","hab","ban","planta","estado","anio","ori","cal","calle","com","rm2","pers","rban","gastos","vent","cama","trabajo","dir"];
function saveHash(){
  const o={c:state.ck,d:state.d,o:state.op,x:state.ex,p:state.pt&&state.pt.map(v=>+v.toFixed(5)),a:state.auto};
  IDS.forEach(i=>{const v=$("#"+i).value;if(v!=="")o[i]=v;});
  try{history.replaceState(null,"","#s="+btoa(unescape(encodeURIComponent(JSON.stringify(o)))));}catch(e){}
}
async function share(){
  saveHash();const url=location.href,m=$("#shareMsg");
  const txt=(state.sum?state.sum+"\n":"")+"Analizado con Vivible:";
  try{if(navigator.share){await navigator.share({title:"Informe Vivible",text:txt,url});return;}}catch(e){}
  try{await navigator.clipboard.writeText(txt+" "+url);m.textContent="Enlace copiado: pégalo donde quieras.";}catch(e){m.textContent=url;}
}
function restore(){
  const h=location.hash.slice(1);if(!h)return;
  let q={};try{q=Object.fromEntries(h.split("&").map(kv=>kv.split("=").map(decodeURIComponent)));}catch(e){return;}
  const OPS=["venta","alquiler","habitacion"];
  if(q.s){try{const o=JSON.parse(decodeURIComponent(escape(atob(q.s))));
      setCity(C[o.c]?o.c:"madrid");setOp(OPS.includes(o.o)?o.o:"venta");
      IDS.forEach(i=>{if(o[i]!=null){const el=$("#"+i),v=String(o[i]).slice(0,120);el.value=v;if(el.tagName==="SELECT"&&el.value!==v)el.selectedIndex=[...el.options].findIndex(x=>x.defaultSelected)>=0?[...el.options].findIndex(x=>x.defaultSelected):0;}});
      Object.keys(state.ex).forEach(k=>setEx(k,0));Object.entries(o.x||{}).forEach(([k,v])=>{if(/^[a-z]{2,4}$/.test(k))setEx(k,v);});
      state.d=C[state.ck].d[o.d]?o.d:"";selD.value=state.d;state.auto=String(o.a||"").slice(0,60);state.media=true;
      if(Array.isArray(o.p)&&o.p.length===2&&o.p.every(Number.isFinite)&&nearestCity(o.p[0],o.p[1])){state.pt=o.p;placeMarker(o.p[0],o.p[1]);map&&map.setView(o.p,15);}
      where();analyze();}catch(e){}return;}
  if(q.c&&C[q.c]){setCity(q.c);state.media=true;if(q.d&&C[q.c].d[q.d]){state.d=q.d;selD.value=q.d;}where();if(OPS.includes(q.op))setOp(q.op);}
}

function iniciarFicha(){
  setCity("madrid",true);
  $("#go").onclick=()=>analyze(false);
  try{const t=localStorage.getItem("viv.trabajo"),o=localStorage.getItem("viv.op");if(t)$("#trabajo").value=t;if(o&&["venta","alquiler","habitacion"].includes(o))setOp(o);}catch(e){}
  restore();
  window.__viv={parseAd,matchDistrict,dPrice,roomBase,classify,state}; // para las pruebas
}
