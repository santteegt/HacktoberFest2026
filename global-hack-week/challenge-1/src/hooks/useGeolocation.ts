import { useCallback, useEffect, useState } from 'react'
import type { Place } from '../api/types'

export type GeoStatus = 'idle' | 'requesting' | 'granted' | 'denied' | 'unavailable'

type GeoState = {
  status: GeoStatus
  place: Place | null
  error: string | null
}

export function useGeolocation(autoRequest = true) {
  const [state, setState] = useState<GeoState>({
    status: 'idle',
    place: null,
    error: null,
  })

  const request = useCallback(() => {
    if (!('geolocation' in navigator)) {
      setState({
        status: 'unavailable',
        place: null,
        error: 'Location services are not available in this browser.',
      })
      return
    }

    setState((prev) => ({ ...prev, status: 'requesting', error: null }))

    navigator.geolocation.getCurrentPosition(
      (pos) => {
        setState({
          status: 'granted',
          place: {
            id: 'geo',
            name: 'Current location',
            latitude: pos.coords.latitude,
            longitude: pos.coords.longitude,
            source: 'geo',
          },
          error: null,
        })
      },
      (err) => {
        const denied = err.code === err.PERMISSION_DENIED
        setState({
          status: denied ? 'denied' : 'unavailable',
          place: null,
          error: denied
            ? 'Location access was denied. Search for a city instead.'
            : 'Could not read your location. Search for a city instead.',
        })
      },
      { enableHighAccuracy: false, timeout: 10000, maximumAge: 5 * 60 * 1000 },
    )
  }, [])

  useEffect(() => {
    if (autoRequest) request()
  }, [autoRequest, request])

  return { ...state, request }
}
