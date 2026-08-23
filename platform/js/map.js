GISGPT.createMap = function () {
  const view = new ol.View({
    center: ol.proj.fromLonLat([100.5015, 13.7252]),
    zoom: 15
  });

  GISGPT.map = new ol.Map({
    target: 'map',
    layers: [],
    view: view
  });

  GISGPT.basemapLayer = new ol.layer.Tile({
    source: GISGPT.basemapSource('osm')
  });
  GISGPT.map.addLayer(GISGPT.basemapLayer);

  GISGPT.selectionLayer = new ol.layer.Vector({
    source: new ol.source.Vector(),
    style: new ol.style.Style({
      stroke: new ol.style.Stroke({ color: '#ffd166', width: 3 }),
      fill: new ol.style.Fill({ color: 'rgba(255,209,102,0.18)' }),
      image: new ol.style.Circle({ radius: 6, fill: new ol.style.Fill({ color: '#ffd166' }) })
    })
  });
  GISGPT.map.addLayer(GISGPT.selectionLayer);

  GISGPT.popup = new ol.Overlay({
    element: document.getElementById('popup'),
    positioning: 'bottom-center',
    offset: [0, -12],
    autoPan: { animation: { duration: 250 } }
  });
  GISGPT.map.addOverlay(GISGPT.popup);

  GISGPT.map.on('pointermove', function (e) {
    if (e.dragging) return;
    const c = ol.proj.toLonLat(e.coordinate);
    document.getElementById('stCoord').textContent =
      'LON ' + c[0].toFixed(5) + ' | LAT ' + c[1].toFixed(5);
  });
  GISGPT.map.on('moveend', function () {
    document.getElementById('stZoom').textContent = 'Z ' + GISGPT.map.getView().getZoom().toFixed(1);
  });
};

GISGPT.basemapSource = function (id) {
  const bm = GISGPT.BASEMAPS[id];
  if (!bm || !bm.url) return null;
  return new ol.source.XYZ({
    url: bm.url,
    attributions: bm.attr,
    maxZoom: 19,
    crossOrigin: 'anonymous'
  });
};

GISGPT.setBasemap = function (id) {
  const src = GISGPT.basemapSource(id);
  if (!src) {
    GISGPT.toast('Basemap นี้ต้องใส่ GISTDA_KEY ใน js/config.js ก่อน', true);
    return false;
  }
  GISGPT.basemapLayer.setSource(src);
  document.querySelectorAll('.bm').forEach(function (b) {
    b.classList.toggle('active', b.dataset.bm === id);
  });
  return true;
};

GISGPT.showPopup = function (feature, layerName) {
  const props = feature.getProperties();
  const rows = Object.keys(props)
    .filter(function (k) { return k !== 'geometry' && props[k] !== undefined && props[k] !== null; })
    .slice(0, 8);
  const html = rows.map(function (k) {
    return '<tr><td>' + k + '</td><td>' + String(props[k]) + '</td></tr>';
  }).join('');
  const el = document.getElementById('popup');
  el.innerHTML = '<button class="p-close" id="pClose">✕</button><h4>' +
    (layerName || 'FEATURE') + '</h4><table>' + html + '</table>';
  el.style.display = 'block';
  document.getElementById('pClose').onclick = function () { GISGPT.hidePopup(); };
  const extent = feature.getGeometry().getExtent();
  GISGPT.popup.setPosition(ol.extent.getCenter(extent));
};

GISGPT.hidePopup = function () {
  document.getElementById('popup').style.display = 'none';
  GISGPT.popup.setPosition(undefined);
};
