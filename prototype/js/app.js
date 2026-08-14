const map = L.map('map',{zoomControl:false,attributionControl:true}).setView([13.0827,100.8851],13);
const satellite = L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',{maxZoom:19,attribution:'Tiles © Esri'}).addTo(map);
const street = L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',{maxZoom:19,attribution:'© OpenStreetMap contributors'});
let currentLayer='satellite';
let roi=null, drawnItems=new L.FeatureGroup().addTo(map), analysisLayer=new L.FeatureGroup().addTo(map);
const defaultCenter=[13.0827,100.8851], defaultZoom=13;

function hideLoading(){setTimeout(()=>document.getElementById('loading').classList.add('hide'),1250)}
hideLoading();

document.getElementById('zoomIn').onclick=()=>map.zoomIn();
document.getElementById('zoomOut').onclick=()=>map.zoomOut();
document.getElementById('reset').onclick=()=>map.setView(defaultCenter,defaultZoom);
document.getElementById('layers').onclick=()=>{
 if(currentLayer==='satellite'){map.removeLayer(satellite);street.addTo(map);currentLayer='street';}
 else{map.removeLayer(street);satellite.addTo(map);currentLayer='satellite';}
};
document.getElementById('locate').onclick=()=>map.locate({setView:true,maxZoom:16});
map.on('locationfound',e=>addMessage('assistant',`Location found.<div class="assistant-card"><div class="metric"><span>LAT</span><span>${e.latlng.lat.toFixed(5)}</span></div><div class="metric"><span>LON</span><span>${e.latlng.lng.toFixed(5)}</span></div></div>`));
map.on('locationerror',()=>addMessage('assistant','Location permission is unavailable in this browser.'));

const drawControl=new L.Control.Draw({draw:{polygon:false,polyline:false,circle:false,circlemarker:false,marker:false,rectangle:{shapeOptions:{color:'#fff',weight:2,dashArray:'7 5',fillOpacity:.08}}},edit:{featureGroup:drawnItems}});
document.getElementById('measure').onclick=()=>{document.getElementById('selectBadge').classList.add('show');new L.Draw.Rectangle(map,drawControl.options.draw.rectangle).enable();};
map.on(L.Draw.Event.CREATED,e=>{
 drawnItems.clearLayers(); analysisLayer.clearLayers(); roi=e.layer; drawnItems.addLayer(roi);
 document.getElementById('selectBadge').classList.remove('show');
 updateSelection();
 openAreaModal();
});
function hav(a,b){const R=6371;const dLat=(b.lat-a.lat)*Math.PI/180,dLon=(b.lng-a.lng)*Math.PI/180;const x=Math.sin(dLat/2)**2+Math.cos(a.lat*Math.PI/180)*Math.cos(b.lat*Math.PI/180)*Math.sin(dLon/2)**2;return 2*R*Math.asin(Math.sqrt(x))}
function dimensions(bounds){const sw=bounds.getSouthWest(),ne=bounds.getNorthEast();const w=hav({lat:sw.lat,lng:sw.lng},{lat:sw.lat,lng:ne.lng});const h=hav({lat:sw.lat,lng:sw.lng},{lat:ne.lat,lng:sw.lng});return {w,h,area:w*h}}
function updateSelection(){if(!roi)return;const d=dimensions(roi.getBounds());document.getElementById('selectionInfo').classList.add('show');document.getElementById('selectionSize').textContent=d.area.toFixed(2)+' km²';document.getElementById('selectionDim').textContent=`${d.w.toFixed(2)} km × ${d.h.toFixed(2)} km`;}
function openAreaModal(){const d=dimensions(roi.getBounds());document.getElementById('widthInput').value=d.w.toFixed(2);document.getElementById('heightInput').value=d.h.toFixed(2);document.getElementById('areaModal').classList.add('show')}
document.getElementById('editArea').onclick=openAreaModal;
document.getElementById('cancelModal').onclick=()=>document.getElementById('areaModal').classList.remove('show');
document.getElementById('applyModal').onclick=()=>{
 if(!roi)return;
 const w=+document.getElementById('widthInput').value,h=+document.getElementById('heightInput').value,c=roi.getBounds().getCenter();
 const latDelta=(h/111.32)/2,lonDelta=(w/(111.32*Math.cos(c.lat*Math.PI/180)))/2;
 roi.setBounds([[c.lat-latDelta,c.lng-lonDelta],[c.lat+latDelta,c.lng+lonDelta]]);
 updateSelection();document.getElementById('areaModal').classList.remove('show');
};
document.getElementById('askArea').onclick=()=>{document.getElementById('chatPanel').classList.add('open');document.getElementById('composer').focus();};

