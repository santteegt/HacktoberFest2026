export function formatTemp(value: number | null | undefined, unit = '°'): string {
  if (value == null || Number.isNaN(value)) return '—'
  return `${Math.round(value)}${unit}`
}

export function formatPercent(value: number | null | undefined): string {
  if (value == null || Number.isNaN(value)) return '—'
  return `${Math.round(value)}%`
}

export function formatWind(value: number | null | undefined, unit = 'km/h'): string {
  if (value == null || Number.isNaN(value)) return '—'
  return `${Math.round(value)} ${unit}`
}

export function formatPrecip(value: number | null | undefined, unit = 'mm'): string {
  if (value == null || Number.isNaN(value)) return '—'
  return `${value.toFixed(value >= 10 ? 0 : 1)} ${unit}`
}

export function formatHour(iso: string, timeZone?: string): string {
  const d = new Date(iso)
  return new Intl.DateTimeFormat(undefined, {
    hour: 'numeric',
    timeZone,
  }).format(d)
}

export function formatWeekday(iso: string, timeZone?: string): string {
  const d = new Date(iso)
  return new Intl.DateTimeFormat(undefined, {
    weekday: 'short',
    month: 'short',
    day: 'numeric',
    timeZone,
  }).format(d)
}

export function formatClock(iso: string, timeZone?: string): string {
  const d = new Date(iso)
  return new Intl.DateTimeFormat(undefined, {
    weekday: 'long',
    hour: 'numeric',
    minute: '2-digit',
    timeZone,
  }).format(d)
}
