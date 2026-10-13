import { useMemo, useState } from 'react'
import { placeLabel } from './api/geocoding'
import type { Place } from './api/types'
import { CitySearch } from './components/CitySearch'
import { CurrentCards } from './components/CurrentCards'
import { ForecastViz } from './components/ForecastViz'
import { useGeolocation } from './hooks/useGeolocation'
import { useWeather } from './hooks/useWeather'
import { weatherMeta } from './lib/weatherCodes'
import './App.css'

function App() {
  const geo = useGeolocation(true)
  const [manualPlace, setManualPlace] = useState<Place | null>(null)

  const activePlace = manualPlace ?? geo.place
  const { data, loading, error } = useWeather(activePlace)

  const needsSearch =
    geo.status === 'denied' ||
    geo.status === 'unavailable' ||
    (geo.status !== 'requesting' && !activePlace)

  const tone = useMemo(() => {
    if (!data) return 'cloud'
    return weatherMeta(data.current.weatherCode).tone
  }, [data])

  const dayPart = data?.current.isDay ? 'day' : 'night'

  return (
    <div className={`app tone-${tone} daypart-${dayPart}`}>
      <div className="sky" aria-hidden="true" />
      <div className="shell">
        <header className="topbar">
          <div>
            <p className="brand">Skyline</p>
            <h1>Weather nearby</h1>
          </div>
          <div className="topbar__actions">
            {geo.status === 'granted' && manualPlace ? (
              <button
                type="button"
                className="ghost-btn"
                onClick={() => setManualPlace(null)}
              >
                Use my location
              </button>
            ) : null}
            {geo.status !== 'granted' ? (
              <button type="button" className="ghost-btn" onClick={geo.request}>
                Retry location
              </button>
            ) : null}
          </div>
        </header>

        {(needsSearch || manualPlace || geo.status === 'granted') && (
          <CitySearch
            prominent={needsSearch && !activePlace}
            autoFocus={needsSearch && !activePlace}
            onSelect={setManualPlace}
          />
        )}

        {geo.status === 'requesting' && !manualPlace ? (
          <p className="status">Requesting location…</p>
        ) : null}
        {geo.error && !manualPlace ? <p className="status status--warn">{geo.error}</p> : null}

        {activePlace && loading ? <p className="status">Loading forecast…</p> : null}
        {error ? <p className="status status--error">{error}</p> : null}

        {activePlace && data && !loading ? (
          <>
            <p className="place-line">
              Showing{' '}
              <strong>
                {activePlace.source === 'geo'
                  ? 'your current position'
                  : placeLabel(activePlace)}
              </strong>
            </p>
            <CurrentCards place={activePlace} weather={data} />
            <ForecastViz weather={data} />
          </>
        ) : null}

        {!activePlace && needsSearch ? (
          <p className="status">
            Allow location access, or type a city name to see the forecast.
          </p>
        ) : null}

        <footer className="footer">
          <p>
            Data from{' '}
            <a href="https://open-meteo.com/" target="_blank" rel="noreferrer">
              Open-Meteo
            </a>
            . No API key required for non-commercial use.
          </p>
        </footer>
      </div>
    </div>
  )
}

export default App
