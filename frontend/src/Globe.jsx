import { useEffect, useRef } from 'react'
import createGlobe from 'cobe'

// ลูกโลก 3D จุดแสง (cobe) — หมุนช้าๆ พื้นหลังโปร่ง
export default function Globe({ className = '' }) {
  const canvasRef = useRef(null)

  useEffect(() => {
    const canvas = canvasRef.current
    if (!canvas) return
    const reduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches

    const globe = createGlobe(canvas, {
      devicePixelRatio: Math.min(window.devicePixelRatio || 1, 2),
      width: canvas.offsetWidth * 2,
      height: canvas.offsetHeight * 2,
      phi: 4.6,
      theta: 0.23,
      dark: 1,
      diffuse: 1.35,
      mapSamples: 17000,
      mapBrightness: 6.2,
      baseColor: [0.16, 0.21, 0.34],
      markerColor: [0.31, 0.55, 1],
      glowColor: [0.13, 0.24, 0.44],
      opacity: 0.95,
      markers: [
        { location: [13.7563, 100.5018], size: 0.085 }, // กรุงเทพฯ
        { location: [14.5236, 103.0744], size: 0.06 }, // บุรีรัมย์
      ],
      onRender: state => {
        if (!reduced) state.phi += 0.0022
        state.width = canvas.offsetWidth * 2
        state.height = canvas.offsetHeight * 2
      },
    })

    return () => globe.destroy()
  }, [])

  return <canvas ref={canvasRef} className={className} aria-hidden="true" />
}
