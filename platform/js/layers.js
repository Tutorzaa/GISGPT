GISGPT.vectorLayers = [];
GISGPT.activeLayerId = null;

GISGPT.layerStyle = function (color) {
  return function (feature) {
    const g = feature.getGeometry();
    if (g instanceof ol.geom.Point || g instanceof ol.geom.MultiPoint) {
      return new ol.style.Style({
        image: new ol.style.Circle({
          radius: 5,
          fill: new ol.style.Fill({ color: color }),
          stroke: new ol.style.Stroke({ color: '#fff', width: 1 })
        })
      });
    }
    if (g instanceof ol.geom.LineString || g instanceof ol.geom.MultiLineString) {
      return new ol.style.Style({
        stroke: new ol.style.Stroke({ color: color, width: 3 })
      });
    }
    return new ol.style.Style({
      stroke: new ol.style.Stroke({ color: '#fff', width: 1.2 }),
      fill: new ol.style.Fill({ color: color, opacity: 0.45 })
    });
  };
};

GISGPT.addVectorLayer = function (name, geojson, opts) {
  opts = opts || {};
  let features;
  try {
    features = new ol.format.GeoJSON().readFeatures(geojson, {
      featureProjection: 'EPSG:3857'
    });
  } catch (e) {
    GISGPT.toast('ไฟล์ข้อมูลไม่ถูกต้อง: ' + e.message, true);
    return null;
  }
  if (!features.length) {
    GISGPT.toast('ไม่พบ feature ในไฟล์นี้', true);
    return null;
  }
  features.forEach(function (f, i) { f.setId('f' + i); });
  const id = 'L' + Date.now();
  const source = new ol.source.Vector({ features: features });
  const color = GISGPT.PALETTE[GISGPT.vectorLayers.length % GISGPT.PALETTE.length];
  const olLayer = new ol.layer.Vector({
    source: source,
    style: GISGPT.layerStyle(color),
    zIndex: 10 + GISGPT.vectorLayers.length
  });
  const rec = { id: id, name: name, olLayer: olLayer, color: color, source: source };
  GISGPT.vectorLayers.push(rec);
  GISGPT.map.addLayer(olLayer);
  GISGPT.renderLayerPanel();
  GISGPT.updateStatus();
  GISGPT.toast('นำเข้า "' + name + '" สำเร็จ — ' + features.length + ' features');
  if (opts.fit !== false) {
    GISGPT.map.getView().fit(source.getExtent(), { padding: [80, 80, 80, 80], maxZoom: 17 });
  }
  return rec;
};

GISGPT.rebuildLayerOrder = function () {
  const layers = GISGPT.map.getLayers();
  layers.clear();
  layers.push(GISGPT.basemapLayer);
  GISGPT.vectorLayers.forEach(function (r, i) {
    r.olLayer.setZIndex(10 + i);
    layers.push(r.olLayer);
  });
  layers.push(GISGPT.selectionLayer);
};

GISGPT.removeVectorLayer = function (id) {
  const idx = GISGPT.vectorLayers.findIndex(function (r) { return r.id === id; });
  if (idx < 0) return;
  const rec = GISGPT.vectorLayers[idx];
  GISGPT.map.removeLayer(rec.olLayer);
  GISGPT.vectorLayers.splice(idx, 1);
  if (GISGPT.activeLayerId === id) {
    GISGPT.activeLayerId = null;
    GISGPT.closeTable();
  }
  GISGPT.renderLayerPanel();
  GISGPT.updateStatus();
};

GISGPT.moveLayer = function (id, dir) {
  const idx = GISGPT.vectorLayers.findIndex(function (r) { return r.id === id; });
  const to = idx + dir;
  if (idx < 0 || to < 0 || to >= GISGPT.vectorLayers.length) return;
  const rec = GISGPT.vectorLayers.splice(idx, 1)[0];
  GISGPT.vectorLayers.splice(to, 0, rec);
  GISGPT.rebuildLayerOrder();
  GISGPT.renderLayerPanel();
};

GISGPT.zoomToLayer = function (id) {
  const rec = GISGPT.vectorLayers.find(function (r) { return r.id === id; });
  if (!rec) return;
  GISGPT.map.getView().fit(rec.source.getExtent(), { padding: [80, 80, 80, 80], maxZoom: 17 });
};

GISGPT.highlightFeature = function (rec, fid) {
  GISGPT.selectionLayer.getSource().clear();
  if (fid === null || fid === undefined) return;
  const f = rec.source.getFeatureById(fid);
  if (f) GISGPT.selectionLayer.getSource().addFeature(f);
};

GISGPT.renderLayerPanel = function () {
  const list = document.getElementById('layerList');
  document.getElementById('layerCount').textContent = String(GISGPT.vectorLayers.length);
  if (!GISGPT.vectorLayers.length) {
    list.innerHTML = '<div class="empty">ไม่มีชั้นข้อมูล — กด LOAD SAMPLE หรือนำเข้าไฟล์ด้านบน</div>';
    return;
  }
  list.innerHTML = '';
  GISGPT.vectorLayers.slice().reverse().forEach(function (rec) {
    const row = document.createElement('div');
    row.className = 'layer-row' + (rec.id === GISGPT.activeLayerId ? ' active' : '');
    row.innerHTML =
      '<div class="lr-head">' +
      '<span style="width:9px;height:9px;background:' + rec.color + ';border-radius:2px;flex-shrink:0"></span>' +
      '<span class="lr-name" title="' + rec.name + '">' + rec.name + '</span>' +
      '<span class="lr-count">' + rec.source.getFeatures().length + '</span>' +
      '</div>' +
      '<div class="lr-controls">' +
      '<input type="checkbox" class="checkbox" title="แสดง/ซ่อน" checked>' +
      '<div class="lr-op"><input type="range" min="0" max="100" value="100" title="ความโปร่งใส"><span>100%</span></div>' +
      '<button class="btn" data-act="table" title="ตาราง attribute">T</button>' +
      '<button class="btn" data-act="zoom" title="ซูมเข้าชั้น">⌖</button>' +
      '<button class="btn" data-act="up" title="ย้ายขึ้น">↑</button>' +
      '<button class="btn" data-act="down" title="ย้ายลง">↓</button>' +
      '<button class="btn" data-act="del" title="ลบชั้น">×</button>' +
      '</div>';
    row.querySelector('.checkbox').onchange = function (e) {
      rec.olLayer.setVisible(e.target.checked);
    };
    row.querySelector('input[type=range]').oninput = function (e) {
      rec.olLayer.setOpacity(Number(e.target.value) / 100);
      row.querySelector('.lr-op span').textContent = e.target.value + '%';
    };
    row.querySelectorAll('[data-act]').forEach(function (b) {
      b.onclick = function () {
        const act = b.dataset.act;
        if (act === 'table') GISGPT.openTable(rec.id);
        else if (act === 'zoom') GISGPT.zoomToLayer(rec.id);
        else if (act === 'up') GISGPT.moveLayer(rec.id, 1);
        else if (act === 'down') GISGPT.moveLayer(rec.id, -1);
        else if (act === 'del') GISGPT.removeVectorLayer(rec.id);
      };
    });
    list.appendChild(row);
  });
};

GISGPT.updateStatus = function () {
  const total = GISGPT.vectorLayers.reduce(function (s, r) { return s + r.source.getFeatures().length; }, 0);
  document.getElementById('stFeatures').textContent = total + ' features / ' + GISGPT.vectorLayers.length + ' layers';
};
