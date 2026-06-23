import { describe, it, expect } from 'vitest'
import { jarvisReducer } from '../context/JarvisContext'
import type { JarvisState, ResultItem, WsMessage } from '../types'

const initialState: JarvisState = {
  status: 'STANDBY',
  transcript: '',
  results: [],
  amplitude: 0,
  log: [],
}

describe('jarvisReducer', () => {
  it('state_change updates status', () => {
    const msg: WsMessage = { type: 'state_change', payload: { state: 'LISTENING' } }
    const next = jarvisReducer(initialState, msg)
    expect(next.status).toBe('LISTENING')
    expect(next.transcript).toBe('')
    expect(next.log).toEqual([])
  })

  it('transcript sets transcript and appends to log with You: prefix', () => {
    const msg: WsMessage = { type: 'transcript', payload: { text: 'what time is it' } }
    const next = jarvisReducer(initialState, msg)
    expect(next.transcript).toBe('what time is it')
    expect(next.log).toEqual(['You: what time is it'])
  })

  it('transcript appends to existing log entries', () => {
    const stateWithLog: JarvisState = { ...initialState, log: ['Jarvis: Hello sir'] }
    const msg: WsMessage = { type: 'transcript', payload: { text: 'search the web' } }
    const next = jarvisReducer(stateWithLog, msg)
    expect(next.log).toEqual(['Jarvis: Hello sir', 'You: search the web'])
  })

  it('results replaces results array entirely', () => {
    const items: ResultItem[] = [
      { title: 'OpenAI', url: 'https://openai.com', snippet: 'AI company', source: 'web' },
      { title: 'Anthropic', url: 'https://anthropic.com', snippet: 'AI safety', source: 'news' },
    ]
    const msg: WsMessage = { type: 'results', payload: { items } }
    const stateWithOldResults: JarvisState = {
      ...initialState,
      results: [{ title: 'Old', url: '', snippet: '', source: '' }],
    }
    const next = jarvisReducer(stateWithOldResults, msg)
    expect(next.results).toEqual(items)
    expect(next.results).toHaveLength(2)
  })

  it('amplitude updates amplitude value', () => {
    const msg: WsMessage = { type: 'amplitude', payload: { value: 0.75 } }
    const next = jarvisReducer(initialState, msg)
    expect(next.amplitude).toBe(0.75)
  })

  it('tts_text appends Jarvis line to log', () => {
    const msg: WsMessage = { type: 'tts_text', payload: { text: 'Hello sir, how can I help?' } }
    const next = jarvisReducer(initialState, msg)
    expect(next.log).toEqual(['Jarvis: Hello sir, how can I help?'])
  })

  it('tts_text appends to existing log entries', () => {
    const stateWithLog: JarvisState = { ...initialState, log: ['You: hello'] }
    const msg: WsMessage = { type: 'tts_text', payload: { text: 'Goodbye sir' } }
    const next = jarvisReducer(stateWithLog, msg)
    expect(next.log).toEqual(['You: hello', 'Jarvis: Goodbye sir'])
  })

  it('state_change to STANDBY preserves existing results', () => {
    const items: ResultItem[] = [{ title: 'News', url: 'https://bbc.com', snippet: '', source: 'news' }]
    const stateWithResults: JarvisState = { ...initialState, results: items, status: 'RESPONDING' }
    const msg: WsMessage = { type: 'state_change', payload: { state: 'STANDBY' } }
    const next = jarvisReducer(stateWithResults, msg)
    expect(next.status).toBe('STANDBY')
    expect(next.results).toEqual(items)
  })
})
