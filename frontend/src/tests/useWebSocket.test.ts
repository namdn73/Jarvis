import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { renderHook, act } from '@testing-library/react'
import { useWebSocket } from '../hooks/useWebSocket'
import type { WsMessage } from '../types'

// Minimal WebSocket mock — tracks the most-recently created instance
class MockWebSocket {
  static last: MockWebSocket | null = null

  url: string
  onopen: (() => void) | null = null
  onmessage: ((e: { data: string }) => void) | null = null
  onclose: (() => void) | null = null

  constructor(url: string) {
    this.url = url
    MockWebSocket.last = this
  }

  close() {}
}

beforeEach(() => {
  vi.useFakeTimers()
  MockWebSocket.last = null
  vi.stubGlobal('WebSocket', MockWebSocket)
})

afterEach(() => {
  vi.useRealTimers()
  vi.unstubAllGlobals()
})

describe('useWebSocket', () => {
  it('returns connected=false before the socket opens', () => {
    const dispatch = vi.fn()
    const { result } = renderHook(() => useWebSocket(dispatch))
    expect(result.current.connected).toBe(false)
  })

  it('sets connected=true when the socket fires onopen', async () => {
    const dispatch = vi.fn()
    const { result } = renderHook(() => useWebSocket(dispatch))

    await act(async () => {
      MockWebSocket.last!.onopen!()
    })

    expect(result.current.connected).toBe(true)
  })

  it('calls dispatch with the parsed WsMessage on each message', async () => {
    const dispatch = vi.fn()
    renderHook(() => useWebSocket(dispatch))

    const msg: WsMessage = { type: 'state_change', payload: { state: 'LISTENING' } }

    await act(async () => {
      MockWebSocket.last!.onmessage!({ data: JSON.stringify(msg) })
    })

    expect(dispatch).toHaveBeenCalledTimes(1)
    expect(dispatch).toHaveBeenCalledWith(msg)
  })

  it('does not throw on malformed JSON — just logs an error', async () => {
    const dispatch = vi.fn()
    const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {})
    renderHook(() => useWebSocket(dispatch))

    await act(async () => {
      MockWebSocket.last!.onmessage!({ data: 'not-json' })
    })

    expect(dispatch).not.toHaveBeenCalled()
    expect(consoleSpy).toHaveBeenCalled()
    consoleSpy.mockRestore()
  })

  it('sets connected=false when socket closes', async () => {
    const dispatch = vi.fn()
    const { result } = renderHook(() => useWebSocket(dispatch))

    await act(async () => { MockWebSocket.last!.onopen!() })
    expect(result.current.connected).toBe(true)

    await act(async () => { MockWebSocket.last!.onclose!() })
    expect(result.current.connected).toBe(false)
  })

  it('reconnects after 2s when the socket closes', async () => {
    const dispatch = vi.fn()
    renderHook(() => useWebSocket(dispatch))

    const firstSocket = MockWebSocket.last

    await act(async () => { MockWebSocket.last!.onclose!() })

    // No new socket yet — reconnect is scheduled
    expect(MockWebSocket.last).toBe(firstSocket)

    // Advance past the 2-second delay
    await act(async () => { vi.advanceTimersByTime(2000) })

    expect(MockWebSocket.last).not.toBe(firstSocket)
    expect(MockWebSocket.last).not.toBeNull()
  })

  it('does not reconnect after unmount', async () => {
    const dispatch = vi.fn()
    const { unmount } = renderHook(() => useWebSocket(dispatch))

    // Trigger close so a reconnect timer is scheduled
    await act(async () => { MockWebSocket.last!.onclose!() })

    const socketAfterClose = MockWebSocket.last

    // Unmount before the 2s timer fires
    unmount()

    // Advance past the reconnect delay — connect() should bail due to unmount guard
    await act(async () => { vi.advanceTimersByTime(2000) })

    expect(MockWebSocket.last).toBe(socketAfterClose)
  })
})
