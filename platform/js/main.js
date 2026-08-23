GISGPT.toast = function (msg, isError) {
  const el = document.getElementById('toast');
  el.textContent = msg;
  el.className = 'toast show' + (isError ? ' err' : '');
  clearTimeout(el._t);
  el._t = setTimeout(function () { el.className = 'toast'; }, 3500);
};

GISGPT.setupIdentify = function () {
  GISGPT.map.on('singleclick', function (e) {
    let hit = null;
    GISGPT.map.forEachFeatureAtPixel(e.pixel, function (f, l) {
      if (l === GISGPT.selectionLayer || l === GISGPT.basemapLayer) return true;
      hit = { f: f, l: l };
      return true;
    }, { hitTolerance: 6 });
    if (!hit) {
      GISGPT.hidePopup();
      return;
    }
    const rec = GISGPT.vectorLayers.find(function (r) { return r.olLayer === hit.l; });
    const fid = hit.f.getId();
    GISGPT.highlightFeature(rec, fid);
    GISGPT.showPopup(hit.f, rec ? rec.name : 'FEATURE');
  });
};

window.addEventListener('load', function () {
  GISGPT.createMap();
  GISGPT.setupIdentify();

  document.getElementById('btnSample').onclick = function () { GISGPT.loadSample(); };
  document.getElementById('btnGeo').onclick = function () { document.getElementById('fileGeo').click(); };
  document.getElementById('btnShp').onclick = function () { document.getElementById('fileShp').click(); };
  document.getElementById('btnKml').onclick = function () { document.getElementById('fileKml').click(); };
  document.getElementById('fileGeo').onchange = function (e) { GISGPT.importFile('geo', e.target.files[0]); e.target.value = ''; };
  document.getElementById('fileShp').onchange = function (e) { GISGPT.importFile('shp', e.target.files[0]); e.target.value = ''; };
  document.getElementById('fileKml').onchange = function (e) { GISGPT.importFile('kml', e.target.files[0]); e.target.value = ''; };
  document.getElementById('tableSearch').oninput = function (e) { GISGPT.setTableFilter(e.target.value.trim()); };
  document.getElementById('tableClose').onclick = function () { GISGPT.closeTable(); };
  document.querySelectorAll('.bm').forEach(function (b) {
    b.onclick = function () { GISGPT.setBasemap(b.dataset.bm); };
  });

  GISGPT.loadSample();
  GISGPT.toast('GISGPT GIS Platform พร้อมใช้งาน');
});

window.onerror = function (msg, src, line) {
  GISGPT.toast('JS error: ' + msg + ' (line ' + line + ')', true);
};