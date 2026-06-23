import { useRef, useEffect } from 'react'
import { useJarvis } from '../context/JarvisContext'

const N = 150
const GOLDEN_RATIO = (1 + Math.sqrt(5)) / 2
const LINE_DIST_SQ = 0.15  // squared distance threshold on unit sphere

// Fibonacci lattice — fixed at module load
const BASE_POINTS = Array.from({ length: N }, (_, i) => {
  const theta = 2 * Math.PI * i / GOLDEN_RATIO
  const phi = Math.acos(1 - 2 * i / (N - 1))
  return {
    x: Math.sin(phi) * Math.cos(theta),
    y: Math.sin(phi) * Math.sin(theta),
    z: Math.cos(phi),
  }
})

// Precompute connected pairs so the draw loop is O(pairs) not O(N²)
const PAIRS: [number, number][] = []
for (let i = 0; i < N; i++) {
  for (let j = i + 1; j < N; j++) {
    const dx = BASE_POINTS[i].x - BASE_POINTS[j].x
    const dy = BASE_POINTS[i].y - BASE_POINTS[j].y
    const dz = BASE_POINTS[i].z - BASE_POINTS[j].z
    if (dx * dx + dy * dy + dz * dz < LINE_DIST_SQ) {
      PAIRS.push([i, j])
    }
  }
}

interface Props {
  mode?: 'fullscreen' | 'orb'
}

export default function SphereCanvas({ mode = 'fullscreen' }: Props) {
  const canvasRef = useRef<HTMLCanvasElement>(null)
  const { state } = useJarvis()
  const stateRef = useRef(state)
  stateRef.current = state

  useEffect(() => {
    const canvas = canvasRef.current
    if (!canvas) return
    const ctx = canvas.getContext('2d')!

    let angleX = 0
    let angleY = 0
    let rafId: number

    const resize = () => {
      canvas.width = canvas.offsetWidth
      canvas.height = canvas.offsetHeight
    }
    resize()
    const ro = new ResizeObserver(resize)
    ro.observe(canvas)

    const draw = () => {
      const { status, amplitude } = stateRef.current
      const w = canvas.width
      const h = canvas.height
      const cx = w / 2
      const cy = h / 2
      const radius = Math.min(w, h) * 0.38
      const focal = 400

      ctx.clearRect(0, 0, w, h)

      angleX += 0.003
      angleY += 0.005
      const cosX = Math.cos(angleX), sinX = Math.sin(angleX)
      const cosY = Math.cos(angleY), sinY = Math.sin(angleY)

      const pulsing =
        status === 'GREETING' || status === 'LISTENING' || status === 'RESPONDING'
      const pulse = pulsing ? 1 + amplitude * 2 : 1

      // Rotate + project all points to screen space
      const proj = BASE_POINTS.map(p => {
        const x1 = p.x * cosY + p.z * sinY
        const z1 = -p.x * sinY + p.z * cosY
        const y1 = p.y * cosX - z1 * sinX
        const z2 = p.y * sinX + z1 * cosX
        const scale = focal / (focal + z2 * radius)
        return { sx: cx + x1 * radius * scale, sy: cy + y1 * radius * scale, z: z2 }
      })

      // Lines
      ctx.strokeStyle = '#00c9ff'
      ctx.shadowColor = '#00c9ff'
      ctx.shadowBlur = 6
      ctx.lineWidth = 0.5
      const lineAlpha = pulsing ? 0.08 + amplitude * 0.18 : 0.06

      for (const [i, j] of PAIRS) {
        const depth = ((proj[i].z + proj[j].z) / 2 + 1) / 2
        ctx.globalAlpha = lineAlpha * depth
        ctx.beginPath()
        ctx.moveTo(proj[i].sx, proj[i].sy)
        ctx.lineTo(proj[j].sx, proj[j].sy)
        ctx.stroke()
      }

      // Dots
      ctx.fillStyle = '#00c9ff'
      ctx.shadowBlur = 8
      for (let i = 0; i < N; i++) {
        const depthScale = (proj[i].z + 1) / 2
        const r = (1 + depthScale) * 1.5 * pulse
        ctx.globalAlpha = 0.4 + depthScale * 0.6
        ctx.beginPath()
        ctx.arc(proj[i].sx, proj[i].sy, r, 0, Math.PI * 2)
        ctx.fill()
      }

      ctx.globalAlpha = 1
      ctx.shadowBlur = 0
      rafId = requestAnimationFrame(draw)
    }

    rafId = requestAnimationFrame(draw)
    return () => {
      cancelAnimationFrame(rafId)
      ro.disconnect()
    }
  }, [])

  return (
    <canvas
      ref={canvasRef}
      className={mode === 'orb' ? 'block w-[120px] h-[120px]' : 'block w-full h-full'}
    />
  )
}
