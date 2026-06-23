import { useJarvis } from '../context/JarvisContext'
import type { JarvisStatus } from '../types'

interface Props {
  connected: boolean
}

type BadgeConfig = { label: string; colorClass: string; pulse: boolean }

function getConfig(status: JarvisStatus, connected: boolean): BadgeConfig {
  if (!connected) return { label: 'DISCONNECTED', colorClass: 'text-gray-500', pulse: false }
  switch (status) {
    case 'STANDBY':      return { label: 'STANDBY',    colorClass: 'text-gray-400',   pulse: false }
    case 'GREETING':     return { label: 'GREETING',   colorClass: 'text-jarvis-cyan', pulse: true  }
    case 'LISTENING':    return { label: 'LISTENING',  colorClass: 'text-jarvis-cyan', pulse: true  }
    case 'PROCESSING':   return { label: 'PROCESSING', colorClass: 'text-amber-400',   pulse: true  }
    case 'RESPONDING':   return { label: 'RESPONDING', colorClass: 'text-green-400',   pulse: false }
    case 'ACTIVE_WINDOW':return { label: 'ACTIVE',     colorClass: 'text-jarvis-cyan', pulse: false }
  }
}

export default function StatusBadge({ connected }: Props) {
  const { state } = useJarvis()
  const { label, colorClass, pulse } = getConfig(state.status, connected)

  return (
    <span
      className={`font-orbitron text-xs tracking-[0.2em] uppercase ${colorClass} ${pulse ? 'animate-pulse' : ''}`}
    >
      {label}
    </span>
  )
}
