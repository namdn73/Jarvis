import type { ResultItem } from '../types'

interface Props {
  item: ResultItem
  delay?: number
}

export default function ResultCard({ item, delay = 0 }: Props) {
  return (
    <div
      className="bg-jarvis-panel border border-jarvis-border rounded-lg p-4
                 hover:border-jarvis-cyan hover:shadow-[0_0_20px_rgba(0,201,255,0.3)]
                 transition-all duration-300 animate-fade-in"
      style={{ animationDelay: `${delay}ms`, animationFillMode: 'backwards' }}
    >
      <span className="inline-block font-orbitron text-[10px] tracking-widest uppercase
                       text-jarvis-cyan border border-jarvis-border px-2 py-0.5 rounded mb-2">
        {item.source}
      </span>

      <p className="text-white font-inter font-semibold text-sm leading-snug mb-1 line-clamp-2">
        {item.title}
      </p>

      <p className="text-gray-400 font-inter text-xs leading-relaxed mb-3 line-clamp-3">
        {item.snippet}
      </p>

      {item.url && (
        <a
          href={item.url}
          target="_blank"
          rel="noopener noreferrer"
          className="text-jarvis-cyan font-inter text-xs hover:underline"
        >
          Open →
        </a>
      )}
    </div>
  )
}
