// ✏️ ข้อความทั้งหมดของหน้า Landing อยู่ที่นี่ไฟล์เดียว — แก้แล้วเว็บเปลี่ยนทันที
export const site = {
  brand: 'GISGPT',

  nav: [
    { label: 'ความสามารถ', href: '#features' },
    { label: 'วิธีใช้งาน', href: '#how' },
    { label: 'เทคโนโลยี', href: '#tech' },
  ],

  hero: {
    badge: 'Geospatial Foundation Model Agent',
    title1: 'วิเคราะห์โลกจากดาวเทียม',
    title2: 'ด้วยการแชท',
    subtitle:
      'GISGPT รวมภาพถ่ายดาวเทียม GIS และ AI Foundation Model เข้าด้วยกัน — อัปโหลดภาพ GeoTIFF แล้วถามเป็นภาษาไทยหรืออังกฤษ รับคำตอบพร้อมแผนที่ผลลัพธ์และสถิติพื้นที่ทันที',
    ctaPrimary: 'เริ่มใช้งาน',
    ctaSecondary: 'ดูแดชบอร์ด',
    trust: 'ใช้ข้อมูล Sentinel-2 · Landsat/HLS · GISTDA Open Data',
  },

  featuresTitle: 'ความสามารถของระบบ',
  featuresSubtitle: 'ครบทุกขั้นตอนการวิเคราะห์ภาพดาวเทียม ตั้งแต่ไฟล์ดิบจนถึงผลลัพธ์ที่นำไปใช้ต่อได้',
  features: [
    {
      icon: '🛰️',
      name: 'จำแนก Land Cover',
      desc: 'แยกป่า แหล่งน้ำ เขตเมือง และพื้นที่เกษตร ทั้งฉากด้วยโมเดล Semantic Segmentation จาก Prithvi-EO-2.0',
    },
    {
      icon: '📊',
      name: 'ดัชนีสเปกตรัม',
      desc: 'คำนวณ NDVI, NDWI และ NDBI ทั่วทั้งภาพ เข้าใจสุขภาพพืช แหล่งน้ำ และการขยายตัวของเมือง',
    },
    {
      icon: '📐',
      name: 'สถิติพื้นที่',
      desc: 'สรุปเนื้อที่แต่ละคลาสเป็นเฮกตาร์และตารางกิโลเมตร พร้อม legend อัตโนมัติในทุกผลลัพธ์',
    },
    {
      icon: '🔥',
      name: 'Hotspots & ไฟป่า',
      desc: 'แผนที่จุดความร้อนจาก NASA FIRMS ซ้อนขอบเขตจังหวัด พร้อมจัดอันดับความรุนแรง (FRP)',
    },
    {
      icon: '🌫️',
      name: 'PM2.5 & อากาศ',
      desc: 'ดึงค่าฝุ่น PM2.5/PM10 จากสถานีวัดของ GISTDA ที่ใกล้พื้นที่สนใจที่สุด 5 สถานี',
    },
    {
      icon: '📤',
      name: 'Export ผลลัพธ์',
      desc: 'ดาวน์โหลด class map เป็น PNG หรือ GeoTIFF ไปใช้ต่อใน QGIS, ArcGIS ได้ทันที',
    },
  ],

  howTitle: 'ใช้งานง่ายแค่ 3 ขั้นตอน',
  howSteps: [
    {
      step: '01',
      name: 'อัปโหลดภาพ',
      desc: 'ลากไฟล์ GeoTIFF (Sentinel-2 / Landsat / HLS) มาวางในหน้าแชท — ไม่ต้องติดตั้งโปรแกรมใด ๆ',
    },
    {
      step: '02',
      name: 'พิมพ์คำสั่ง',
      desc: "สั่งงานเป็นภาษาธรรมชาติ เช่น “จำแนก land cover” หรือ “คำนวณ NDVI” ทั้งภาษาไทยและอังกฤษ",
    },
    {
      step: '03',
      name: 'รับผลลัพธ์',
      desc: 'แผนที่ผลลัพธ์ระบายสี + สถิติพื้นที่ + legend พร้อมดาวน์โหลดไฟล์ไปใช้ต่อได้เลย',
    },
  ],

  stats: [
    { value: '330M', label: 'พารามิเตอร์ของโมเดล Prithvi' },
    { value: '6', label: 'แบนด์ Sentinel-2/HLS (B02–B07)' },
    { value: '10', label: 'คลาส land cover จาก Sen4Map' },
    { value: '2', label: 'ภาษา — ไทยและอังกฤษ' },
  ],

  techTitle: 'เทคโนโลยีที่ใช้',
  techItems: [
    'Prithvi-EO-2.0 (NASA–IBM)',
    'Sentinel-2 · Landsat/HLS',
    'GISTDA Open Data',
    'NASA FIRMS',
    'ONNX Runtime (CPU)',
    'Flask + Python Agent',
    'OpenLayers Web GIS',
  ],

  ctaBanner: {
    title: 'พร้อมสำรวจโลกจากมุมสูงหรือยัง?',
    subtitle: 'เริ่มแชทกับ GISGPT ได้เลย ไม่ต้องสมัครสมาชิก ไม่ต้องติดตั้งอะไร',
    button: 'เริ่มใช้งาน',
  },

  footer: {
    tagline: 'Satellite Imagery + GIS + AI Foundation Model',
    appLinks: [
      { label: 'หน้าแชท', href: '/chat' },
      { label: 'แดชบอร์ด', href: '/dashboard' },
      { label: 'Hotspots', href: '/hotspots' },
    ],
    dataLinks: [
      { label: 'GISTDA NSDC', href: 'https://nsdc.gistda.or.th' },
      { label: 'Copernicus Data Space', href: 'https://dataspace.copernicus.eu' },
      { label: 'NASA FIRMS', href: 'https://firms.modaps.eosdis.nasa.gov' },
    ],
    credit: 'ข้อมูลภูมิสารสนเทศจาก GISTDA, Copernicus และ NASA',
  },
}
