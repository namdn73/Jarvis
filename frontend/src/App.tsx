import { useState, useEffect } from 'react'
import { JarvisProvider, useJarvis } from './context/JarvisContext'
import { useWebSocket } from './hooks/useWebSocket'
import { useMouseActivity } from './hooks/useMouseActivity'
import SphereCanvas from './components/SphereCanvas'
import LeftPanel from './components/LeftPanel'
import RightPanel from './components/RightPanel'

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
    <div className="w-screen h-screen bg-jarvis-bg text-white font-inter overflow-hidden">
      {layout === 'IDLE' ? (
        <SphereCanvas mode="fullscreen" />
      ) : (
        <div className="flex h-full">
          <div className="w-1/3 h-full">
            <LeftPanel connected={connected} />
          </div>
          <div className="w-2/3 h-full">
            <RightPanel />
          </div>
        </div>
      )}
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
