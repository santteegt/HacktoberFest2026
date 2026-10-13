/** WMO weather interpretation codes used by Open-Meteo. */
export type WeatherMeta = {
  label: string
  icon: string
  tone: 'clear' | 'cloud' | 'fog' | 'rain' | 'snow' | 'storm'
}

const TABLE: Record<number, WeatherMeta> = {
  0: { label: 'Clear sky', icon: '☀', tone: 'clear' },
  1: { label: 'Mainly clear', icon: '🌤', tone: 'clear' },
  2: { label: 'Partly cloudy', icon: '⛅', tone: 'cloud' },
  3: { label: 'Overcast', icon: '☁', tone: 'cloud' },
  45: { label: 'Fog', icon: '🌫', tone: 'fog' },
  48: { label: 'Rime fog', icon: '🌫', tone: 'fog' },
  51: { label: 'Light drizzle', icon: '🌦', tone: 'rain' },
  53: { label: 'Drizzle', icon: '🌦', tone: 'rain' },
  55: { label: 'Heavy drizzle', icon: '🌧', tone: 'rain' },
  56: { label: 'Freezing drizzle', icon: '🌧', tone: 'rain' },
  57: { label: 'Heavy freezing drizzle', icon: '🌧', tone: 'rain' },
  61: { label: 'Slight rain', icon: '🌧', tone: 'rain' },
  63: { label: 'Rain', icon: '🌧', tone: 'rain' },
  65: { label: 'Heavy rain', icon: '🌧', tone: 'rain' },
  66: { label: 'Freezing rain', icon: '🌧', tone: 'rain' },
  67: { label: 'Heavy freezing rain', icon: '🌧', tone: 'rain' },
  71: { label: 'Slight snow', icon: '❄', tone: 'snow' },
  73: { label: 'Snow', icon: '❄', tone: 'snow' },
  75: { label: 'Heavy snow', icon: '❄', tone: 'snow' },
  77: { label: 'Snow grains', icon: '❄', tone: 'snow' },
  80: { label: 'Slight showers', icon: '🌦', tone: 'rain' },
  81: { label: 'Showers', icon: '🌧', tone: 'rain' },
  82: { label: 'Violent showers', icon: '🌧', tone: 'rain' },
  85: { label: 'Slight snow showers', icon: '❄', tone: 'snow' },
  86: { label: 'Heavy snow showers', icon: '❄', tone: 'snow' },
  95: { label: 'Thunderstorm', icon: '⛈', tone: 'storm' },
  96: { label: 'Thunderstorm with hail', icon: '⛈', tone: 'storm' },
  99: { label: 'Thunderstorm with heavy hail', icon: '⛈', tone: 'storm' },
}

export function weatherMeta(code: number | null | undefined): WeatherMeta {
  if (code == null) return { label: 'Unknown', icon: '·', tone: 'cloud' }
  return TABLE[code] ?? { label: `Code ${code}`, icon: '☁', tone: 'cloud' }
}

export function windDirectionLabel(degrees: number | null | undefined): string {
  if (degrees == null || Number.isNaN(degrees)) return '—'
  const dirs = ['N', 'NE', 'E', 'SE', 'S', 'SW', 'W', 'NW']
  const idx = Math.round((((degrees % 360) + 360) % 360) / 45) % 8
  return dirs[idx]
}
