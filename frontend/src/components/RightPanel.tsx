import ResultCard from './ResultCard'
import { useJarvis } from '../context/JarvisContext'

export default function RightPanel() {
  const { state } = useJarvis()
  const { results, status } = state

  const showSkeleton =
    results.length === 0 &&
    status !== 'STANDBY' &&
    status !== 'LISTENING' &&
    status !== 'GREETING'

  return (
    <div className="h-full overflow-y-auto p-4 animate-slide-in-right">
      <h2 className="font-orbitron text-jarvis-cyan text-xs tracking-[0.2em] uppercase mb-4">
        Results
      </h2>

      {showSkeleton ? (
        <div className="flex flex-col gap-3">
          {[0, 1, 2].map(i => (
            <div
              key={i}
              className="bg-jarvis-panel border border-jarvis-border rounded-lg p-4 animate-pulse"
              style={{ animationDelay: `${i * 120}ms` }}
            >
              <div className="h-2 bg-jarvis-border rounded w-1/4 mb-3" />
              <div className="h-3 bg-jarvis-border rounded w-3/4 mb-2" />
              <div className="h-2 bg-jarvis-border rounded w-full mb-1" />
              <div className="h-2 bg-jarvis-border rounded w-5/6" />
            </div>
          ))}
        </div>
      ) : (
        <div className="flex flex-col gap-3">
          {results.slice(0, 5).map((item, i) => (
            <ResultCard key={i} item={item} delay={i * 80} />
          ))}
        </div>
      )}
    </div>
  )
}
