import { useEffect, useId, useRef, useState } from 'react'
import { placeLabel, searchCities } from '../api/geocoding'
import type { Place } from '../api/types'

type Props = {
  onSelect: (place: Place) => void
  autoFocus?: boolean
  prominent?: boolean
}

export function CitySearch({ onSelect, autoFocus = false, prominent = false }: Props) {
  const listId = useId()
  const [query, setQuery] = useState('')
  const [results, setResults] = useState<Place[]>([])
  const [open, setOpen] = useState(false)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const wrapRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (query.trim().length < 2) {
      setResults([])
      setLoading(false)
      setError(null)
      return
    }

    const controller = new AbortController()
    const timer = window.setTimeout(() => {
      setLoading(true)
      setError(null)
      searchCities(query, controller.signal)
        .then((places) => {
          if (!controller.signal.aborted) {
            setResults(places)
            setOpen(true)
            setLoading(false)
          }
        })
        .catch((err: unknown) => {
          if (controller.signal.aborted) return
          setResults([])
          setLoading(false)
          setError(err instanceof Error ? err.message : 'Search failed')
        })
    }, 280)

    return () => {
      controller.abort()
      window.clearTimeout(timer)
    }
  }, [query])

  useEffect(() => {
    const onPointer = (event: MouseEvent) => {
      if (!wrapRef.current?.contains(event.target as Node)) setOpen(false)
    }
    document.addEventListener('mousedown', onPointer)
    return () => document.removeEventListener('mousedown', onPointer)
  }, [])

  return (
    <div
      className={`city-search ${prominent ? 'city-search--prominent' : ''}`}
      ref={wrapRef}
    >
      <label className="city-search__label" htmlFor="city-query">
        Search city
      </label>
      <div className="city-search__field">
        <input
          id="city-query"
          type="search"
          autoComplete="off"
          autoFocus={autoFocus}
          placeholder="Search for a city…"
          value={query}
          role="combobox"
          aria-expanded={open}
          aria-controls={listId}
          aria-autocomplete="list"
          onChange={(e) => setQuery(e.target.value)}
          onFocus={() => results.length > 0 && setOpen(true)}
        />
        {loading ? <span className="city-search__hint">Searching…</span> : null}
      </div>
      {error ? <p className="city-search__error">{error}</p> : null}
      {open && results.length > 0 ? (
        <ul id={listId} className="city-search__results" role="listbox">
          {results.map((place) => (
            <li key={place.id} role="option">
              <button
                type="button"
                onClick={() => {
                  onSelect(place)
                  setQuery(placeLabel(place))
                  setOpen(false)
                }}
              >
                {placeLabel(place)}
              </button>
            </li>
          ))}
        </ul>
      ) : null}
      {open && !loading && query.trim().length >= 2 && results.length === 0 && !error ? (
        <p className="city-search__empty">No cities matched that search.</p>
      ) : null}
    </div>
  )
}
