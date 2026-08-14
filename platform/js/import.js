GISGPT.importHandlers = {
  geo: function (file) {
    return new Promise(function (resolve, reject) {
      const reader = new FileReader();
      reader.onload = function () {
        try {
          resolve(JSON.parse(String(reader.result)));
        } catch (e) { reject(new Error('GeoJSON ไม่ถูกต้อง: ' + e.message)); }
      };
      reader.onerror = function () { reject(new Error('อ่านไฟล์ไม่ได้')); };
      reader.readAsText(file);
    });
  },
  shp: function (file) {
    const isZip = file.name.toLowerCase().endsWith('.zip');
    if (isZip) {
      return window.shp(file).then(function (geojson) {
        if (!geojson) throw new Error('ไม่พบข้อมูลใน ZIP');
        return geojson;
      });
    }
    return file.arrayBuffer().then(function (buf) {
      return window.shp(buf);
    });
  },
  kml: function (file) {
    return new Promise(function (resolve, reject) {
      const reader = new FileReader();
      reader.onload = function () {
        try {
          const doc = new DOMParser().parseFromString(String(reader.result), 'text/xml');
          const isKml = file.name.toLowerCase().endsWith('.kml');
          const geojson = isKml ? window.togeojson.kml(doc) : window.togeojson.gpx(doc);
          resolve(geojson);
        } catch (e) { reject(new Error('KML/GPX ไม่ถูกต้อง: ' + e.message)); }
      };
      reader.onerror = function () { reject(new Error('อ่านไฟล์ไม่ได้')); };
      reader.readAsText(file);
    });
  }
};

GISGPT.importFile = function (kind, file) {
  if (!file) return;
  GISGPT.importHandlers[kind](file).then(function (geojson) {
    const name = file.name.replace(/\.[^.]+$/, '');
    const rec = GISGPT.addVectorLayer(name, geojson);
    if (rec) GISGPT.openTable(rec.id);
  }).catch(function (err) {
    GISGPT.toast('นำเข้าไม่สำเร็จ: ' + err.message, true);
  });
};

GISGPT.loadSample = function () {
  GISGPT.addVectorLayer('sample-bangkok', GISGPT.SAMPLE);
};