document.getElementById('chatToggle').onclick=()=>document.getElementById('chatPanel').classList.toggle('open');
document.querySelectorAll('.scenario').forEach(b=>b.onclick=()=>{document.getElementById('composer').value=b.dataset.q;sendMessage()});
document.getElementById('send').onclick=sendMessage;
document.getElementById('composer').addEventListener('keydown',e=>{if(e.key==='Enter'&&!e.shiftKey){e.preventDefault();sendMessage()}});

function addMessage(type,text){const box=document.getElementById('messages'),m=document.createElement('div');m.className='msg '+type;m.innerHTML=`<div class="meta">${type==='user'?'USER_09':'GISGPT // CORE-V4'}</div><div class="bubble">${text}</div>`;box.appendChild(m);box.scrollTop=box.scrollHeight}
function scenarioFor(q){q=q.toLowerCase();if(q.includes('green')||q.includes('สีเขียว'))return 'green';if(q.includes('road')||q.includes('ถนน')||q.includes('เส้นทาง'))return 'roads';if(q.includes('water')||q.includes('น้ำ'))return 'water';if(q.includes('land')||q.includes('ใช้ประโยชน์'))return 'land';return 'buildings'}
function fakeAnalysis(kind){
 analysisLayer.clearLayers();if(!roi)return;
 const b=roi.getBounds(),sw=b.getSouthWest(),ne=b.getNorthEast(),latSpan=ne.lat-sw.lat,lonSpan=ne.lng-sw.lng;
 const polys=[];let count=kind==='buildings'?18:kind==='roads'?4:kind==='water'?2:kind==='green'?5:6;
 for(let i=0;i<count;i++){
   const x=(i*37%100)/100,y=(i*61%100)/100,w=(kind==='buildings'?.07:.18),h=(kind==='buildings'?.045:.12);
   const x2=Math.min(.95,x+w),y2=Math.min(.95,y+h);
   polys.push([[sw.lat+y*latSpan,sw.lng+x*lonSpan],[sw.lat+y2*latSpan,sw.lng+x2*lonSpan]]);
 }
 polys.forEach(p=>{
   L.rectangle(p,{color:'#fff',weight:1.5,dashArray:kind==='roads'?'2 5':'4 3',fillColor:'#fff',fillOpacity:.16,interactive:false}).addTo(analysisLayer)
 });
 document.getElementById('legend').classList.add('show');
}
function sendMessage(){
 const el=document.getElementById('composer'),q=el.value.trim();if(!q)return;
 addMessage('user',q);el.value='';
 if(!roi){setTimeout(()=>addMessage('assistant','เลือกพื้นที่บนแผนที่ก่อนครับ แล้วผมจะผูกคำถามเข้ากับ ROI ที่เลือก'),250);return}
 const kind=scenarioFor(q);setTimeout(()=>{
   fakeAnalysis(kind);const d=dimensions(roi.getBounds());
   const data={buildings:['BUILDINGS DETECTED','184','42,381 m²'],green:['GREEN SPACE','31.6%','0.76 km²'],roads:['ROAD NETWORK','12.4 km','18 segments'],water:['WATER FEATURES','2','0.18 km²'],land:['LAND USE CLASSES','5','classified']};
   const x=data[kind];
   addMessage('assistant',`Analysis complete. Highlight overlay updated on the map.<div class="assistant-card"><div class="metric"><span>ROI</span><span>${d.area.toFixed(2)} km²</span></div><div class="metric"><span>${x[0]}</span><span>${x[1]}</span></div><div class="metric"><span>MEASURE</span><span>${x[2]}</span></div></div>`);
 },500);
}

document.getElementById('searchInput').addEventListener('keydown',async e=>{
 if(e.key!=='Enter')return;const q=e.target.value.trim();if(!q)return;
 document.getElementById('systemText').textContent='SYS: SEARCHING // GEOCODING';
 try{
   const r=await fetch('https://nominatim.openstreetmap.org/search?format=jsonv2&limit=1&q='+encodeURIComponent(q),{headers:{'Accept-Language':'en'}});
   const a=await r.json();if(!a.length)throw new Error('not found');
   map.flyTo([+a[0].lat,+a[0].lon],15,{duration:1.2});
   addMessage('assistant',`Location found: <b>${a[0].display_name}</b><div class="assistant-card"><div class="metric"><span>LAT</span><span>${(+a[0].lat).toFixed(5)}</span></div><div class="metric"><span>LON</span><span>${(+a[0].lon).toFixed(5)}</span></div></div>`);
 }catch(err){addMessage('assistant','ไม่พบพื้นที่จากคำค้นนี้ ลองชื่อสถานที่หรือพิกัดอีกครั้ง');}
 document.getElementById('systemText').textContent='SYS: STABLE // SATELLITE MODE';
});
document.getElementById('connectBtn').onclick=function(){this.textContent=this.textContent==='CONNECT STREAM'?'STREAM CONNECTED':'CONNECT STREAM'};