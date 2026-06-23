export type JarvisStatus =
  | 'STANDBY'
  | 'GREETING'
  | 'LISTENING'
  | 'PROCESSING'
  | 'RESPONDING'
  | 'ACTIVE_WINDOW'

export type ResultItem = {
  title: string
  url: string
  snippet: string
  source: string
}

export type WsMessage =
  | { type: 'state_change'; payload: { state: JarvisStatus } }
  | { type: 'transcript'; payload: { text: string } }
  | { type: 'results'; payload: { items: ResultItem[] } }
  | { type: 'amplitude'; payload: { value: number } }
  | { type: 'tts_text'; payload: { text: string } }

export type JarvisState = {
  status: JarvisStatus
  transcript: string
  results: ResultItem[]
  amplitude: number
  log: string[]
}
