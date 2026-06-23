import { useRef, useEffect } from 'react'
import { useJarvis } from '../context/JarvisContext'

export default function ConversationLog() {
  const { state } = useJarvis()
  const bottomRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [state.log])

  return (
    <div className="flex flex-col gap-2 overflow-y-auto h-full px-3 py-2">
      {state.log.length === 0 && (
        <p className="text-gray-600 font-inter text-xs text-center mt-4">
          Conversation will appear here…
        </p>
      )}

      {state.log.map((entry, i) => {
        const isUser = entry.startsWith('You: ')
        const text = isUser ? entry.slice('You: '.length) : entry.slice('Jarvis: '.length)
        return (
          <div key={i} className={`flex ${isUser ? 'justify-end' : 'justify-start'}`}>
            <span
              className={`max-w-[80%] text-xs font-inter px-3 py-2 rounded-lg leading-relaxed ${
                isUser ? 'bg-white/10 text-white' : 'text-jarvis-cyan'
              }`}
            >
              {text}
            </span>
          </div>
        )
      })}

      <div ref={bottomRef} />
    </div>
  )
}
