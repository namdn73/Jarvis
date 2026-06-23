import { createContext, useContext, useReducer, type ReactNode } from 'react'
import type { JarvisState, WsMessage } from '../types'

const initialState: JarvisState = {
  status: 'STANDBY',
  transcript: '',
  results: [],
  amplitude: 0,
  log: [],
}

function jarvisReducer(state: JarvisState, message: WsMessage): JarvisState {
  switch (message.type) {
    case 'state_change':
      return { ...state, status: message.payload.state }
    case 'transcript':
      return {
        ...state,
        transcript: message.payload.text,
        log: [...state.log, `You: ${message.payload.text}`],
      }
    case 'results':
      return { ...state, results: message.payload.items }
    case 'amplitude':
      return { ...state, amplitude: message.payload.value }
    case 'tts_text':
      return { ...state, log: [...state.log, `Jarvis: ${message.payload.text}`] }
  }
}

type JarvisContextType = {
  state: JarvisState
  dispatch: React.Dispatch<WsMessage>
}

const JarvisContext = createContext<JarvisContextType | null>(null)

export function JarvisProvider({ children }: { children: ReactNode }) {
  const [state, dispatch] = useReducer(jarvisReducer, initialState)
  return (
    <JarvisContext.Provider value={{ state, dispatch }}>
      {children}
    </JarvisContext.Provider>
  )
}

export function useJarvis(): JarvisContextType {
  const ctx = useContext(JarvisContext)
  if (!ctx) throw new Error('useJarvis must be used within JarvisProvider')
  return ctx
}
