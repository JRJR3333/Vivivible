// Vivible · el informe como HTML (lo comparten los formatos de navegador) y como texto (WhatsApp, avisos…).
// Recibe lo que devuelve informe() del núcleo. No toca la pantalla: devuelve cadenas.
function ring(v,c){return `<div class="ring" role="img" aria-label="Nota ${dec(v)} sobre 10" style="--p:${v*10};--c:${c}"><div>${dec(v)}<small>sobre 10</small></div></div>`;}
const barCol=v=>v>=7.5?"#1f7a4d":v>=5.5?"#d39b3a":"#b23b3b";
function informeHTML(x){
  const {f,ck,d,env,work}=x,c=C[ck],op=f.op,room=x.room,tot=x.tot,tv=x.tv,place=x.place;
  let h=`<section class="card"><div class="score">${ring(tot,barCol(tot))}<div><p class="verdict">${tv}</p><div style="color:var(--mute);font-size:14px">${x.title} · ${esc(place)}</div>${x.dev!==null?`<div style="margin-top:8px"><span class="pill ${x.cls}">${x.ver}</span></div>`:""}</div></div><div class="bars">`+
    x.parts.map(p=>`<div class="bar"><span>${p[0]}</span><div class="t"><b style="width:${p[1]*10}%;background:${barCol(p[1])}"></b></div><span>${dec(p[1])}</span></div>`).join("")+`</div>
    <div class="actions noprint" style="margin-top:14px"><button class="btn2" id="pdf">Guardar en PDF</button><button class="btn2" id="share">Compartir informe</button></div><div id="shareMsg" class="ok noprint" role="status" aria-live="polite"></div></section>`;
  // price
  const lo=x.est*.9,hi=x.est*1.1,mo=op==="venta"?"":"/mes";
  h+=`<section class="card"><h2>💶 ${op==="venta"?"¿Cuánto vale?":"¿Cuánto debería costar?"}</h2><p class="hint">${room?`Estimación a partir del precio medio de una habitación en ${c.n} (${eur(c.hab)}/mes) ajustado al distrito y a lo que ofrece.`:`Estimación según el precio medio de ${d||c.n} y las características del piso.`}${!room&&f.m2est?` <b>Calculado con ≈ ${f.m2} m² supuestos: pon los metros reales para saber si está bien de precio.</b>`:""}</p>
  <div class="row2"><div class="box"><div class="l">${op==="venta"?"Valor estimado":room?"Precio razonable":"Alquiler razonable"}</div><div class="big">${eur(x.est)}${mo}</div><div class="l">Horquilla: ${eur(lo)} – ${eur(hi)}${mo}</div></div>
  <div class="box"><div class="l">Lo que piden</div><div class="big">${f.precio?eur(f.precio)+mo:"—"}</div>${x.dev!==null?`<div class="l">${Math.round(x.dev*100)===0?"Igual que":(x.dev>0?"+":"−")+Math.abs(Math.round(x.dev*100))+" % frente a"} la estimación</div>`:'<div class="l">Pon el precio para compararlo</div>'}</div></div><div class="kv" style="margin-top:12px">`;
  if(room)h+=`<div>Habitación media en ${d||c.n}</div><div>${eur(x.base)}/mes</div><div>Media de ${c.n}</div><div>${eur(c.hab)}/mes</div>`;
  else{h+=`<div>Precio medio en ${d||c.n}${(op==="venta"?x.v.es:x.v.er)?" (estimado)":""}</div><div>${op==="venta"?fmt(x.v.baseS)+" €/m²":dec(x.v.baseR)+" €/m²/mes"}</div>`+(f.precio?`<div>Este piso</div><div>${op==="venta"?fmt(f.precio/f.m2)+" €/m²":dec(f.precio/f.m2)+" €/m²/mes"}</div>`:"")+`<div>Media de ${c.n}</div><div>${op==="venta"?fmt(c.venta)+" €/m²":dec(c.alquiler)+" €/m²/mes"}</div>`;}
  h+=`</div>`;
  if(x.v.why.length)h+=`<ul class="pc">`+x.v.why.map(w=>`<li class="${w[1]>0?"p":"c"}">${w[0]}: ${w[1]>0?"+":""}${Math.round(w[1]*100)} %</li>`).join("")+`</ul>`;
  if(x.dev!==null&&x.dev<-.18&&(room||!f.m2est))h+=room?`<p class="note">⚠️ Mucho más barata que lo normal: desconfía si te piden pagar la fianza antes de verla o sin contrato. Es la estafa más común.</p>`:`<p class="note">⚠️ Un precio muy por debajo del mercado suele tener explicación: ocupación, nuda propiedad, cargas, derramas o un error en los metros. Pregunta antes de ir.</p>`;
  if(op==="venta"){const p=f.precio||x.est,nuevo=f.estado==="nuevo",taxes=nuevo?p*(.1+c.ajd/100):p*c.itp/100,other=p*.015+400,loan=p*.8,i=.028/12,n=360,cuota=loan*i/(1-Math.pow(1+i,-n));
    h+=`<h2 style="margin-top:16px">🧾 Si lo compras</h2>${f.precio?"":`<p class="hint">Calculado con el valor estimado (${eur(p)}). Pon el precio que piden para afinarlo.</p>`}<div class="kv"><div>Entrada (20 %)</div><div>${eur(p*.2)}</div><div>${nuevo?`IVA 10 % + AJD ${dec(c.ajd,2).replace(/,?0+$/,"")} %`:`ITP ${c.ccaa} (${String(c.itp).replace(".",",")} %)`}</div><div>${eur(taxes)}</div><div>Notaría, registro, gestoría y tasación (aprox.)</div><div>${eur(other)}</div><div><b>Ahorros necesarios</b></div><div>${eur(p*.2+taxes+other)}</div><div>Cuota hipoteca (80 %, 30 años, 2,8 %)</div><div>${eur(cuota)}/mes</div><div>Ingresos netos recomendados (cuota ≤ 33 %)</div><div>${eur(cuota/.33)}/mes</div></div>
    <p class="note">Si lo alquilaras, sacarías unos ${eur(x.v.rent)}/mes: rentabilidad bruta del ${dec(x.v.rent*12/p*100)} %. Impuestos con el tipo general; puede haber tipos reducidos por edad, vivienda habitual o precio: confírmalo con tu gestor.</p>`;}
  else{const rent=f.precio||x.est,gm=room&&f.gastos!=="inc"?55:0;
    h+=`<h2 style="margin-top:16px">🧾 Al entrar</h2>${f.precio?"":`<p class="hint">Calculado con el alquiler estimado (${eur(rent)}/mes). Pon el precio que piden para afinarlo.</p>`}<div class="kv">`+(room?`<div>Primer mes + fianza habitual (1 mes)</div><div>${eur(rent*2)}</div><div>Coste real al mes${gm?" (con unos 55 € de gastos)":""}</div><div>${eur(rent+gm)}</div>`:`<div>Fianza legal (1 mes)</div><div>${eur(rent)}</div><div>Garantía adicional máxima (2 meses)</div><div>${eur(rent*2)}</div><div>Honorarios de agencia</div><div>0 € (los paga el propietario)</div>`)+`<div>Ingresos netos recomendados (≤ 33 %)</div><div>${eur((rent+gm)/.33)}/mes</div></div>`;}
  h+=`</section>`;
  // transport
  if(env){h+=`<section class="card"><h2>🚇 Transporte</h2><p class="hint">Estaciones a menos de 1,2 km y tiempo andando (estimado).</p>${env.partial?`<p class="note">⚠️ OpenStreetMap no responde ahora: solo te enseño el metro. Faltan autobuses, servicios y ruido de la zona; vuelve a intentarlo en un rato.</p>`:""}`+
    (env.st.length?env.st.map(s=>`<div class="st"><span>${esc(s.n)} <span class="ln">${s.typ}</span>${(s.l||[]).map(l=>`<span class="ln">${esc(l)}</span>`).join("")}</span><b>${walkMin(s.km)} min</b></div>`).join(""):`<p class="hint">No hay estaciones de metro, tranvía ni tren a menos de 1,2 km: dependerás del autobús o del coche.</p>`)+
    `<div class="kv" style="margin-top:10px">${env.bus!=null?`<div>Paradas de autobús a menos de 400 m</div><div>${env.bus}</div>`:""}${work?work.err?`<div>Al trabajo</div><div>no encontré «${esc(work.n)}»</div>`:work.far?`<div>Al trabajo (${esc(work.n)})</div><div>a ${fmt(work.km)} km: demasiado lejos para ir cada día</div>`:`<div>Al trabajo (${esc(work.n)})</div><div>≈ ${work.min} min</div>`:""}</div><p class="note">Tiempo al trabajo aproximado: andando + espera + trayecto + transbordos.</p></section>`;}
  else if(!x.pt)h+=`<section class="card noprint"><h2>📍 Falta el punto exacto</h2><p class="hint">Este informe usa la media ${d?"del distrito":"de la ciudad"}. Si escribes la dirección o tocas en el mapa, te digo también el metro más cercano, el tiempo al trabajo, los supermercados, los parques y el ruido de la calle. Mientras tanto, la nota no cuenta transporte ni servicios.</p><button class="btn2" id="toMap">Marcar el piso en el mapa</button></section>`;
  else h+=`<section class="card"><h2>🚇 Transporte y servicios</h2><p class="hint">No he podido consultar ahora los datos de la zona (OpenStreetMap no responde), así que la nota no los cuenta. Vuelve a pulsar «Ver informe» en un rato.</p></section>`;
  // services
  if(env&&!env.partial){const sh=env.shops.find(s=>s.s==="supermarket");const sal=env.salud[0];
    h+=`<section class="card"><h2>🛒 Servicios y zonas verdes</h2><div class="kv">`+
    `<div>Supermercado más cercano</div><div>${sh?esc(sh.n)+" · "+dist(sh.km):"ninguno a menos de 600 m"}</div>`+
    `<div>Tiendas de alimentación a menos de 600 m</div><div>${env.shops.length}</div>`+
    `<div>Farmacia más cercana</div><div>${env.farm[0]?dist(env.farm[0].km):"más de 1,5 km"}</div>`+
    `<div>Centro de salud o clínica</div><div>${sal?esc(sal.n)+" · "+dist(sal.km):"más de 1,5 km"}</div>`+
    `${env.hosp[0]?`<div>Hospital</div><div>${esc(env.hosp[0].n)} · ${dist(env.hosp[0].km)}</div>`:""}`+
    `<div>Colegios y escuelas infantiles a menos de 1 km</div><div>${env.cole}</div>`+
    `<div>Parque más cercano</div><div>${env.parks[0]?(env.named[0]&&env.named[0].km-env.parks[0].km<.2?esc(env.named[0].n):"Zona verde")+" · "+dist(env.parks[0].km):"ninguno a menos de 1,2 km"}</div>`+
    `<div>Parques y jardines a menos de 1,2 km</div><div>${env.parks.length}</div></div><p class="note">Datos de OpenStreetMap: pueden faltar locales recientes.</p></section>`;}
  h+=`<section class="card"><h2>🏠 ${room?"Convivencia y confort":"Distribución, ruido y confort"}</h2><ul class="pc">`+x.pros.map(t=>`<li class="p">${t}</li>`).join("")+x.cons.map(t=>`<li class="c">${t}</li>`).join("")+x.info.map(t=>`<li class="i">${t}</li>`).join("")+`</ul></section>`;
  h+=`<section class="card"><h2>📋 ${room?"Antes de decir que sí":"Qué revisar en la visita"}</h2><ul class="pc">`+x.chk.map(t=>`<li class="q">${t}</li>`).join("")+`</ul></section>`;
  return h;
}
function informeTexto(x){
  const {f,env,work}=x,c=C[x.ck],mo=f.op==="venta"?"":"/mes",L=[];
  L.push(`*${dec(x.tot)}/10 · ${x.tv}*`,`${x.title} · ${x.place}`,"");
  L.push(`💶 ${f.op==="venta"?"Valor estimado":"Precio razonable"}: ${eur(x.est)}${mo} (entre ${eur(x.est*.9)}${mo} y ${eur(x.est*1.1)}${mo})`);
  if(f.precio)L.push(`Piden ${eur(f.precio)}${mo}`+(x.dev!==null?` → ${x.ver}`:""));
  L.push("",...x.parts.map(p=>`${p[0]}: ${dec(p[1])}`));
  if(env&&env.st.length)L.push("",`🚇 ${env.st.slice(0,3).map(s=>`${s.n} (${s.typ}, ${walkMin(s.km)} min)`).join(" · ")}`);
  if(work&&!work.err)L.push(work.far?`Al trabajo: demasiado lejos (${fmt(work.km)} km)`:`Al trabajo (${work.n}): ≈ ${work.min} min`);
  const sin=t=>t.replace(/<[^>]+>/g,"").replace(/&lt;/g,"<").replace(/&gt;/g,">").replace(/&quot;/g,'"').replace(/&#39;/g,"'").replace(/&amp;/g,"&");
  if(x.pros.length)L.push("",...x.pros.slice(0,4).map(t=>"✅ "+sin(t)));
  if(x.cons.length)L.push(...x.cons.slice(0,4).map(t=>"⚠️ "+sin(t)));
  return L.join("\n");
}
