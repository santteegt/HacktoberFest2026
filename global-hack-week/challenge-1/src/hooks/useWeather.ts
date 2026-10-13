import { useEffect, useState } from 'react'
import { fetchWeather } from '../api/openMeteo'
import type { Place, WeatherBundle } from '../api/types'

type WeatherState = {
  data: WeatherBundle | null
  loading: boolean
  error: string | null
}

export function useWeather(place: Place | null) {
  const [state, setState] = useState<WeatherState>({
    data: null,
    loading: false,
    error: null,
  })

  useEffect(() => {
    if (!place) {
      setState({ data: null, loading: false, error: null })
      return
    }

    const controller = new AbortController()
    setState((prev) => ({ ...prev, loading: true, error: null }))

    fetchWeather(place.latitude, place.longitude, controller.signal)
      .then((data) => {
        if (!controller.signal.aborted) {
          setState({ data, loading: false, error: null })
        }
      })
      .catch((err: unknown) => {
        if (controller.signal.aborted) return
        const message = err instanceof Error ? err.message : 'Failed to load weather'
        setState({ data: null, loading: false, error: message })
      })

    return () => controller.abort()
  }, [place])

  return state
}
