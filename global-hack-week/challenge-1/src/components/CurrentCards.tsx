import type { Place, WeatherBundle } from '../api/types'
import { placeLabel } from '../api/geocoding'
import {
  formatClock,
  formatPercent,
  formatPrecip,
  formatTemp,
  formatWind,
} from '../lib/format'
import { weatherMeta, windDirectionLabel } from '../lib/weatherCodes'

type Props = {
  place: Place
  weather: WeatherBundle
}

export function CurrentCards({ place, weather }: Props) {
  const { current, timezone } = weather
  const meta = weatherMeta(current.weatherCode)
  const title = place.source === 'geo' ? 'Near you' : placeLabel(place)

  return (
    <section className="current-grid" aria-label="Current conditions">
      <article className="wx-card wx-card--hero">
        <p className="wx-card__eyebrow">{title}</p>
        <div className="wx-card__hero-row">
          <span className="wx-card__icon" aria-hidden="true">
            {meta.icon}
          </span>
          <div>
            <p className="wx-card__temp">{formatTemp(current.temperature)}</p>
            <p className="wx-card__condition">{meta.label}</p>
          </div>
        </div>
        <p className="wx-card__feels">
          Feels like {formatTemp(current.apparentTemperature)}
        </p>
        <p className="wx-card__time">{formatClock(current.time, timezone)}</p>
      </article>

      <article className="wx-card wx-card--details">
        <h2 className="wx-card__title">Atmosphere</h2>
        <dl className="wx-stats">
          <div>
            <dt>Humidity</dt>
            <dd>{formatPercent(current.humidity)}</dd>
          </div>
          <div>
            <dt>Wind</dt>
            <dd>
              {formatWind(current.windSpeed)} {windDirectionLabel(current.windDirection)}
            </dd>
          </div>
          <div>
            <dt>Gusts</dt>
            <dd>{formatWind(current.windGusts)}</dd>
          </div>
          <div>
            <dt>Precip</dt>
            <dd>{formatPrecip(current.precipitation)}</dd>
          </div>
          <div>
            <dt>Clouds</dt>
            <dd>{formatPercent(current.cloudCover)}</dd>
          </div>
          <div>
            <dt>Pressure</dt>
            <dd>{Math.round(current.pressureMsl)} hPa</dd>
          </div>
        </dl>
      </article>
    </section>
  )
}
