import type { Place } from './types'

type GeocodeResult = {
  id: number
  name: string
  latitude: number
  longitude: number
  admin1?: string
  country?: string
  timezone?: string
}

type GeocodeResponse = {
  results?: GeocodeResult[]
}

export async function searchCities(query: string, signal?: AbortSignal): Promise<Place[]> {
  const name = query.trim()
  if (name.length < 2) return []

  const url = new URL('https://geocoding-api.open-meteo.com/v1/search')
  url.searchParams.set('name', name)
  url.searchParams.set('count', '8')
  url.searchParams.set('language', 'en')
  url.searchParams.set('format', 'json')

  const res = await fetch(url, { signal })
  if (!res.ok) throw new Error(`City search failed (${res.status})`)
  const data = (await res.json()) as GeocodeResponse

  return (data.results ?? []).map((r) => ({
    id: String(r.id),
    name: r.name,
    latitude: r.latitude,
    longitude: r.longitude,
    admin1: r.admin1,
    country: r.country,
    timezone: r.timezone,
    source: 'search' as const,
  }))
}

export function placeLabel(place: Place): string {
  return [place.name, place.admin1, place.country].filter(Boolean).join(', ')
}
