/* GISGPT chat UI — โต้ตอบกับ /api/chat และ /api/upload */
const chatEl = document.getElementById('chat');
const inputEl = document.getElementById('message');
const sendBtn = document.getElementById('send');
const dropZone = document.getElementById('drop-zone');
const fileInput = document.getElementById('file-input');
const fileHint = document.getElementById('file-hint');
const statusDot = document.getElementById('status-dot');

function esc(s) {
  return s.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
}

function addMsg(role, text) {
  const div = document.createElement('div');
  div.className = 'msg ' + role;
  div.textContent = text;
  chatEl.appendChild(div);
  chatEl.scrollTop = chatEl.scrollHeight;
  return div;
}

function addArtifacts(artifacts) {
  if (!artifacts || !artifacts.length) return;
  const wrap = document.createElement('div');
  wrap.className = 'artifacts';
  artifacts.forEach(a => {
    const el = document.createElement('div');
    el.className = 'artifact';
    if (a.type === 'image') {
      el.innerHTML = `<img src="${esc(a.url)}" alt=""><div class="cap">${esc(a.caption || '')}</div>`;
    } else if (a.type === 'download') {
      el.innerHTML = `<a href="${esc(a.url)}" download>⬇️ ${esc(a.caption || 'ดาวน์โหลด')}</a>`;
    }
    wrap.appendChild(el);
  });
  chatEl.appendChild(wrap);
  chatEl.scrollTop = chatEl.scrollHeight;
}

function addLegend(legend) {
  if (!legend || !legend.length) return;
  const wrap = document.createElement('div');
  wrap.className = 'legend';
  legend.forEach(c => {
    const chip = document.createElement('span');
    chip.className = 'chip';
    chip.innerHTML = `<span class="sw" style="background:${esc(c.color)}"></span> ${esc(c.th)} (${esc(c.en)})`;
    wrap.appendChild(chip);
  });
  chatEl.appendChild(wrap);
  chatEl.scrollTop = chatEl.scrollHeight;
}

function setBusy(b) {
  statusDot.className = 'dot' + (b ? ' busy' : '');
  sendBtn.disabled = b;
}

async function send() {
  const text = inputEl.value.trim();
  if (!text) return;
  inputEl.value = '';
  addMsg('user', text);
  setBusy(true);
  const typing = addMsg('bot', '⏳ กำลังประมวลผล...');
  try {
    const r = await fetch('/api/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message: text }),
    });
    const data = await r.json();
    typing.textContent = data.reply || '(ไม่มีคำตอบ)';
    addArtifacts(data.artifacts);
    addLegend(data.legend);
  } catch (e) {
    typing.textContent = '⚠️ เกิดข้อผิดพลาด: ' + e.message;
  } finally {
    setBusy(false);
    chatEl.scrollTop = chatEl.scrollHeight;
  }
}

async function uploadFile(file) {
  const fd = new FormData();
  fd.append('file', file);
  setBusy(true);
  fileHint.textContent = '⏳ กำลังอัปโหลด...';
  try {
    const r = await fetch('/api/upload', { method: 'POST', body: fd });
    const info = await r.json();
    if (r.ok) {
      fileHint.textContent = `✅ อัปโหลดแล้ว: ${info.name} (${info.bands} แบนด์, ${info.width}×${info.height} px)`;
      dropZone.classList.add('ok');
      addMsg('bot', `📥 ได้รับภาพ **${info.name}** แล้ว (${info.bands} แบนด์ · CRS ${info.crs})\nลองสั่ง "จำแนก land cover" ได้เลย`);
    } else {
      fileHint.textContent = '❌ ' + (info.error || 'อัปโหลดไม่สำเร็จ');
    }
  } catch (e) {
    fileHint.textContent = '❌ อัปโหลดผิดพลาด: ' + e.message;
  } finally {
    setBusy(false);
  }
}

sendBtn.addEventListener('click', send);
inputEl.addEventListener('keydown', e => { if (e.key === 'Enter') send(); });

dropZone.addEventListener('click', () => fileInput.click());
dropZone.addEventListener('dragover', e => { e.preventDefault(); dropZone.classList.add('drag'); });
dropZone.addEventListener('dragleave', () => dropZone.classList.remove('drag'));
dropZone.addEventListener('drop', e => {
  e.preventDefault();
  dropZone.classList.remove('drag');
  const f = e.dataTransfer.files[0];
  if (f) uploadFile(f);
});
fileInput.addEventListener('change', () => {
  if (fileInput.files[0]) uploadFile(fileInput.files[0]);
  fileInput.value = '';
});

// เปิดแชทด้วยข้อความต้อนรับ
addMsg('bot', 'สวัสดี! ผม GISGPT 🌍\nอัปโหลดภาพดาวเทียม (GeoTIFF) แล้วถามได้เลย เช่น "จำแนก land cover" หรือพิมพ์ "ช่วยด้วย"');
