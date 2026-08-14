const GISGPT = window.GISGPT = {};

GISGPT.GISTDA_KEY = ''; // สมัครฟรีที่ https://api-gateway.gistda.or.th เพื่อเปิดเลเยอร์ภาพดาวเทียม 2 เมตร

GISGPT.BASEMAPS = {
  osm: {
    name: 'STREET',
    url: 'https://{a-c}.tile.openstreetmap.org/{z}/{x}/{y}.png',
    attr: '© OpenStreetMap contributors'
  },
  esri: {
    name: 'ESRI SAT',
    url: 'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
    attr: 'Tiles © Esri'
  },
  gistda: {
    name: 'GISTDA 2M',
    url: GISGPT.GISTDA_KEY ? 'https://api-gateway.gistda.or.th/api/2.0/resources/tiles/gi-basemap_68/{z}/{x}/{y}.png?api_key=' + GISGPT.GISTDA_KEY : null,
    attr: '© GISTDA'
  }
};

GISGPT.PALETTE = ['#ffd166', '#06d6a0', '#4cc9f0', '#ef476f', '#a78bfa', '#f9a826', '#2ec4b6', '#e76f51', '#8d99ae', '#f4a261'];

GISGPT.SAMPLE = {
  type: 'FeatureCollection',
  features: [
    { type: 'Feature', properties: { name: 'อาคารสำนักงาน A', type: 'building', floors: 12 }, geometry: { type: 'Polygon', coordinates: [[[100.5000, 13.7240], [100.5012, 13.7240], [100.5012, 13.7249], [100.5000, 13.7249], [100.5000, 13.7240]]] } },
    { type: 'Feature', properties: { name: 'อาคารพาณิชย์ B', type: 'building', floors: 4 }, geometry: { type: 'Polygon', coordinates: [[[100.5018, 13.7236], [100.5027, 13.7236], [100.5027, 13.7242], [100.5018, 13.7242], [100.5018, 13.7236]]] } },
    { type: 'Feature', properties: { name: 'บ้านพักอาศัย C', type: 'building', floors: 2 }, geometry: { type: 'Polygon', coordinates: [[[100.5006, 13.7253], [100.5011, 13.7253], [100.5011, 13.7257], [100.5006, 13.7257], [100.5006, 13.7253]]] } },
    { type: 'Feature', properties: { name: 'ศูนย์การค้า D', type: 'building', floors: 5 }, geometry: { type: 'Polygon', coordinates: [[[100.5029, 13.7248], [100.5040, 13.7248], [100.5040, 13.7255], [100.5029, 13.7255], [100.5029, 13.7248]]] } },
    { type: 'Feature', properties: { name: 'ถนนสายหลัก 1', type: 'road', lanes: 6 }, geometry: { type: 'LineString', coordinates: [[100.4992, 13.7262], [100.5018, 13.7261], [100.5043, 13.7259]] } },
    { type: 'Feature', properties: { name: 'ถนนสายรอง 2', type: 'road', lanes: 2 }, geometry: { type: 'LineString', coordinates: [[100.5020, 13.7230], [100.5022, 13.7246], [100.5024, 13.7260]] } },
    { type: 'Feature', properties: { name: 'สวนสาธารณะ', type: 'park', area_ha: 3.2 }, geometry: { type: 'Polygon', coordinates: [[[100.5008, 13.7270], [100.5026, 13.7270], [100.5026, 13.7284], [100.5008, 13.7284], [100.5008, 13.7270]]] } },
    { type: 'Feature', properties: { name: 'บึงน้ำ', type: 'water', area_ha: 1.1 }, geometry: { type: 'Polygon', coordinates: [[[100.4994, 13.7236], [100.5000, 13.7236], [100.5000, 13.7242], [100.4994, 13.7242], [100.4994, 13.7236]]] } },
    { type: 'Feature', properties: { name: 'ป้ายรถเมล์', type: 'poi', amenity: 'bus_stop' }, geometry: { type: 'Point', coordinates: [100.5013, 13.7258] } },
    { type: 'Feature', properties: { name: 'โรงพยาบาล', type: 'poi', amenity: 'hospital' }, geometry: { type: 'Point', coordinates: [100.5033, 13.7266] } },
    { type: 'Feature', properties: { name: 'โรงเรียน', type: 'poi', amenity: 'school' }, geometry: { type: 'Point', coordinates: [100.4998, 13.7258] } }
  ]
};
