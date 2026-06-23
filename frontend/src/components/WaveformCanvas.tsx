import { useRef, useEffect } from 'react'
import { useJarvis } from '../context/JarvisContext'

const BUFFER_SIZE = 60

export default function WaveformCanvas() {
  const canvasRef = useRef<HTMLCanvasElement>(null)
  const { state } = useJarvis()
  const stateRef = useRef(state)
  stateRef.current = state

  // Rolling amplitude buffer — updated in draw loop, not via useEffect
  const bufferRef = useRef<number[]>(new Array(BUFFER_SIZE).fill(0))

  useEffect(() => {
    const canvas = canvasRef.current
    if (!canvas) return
    const ctx = canvas.getContext('2d')!
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

      // Push latest amplitude into rolling buffer
      bufferRef.current.push(amplitude)
      if (bufferRef.current.length > BUFFER_SIZE) bufferRef.current.shift()

      const w = canvas.width
      const h = canvas.height
      ctx.clearRect(0, 0, w, h)

      const active = status === 'LISTENING' || status === 'RESPONDING'
      if (active) {
        const buf = bufferRef.current
        const n = buf.length
        const barW = w / n
        const centerY = h / 2

        ctx.fillStyle = '#00c9ff'
        ctx.shadowColor = '#00c9ff'
        ctx.shadowBlur = 6

        for (let i = 0; i < n; i++) {
          const barH = Math.max(1, buf[i] * centerY * 0.9)
          const x = i * barW
          // Mirrored vertically around centre
          ctx.fillRect(x + 1, centerY - barH, barW - 2, barH)
          ctx.fillRect(x + 1, centerY, barW - 2, barH)
        }

        ctx.shadowBlur = 0
      }

      rafId = requestAnimationFrame(draw)
    }

    rafId = requestAnimationFrame(draw)
    return () => {
      cancelAnimationFrame(rafId)
      ro.disconnect()
    }
  }, [])

  return <canvas ref={canvasRef} className="block w-full h-full" />
}
