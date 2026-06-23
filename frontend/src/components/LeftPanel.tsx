import SphereCanvas from './SphereCanvas'
import WaveformCanvas from './WaveformCanvas'
import StatusBadge from './StatusBadge'
import ConversationLog from './ConversationLog'
import { useJarvis } from '../context/JarvisContext'

interface Props {
  connected: boolean
}

export default function LeftPanel({ connected }: Props) {
  const { state } = useJarvis()
  const showWaveform = state.status === 'LISTENING' || state.status === 'RESPONDING'

  return (
    <div className="flex flex-col h-full border-r border-jarvis-border">
      {/* Orb + status badge */}
      <div className="flex items-center gap-3 p-4 flex-shrink-0">
        <div className="w-[120px] h-[120px] flex-shrink-0">
          <SphereCanvas mode="orb" />
        </div>
        <StatusBadge connected={connected} />
      </div>

      {/* Waveform — visible only while audio is active */}
      <div
        className={`px-4 flex-shrink-0 transition-all duration-500 ${
          showWaveform ? 'h-16 opacity-100' : 'h-0 opacity-0 overflow-hidden'
        }`}
      >
        <WaveformCanvas />
      </div>

      {/* Conversation log — fills remaining height */}
      <div className="flex-1 min-h-0">
        <ConversationLog />
      </div>
    </div>
  )
}
