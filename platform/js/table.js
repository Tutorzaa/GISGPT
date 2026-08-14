GISGPT.openTable = function (layerId) {
  const rec = GISGPT.vectorLayers.find(function (r) { return r.id === layerId; });
  if (!rec) return;
  GISGPT.activeLayerId = layerId;
  GISGPT.renderLayerPanel();
  const features = rec.source.getFeatures();
  const keys = {};
  features.forEach(function (f) {
    Object.keys(f.getProperties()).forEach(function (k) {
      if (k !== 'geometry') keys[k] = (keys[k] || 0) + 1;
    });
  });
  const cols = Object.keys(keys)
    .filter(function (k) { return keys[k] > features.length * 0.4; })
    .slice(0, 8);
  rec._tableCols = cols;

  document.getElementById('tableTitle').textContent = 'ATTRIBUTE TABLE — ' + rec.name.toUpperCase();
  document.getElementById('tableCount').textContent = features.length + ' features';
  const panel = document.getElementById('tablePanel');
  panel.classList.add('open');
  GISGPT.renderTable(rec, '');
};

GISGPT.renderTable = function (rec, filter) {
  const thead = document.querySelector('#table thead');
  const tbody = document.querySelector('#table tbody');
  const cols = rec._tableCols || [];
  thead.innerHTML = '<tr><th>#</th>' + cols.map(function (c) { return '<th>' + c + '</th>'; }).join('') + '</tr>';
  const features = rec.source.getFeatures();
  const q = filter.toLowerCase();
  let shown = 0;
  tbody.innerHTML = '';
  features.forEach(function (f, i) {
    const props = f.getProperties();
    const hay = cols.map(function (c) { return String(props[c] === undefined ? '' : props[c]); }).join(' ').toLowerCase();
    if (q && hay.indexOf(q) < 0) return;
    shown++;
    const tr = document.createElement('tr');
    tr.dataset.fid = String(f.getId());
    tr.innerHTML = '<td>' + (i + 1) + '</td>' +
      cols.map(function (c) {
        const v = props[c];
        return '<td title="' + String(v === undefined ? '' : v) + '">' + (v === undefined ? '' : v) + '</td>';
      }).join('');
    tr.onclick = function () {
      document.querySelectorAll('#table tbody tr').forEach(function (r) { r.classList.remove('sel'); });
      tr.classList.add('sel');
      GISGPT.highlightFeature(rec, f.getId());
      const center = ol.extent.getCenter(f.getGeometry().getExtent());
      GISGPT.map.getView().animate({ center: center, duration: 300 });
    };
    tbody.appendChild(tr);
  });
  document.getElementById('tableCount').textContent = shown + ' / ' + features.length + ' features';
};

GISGPT.closeTable = function () {
  document.getElementById('tablePanel').classList.remove('open');
  document.getElementById('tableSearch').value = '';
  GISGPT.activeLayerId = null;
  GISGPT.selectionLayer.getSource().clear();
  GISGPT.renderLayerPanel();
};

GISGPT.setTableFilter = function (q) {
  const rec = GISGPT.vectorLayers.find(function (r) { return r.id === GISGPT.activeLayerId; });
  if (rec) GISGPT.renderTable(rec, q);
};