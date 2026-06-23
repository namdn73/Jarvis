import { useEffect } from 'react'

type Layout = 'IDLE' | 'ACTIVE'

export function useMouseActivity(layout: Layout, setLayout: (l: Layout) => void): void {
  useEffect(() => {
    let debouncing = false

    function handleMouseMove() {
      if (layout !== 'IDLE' || debouncing) return
      debouncing = true
      setLayout('ACTIVE')
      setTimeout(() => { debouncing = false }, 500)
    }

    window.addEventListener('mousemove', handleMouseMove)
    return () => window.removeEventListener('mousemove', handleMouseMove)
  }, [layout, setLayout])
}
