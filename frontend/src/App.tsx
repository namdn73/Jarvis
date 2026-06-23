import { useState, useEffect } from 'react'
import { JarvisProvider, useJarvis } from './context/JarvisContext'
import { useWebSocket } from './hooks/useWebSocket'
import { useMouseActivity } from './hooks/useMouseActivity'

type Layout = 'IDLE' | 'ACTIVE'

function AppInner() {
  const { state, dispatch } = useJarvis()
  const [layout, setLayout] = useState<Layout>('IDLE')
  const { connected } = useWebSocket(dispatch)

  useMouseActivity(layout, setLayout)

  useEffect(() => {
    if (state.status !== 'STANDBY') setLayout('ACTIVE')
    else setLayout('IDLE')
  }, [state.status])

  return (
    <div className="w-screen h-screen bg-jarvis-bg text-white font-inter flex items-center justify-center">
      <div className="text-center">
        <div className="text-jarvis-cyan font-orbitron text-4xl font-bold tracking-widest mb-4">
          JARVIS
        </div>
        <div className="text-jarvis-cyan font-orbitron text-sm tracking-wider opacity-70">
          {connected ? state.status : 'DISCONNECTED'}
        </div>
        <div className="mt-2 text-xs text-white/30 font-inter">
          {layout === 'IDLE' ? 'Move mouse to activate' : 'Active'}
        </div>
      </div>
    </div>
  )
}

export default function App() {
  return (
    <JarvisProvider>
      <AppInner />
    </JarvisProvider>
  )
}
