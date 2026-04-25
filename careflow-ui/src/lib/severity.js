export const SEVERITY_COLORS = {
  LOW: 'text-green-400 bg-green-900',
  MEDIUM: 'text-yellow-400 bg-yellow-900',
  HIGH: 'text-orange-400 bg-orange-900',
  CRITICAL: 'text-red-400 bg-red-900',
}

export const SEVERITY_DOT = {
  LOW: 'bg-green-400',
  MEDIUM: 'bg-yellow-400',
  HIGH: 'bg-orange-400',
  CRITICAL: 'bg-red-400',
}

export function scoreToSeverity(score) {
  if (score >= 0.8) return 'CRITICAL'
  if (score >= 0.6) return 'HIGH'
  if (score >= 0.4) return 'MEDIUM'
  return 'LOW'
}
