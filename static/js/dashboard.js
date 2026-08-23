/* GISGPT Fire Emissions Watch — dashboard logic */
const map = L.map('map').setView([15.0, 103.0], 8);
L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
  maxZoom: 18, attribution: '© OpenStreetMap'
}).addTo(map);

let fireLayer = L.layerGroup().addTo(map);
let boundaryLayer = L.layerGroup().addTo(map);
const dailyChart = echarts.init(document.getElementById('chart-daily'));
const provChart = echarts.init(document.getElementById('chart-province'));

const $ = id => document.getElementById(id);

function fireColor(frp) {
  // เขียว(อ่อน) → เหลือง → แดง(แรง) ตาม FRP
  const t = Math.min(1, frp / 30);
  return `hsl(${Math.round(40 - 40 * t)}, 100%, ${Math.round(50 - 10 * t)}%)`;
}

function setBusy(b) {
  $('loading').className = b ? '' : 'loading-hidden';
  $('apply').disabled = b;
}

async function loadDashboard() {
  setBusy(true);
  const q = new URLSearchParams({
    province: $('province').value,
    start: $('start').value,
    end: $('end').value,
  });
  try {
    const r = await fetch('/api/dashboard?' + q);
    const d = await r.json();
    if (d.error) { alert(d.error); return; }
    render(d);
  } catch (e) {
    alert('โหลดล้มเหลว: ' + e.message);
  } finally {
    setBusy(false);
  }
}

function render(d) {
  // สถิติ
  $('st-hot').textContent = d.summary.total_hotspots;
  $('st-frp').textContent = d.summary.total_frp;
  $('st-days').textContent = d.summary.active_days;
  $('st-peak').textContent = d.summary.peak_day ? d.summary.peak_day.slice(5) : '–';

  // ขอบเขตจังหวัด
  boundaryLayer.clearLayers();
  L.geoJSON(d.boundary, { style: { color: '#4ecdc4', weight: 2, fillOpacity: 0.05 } }).addTo(boundaryLayer);

  // จุดไฟ
  fireLayer.clearLayers();
  d.points.forEach(p => {
    L.circleMarker([p.lat, p.lon], {
      radius: 3 + Math.min(5, p.frp / 8),
      color: '#fff', weight: 0.5,
      fillColor: fireColor(p.frp), fillOpacity: 0.85,
    }).addTo(fireLayer).bindPopup(
      `FRP ${p.frp}<br>${p.datetime}<br>${p.satellite || ''}`
    );
  });

  // กราฟรายวัน (bar = จำนวนจุด, line = FRP)
  dailyChart.setOption({
    backgroundColor: 'transparent',
    grid: { left: 40, right: 40, top: 20, bottom: 24 },
    tooltip: { trigger: 'axis' },
    legend: { data: ['FRP', 'จำนวนจุด'], textStyle: { color: '#8fb6bd' }, top: 0 },
    xAxis: { type: 'category', data: d.daily.map(x => x.date.slice(5)), axisLabel: { color: '#8fb6bd', fontSize: 10 } },
    yAxis: [
      { type: 'value', name: 'FRP', axisLabel: { color: '#8fb6bd' }, splitLine: { lineStyle: { color: '#1d5c69' } } },
      { type: 'value', name: 'จุด', axisLabel: { color: '#8fb6bd' }, splitLine: { show: false } },
    ],
    series: [
      { name: 'FRP', type: 'line', smooth: true, data: d.daily.map(x => x.sum_frp), itemStyle: { color: '#ff9f43' }, areaStyle: { color: 'rgba(255,159,67,.15)' } },
      { name: 'จำนวนจุด', type: 'bar', yAxisIndex: 1, data: d.daily.map(x => x.count), itemStyle: { color: '#4ecdc4' } },
    ],
  });

  // กราฟแยกจังหวัด (top 10)
  const top = d.by_province.slice(0, 10);
  provChart.setOption({
    backgroundColor: 'transparent',
    grid: { left: 90, right: 20, top: 10, bottom: 24 },
    tooltip: { trigger: 'axis' },
    xAxis: { type: 'value', axisLabel: { color: '#8fb6bd' }, splitLine: { lineStyle: { color: '#1d5c69' } } },
    yAxis: { type: 'category', data: top.map(x => x.province).reverse(), axisLabel: { color: '#8fb6bd', fontSize: 10 } },
    series: [{ type: 'bar', data: top.map(x => x.sum_frp).reverse(), itemStyle: { color: '#ff5e3a' } }],
  });

  map.fitBounds(L.geoJSON(d.boundary).getBounds(), { padding: [20, 20] });
}

// ----- แชท AI agent -----
function chatToggle() {
  const c = $('chat');
  c.classList.toggle('chat-closed');
  if (!c.classList.contains('chat-closed')) {
    $('chat-log').scrollTop = $('chat-log').scrollHeight;
  }
}

function chatAdd(role, text) {
  const div = document.createElement('div');
  div.className = 'msg ' + role;
  div.textContent = text;
  $('chat-log').appendChild(div);
  $('chat-log').scrollTop = $('chat-log').scrollHeight;
  return div;
}

async function chatSend() {
  const inp = $('chat-msg');
  const text = inp.value.trim();
  if (!text) return;
  inp.value = '';
  chatAdd('user', text);
  const typing = chatAdd('bot', '⏳ ...');
  try {
    const r = await fetch('/api/chat', {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message: text }),
    });
    const d = await r.json();
    typing.textContent = d.reply || '(ไม่มีคำตอบ)';
  } catch (e) {
    typing.textContent = '⚠️ ' + e.message;
  }
}

$('apply').addEventListener('click', loadDashboard);
$('chat-toggle').addEventListener('click', chatToggle);
$('chat-send').addEventListener('click', chatSend);
$('chat-msg').addEventListener('keydown', e => { if (e.key === 'Enter') chatSend(); });

chatAdd('bot', 'สวัสดี! ผม GISGPT Agent 🤖\nถามผมได้ เช่น "จุดไหนเผาเยอะสุด" หรือ "สรุปสถานการณ์ไฟ"');
loadDashboard();
