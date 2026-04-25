export default function AgentStatusBar({ agents, connected }) {
  return (
    <header className="bg-gray-900 border-b border-gray-800 px-4 py-2 flex items-center gap-6 overflow-x-auto shrink-0">
      <span className="text-brand font-bold text-lg tracking-widest shrink-0">CAREFLOW</span>
      <span className={`text-xs px-2 py-0.5 rounded shrink-0 ${connected ? 'bg-green-900 text-green-300' : 'bg-red-900 text-red-300'}`}>
        {connected ? 'WS connected' : 'reconnecting…'}
      </span>
      <div className="flex gap-4">
        {agents.map((a) => (
          <div key={a.id} className="flex items-center gap-1.5 text-xs text-gray-400">
            <span className={`w-2 h-2 rounded-full ${a.heartbeat ? 'bg-green-400' : 'bg-gray-600'}`} />
            <span>{a.name}</span>
          </div>
        ))}
      </div>
    </header>
  )
}
