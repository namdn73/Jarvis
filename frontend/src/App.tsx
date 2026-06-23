import { useState, useEffect } from 'react'
import { JarvisProvider, useJarvis } from './context/JarvisContext'
import { useWebSocket } from './hooks/useWebSocket'
import { useMouseActivity } from './hooks/useMouseActivity'
import SphereCanvas from './components/SphereCanvas'
import WaveformCanvas from './components/WaveformCanvas'

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
    <div className="w-screen h-screen bg-jarvis-bg text-white font-inter">
      {/* Session 8 visual test — replaced by full layout in Session 9 */}
      <div className="w-full h-3/4">
        <SphereCanvas mode="fullscreen" />
      </div>
      <div className="w-full h-1/4 flex items-center gap-4 px-4">
        <div className="w-[120px] h-[120px] flex-shrink-0">
          <SphereCanvas mode="orb" />
        </div>
        <div className="flex-1 h-full">
          <WaveformCanvas />
        </div>
        <div className="text-jarvis-cyan font-orbitron text-xs tracking-wider opacity-70 flex-shrink-0">
          {connected ? state.status : 'DISCONNECTED'}
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
