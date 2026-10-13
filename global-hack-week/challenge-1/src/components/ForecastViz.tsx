import { useMemo, useRef, useState, type PointerEvent } from 'react'
import type { DailyPoint, HourlyPoint, WeatherBundle } from '../api/types'
import {
  formatHour,
  formatPercent,
  formatPrecip,
  formatTemp,
  formatWeekday,
} from '../lib/format'
import { weatherMeta } from '../lib/weatherCodes'

type Interval = 'hourly' | 'daily'

type Props = {
  weather: WeatherBundle
}

type Selected =
  | { kind: 'hourly'; point: HourlyPoint }
  | { kind: 'daily'; point: DailyPoint }

type ChartBar = {
  key: string
  label: string
  dayLabel?: string
  height: number
  lowMark?: number
  value: string
  lowValue?: string
  precip: number
  code: number
  onSelect: () => void
  active: boolean
}

type LinePoint = { x: number; y: number }

const HOURLY_COL_PX = 68
const TRACK_H = 110

function clampRange(values: number[]): { min: number; max: number } {
  const min = Math.min(...values)
  const max = Math.max(...values)
  if (min === max) return { min: min - 1, max: max + 1 }
  const pad = (max - min) * 0.12
  return { min: min - pad, max: max + pad }
}

/** Column-center points in an SVG coordinate space of width `plotW`. */
function tempLinePoints(heights: number[], plotW: number): LinePoint[] {
  const n = heights.length
  if (n === 0) return []
  const colW = plotW / n
  return heights.map((h, i) => ({
    x: i * colW + colW / 2,
    y: ((100 - h) / 100) * TRACK_H,
  }))
}

/** Catmull-Rom → cubic Bézier so the line rides through each temp without sharp zigzags. */
function smoothLinePath(points: LinePoint[]): string {
  if (points.length === 0) return ''
  if (points.length === 1) {
    const p = points[0]!
    return `M ${p.x} ${p.y}`
  }
  if (points.length === 2) {
    const a = points[0]!
    const b = points[1]!
    return `M ${a.x} ${a.y} L ${b.x} ${b.y}`
  }

  let d = `M ${points[0]!.x} ${points[0]!.y}`
  for (let i = 0; i < points.length - 1; i++) {
    const p0 = points[i === 0 ? 0 : i - 1]!
    const p1 = points[i]!
    const p2 = points[i + 1]!
    const p3 = points[i + 2] ?? p2
    const cp1x = p1.x + (p2.x - p0.x) / 6
    const cp1y = p1.y + (p2.y - p0.y) / 6
    const cp2x = p2.x - (p3.x - p1.x) / 6
    const cp2y = p2.y - (p3.y - p1.y) / 6
    d += ` C ${cp1x} ${cp1y}, ${cp2x} ${cp2y}, ${p2.x} ${p2.y}`
  }
  return d
}

export function ForecastViz({ weather }: Props) {
  const [interval, setInterval] = useState<Interval>('daily')
  const [selected, setSelected] = useState<Selected | null>(null)
  const scrollerRef = useRef<HTMLDivElement>(null)
  const dragRef = useRef<{ active: boolean; startX: number; startScroll: number; moved: boolean }>({
    active: false,
    startX: 0,
    startScroll: 0,
    moved: false,
  })

  const hourlySlice = useMemo(() => {
    const now = Date.now() - 60 * 60 * 1000
    return weather.hourly.filter((h) => new Date(h.time).getTime() >= now)
  }, [weather.hourly])

  const daily = weather.daily

  const chart = useMemo((): { bars: ChartBar[]; lineHeights: number[] } => {
    if (interval === 'hourly') {
      const temps = hourlySlice.map((h) => h.temperature)
      const range = clampRange(temps)
      let lastDayKey = ''
      const bars = hourlySlice.map((point) => {
        const height =
          ((point.temperature - range.min) / (range.max - range.min)) * 100
        const dayKey = new Intl.DateTimeFormat('en-CA', {
          timeZone: weather.timezone,
          year: 'numeric',
          month: '2-digit',
          day: '2-digit',
        }).format(new Date(point.time))
        const showDay = dayKey !== lastDayKey
        lastDayKey = dayKey
        return {
          key: point.time,
          label: formatHour(point.time, weather.timezone),
          dayLabel: showDay
            ? new Intl.DateTimeFormat(undefined, {
                weekday: 'short',
                day: 'numeric',
                timeZone: weather.timezone,
              }).format(new Date(point.time))
            : undefined,
          height,
          value: formatTemp(point.temperature),
          precip: point.precipitationProbability,
          code: point.weatherCode,
          onSelect: () => {
            if (dragRef.current.moved) return
            setSelected({ kind: 'hourly', point })
          },
          active:
            selected?.kind === 'hourly' && selected.point.time === point.time,
        }
      })
      return { bars, lineHeights: bars.map((b) => b.height) }
    }

    const highs = daily.map((d) => d.tempMax)
    const lows = daily.map((d) => d.tempMin)
    const range = clampRange([...highs, ...lows])
    const bars = daily.map((point) => {
      const height =
        ((point.tempMax - range.min) / (range.max - range.min)) * 100
      const lowMark =
        ((point.tempMin - range.min) / (range.max - range.min)) * 100
      return {
        key: point.date,
        label: formatWeekday(point.date, weather.timezone).split(',')[0] ?? '',
        height,
        lowMark,
        value: formatTemp(point.tempMax),
        lowValue: formatTemp(point.tempMin),
        precip: point.precipProbabilityMax,
        code: point.weatherCode,
        onSelect: () => setSelected({ kind: 'daily', point }),
        active: selected?.kind === 'daily' && selected.point.date === point.date,
      }
    })
    return { bars, lineHeights: bars.map((b) => b.height) }
  }, [daily, hourlySlice, interval, selected, weather.timezone])

  const detail = selected ?? (interval === 'daily' && daily[0]
    ? ({ kind: 'daily', point: daily[0] } as Selected)
    : hourlySlice[0]
      ? ({ kind: 'hourly', point: hourlySlice[0] } as Selected)
      : null)

  const plotW =
    interval === 'hourly'
      ? Math.max(chart.bars.length * HOURLY_COL_PX, HOURLY_COL_PX)
      : 1000
  const linePoints = tempLinePoints(chart.lineHeights, plotW)
  const path = smoothLinePath(linePoints)

  const onPointerDown = (event: PointerEvent<HTMLDivElement>) => {
    if (interval !== 'hourly') return
    const el = scrollerRef.current
    if (!el) return
    dragRef.current = {
      active: true,
      startX: event.clientX,
      startScroll: el.scrollLeft,
      moved: false,
    }
    el.classList.add('is-dragging')
    el.setPointerCapture(event.pointerId)
  }

  const onPointerMove = (event: PointerEvent<HTMLDivElement>) => {
    if (!dragRef.current.active || interval !== 'hourly') return
    const el = scrollerRef.current
    if (!el) return
    const dx = event.clientX - dragRef.current.startX
    if (Math.abs(dx) > 4) dragRef.current.moved = true
    el.scrollLeft = dragRef.current.startScroll - dx
  }

  const endDrag = (event: PointerEvent<HTMLDivElement>) => {
    if (!dragRef.current.active) return
    dragRef.current.active = false
    scrollerRef.current?.classList.remove('is-dragging')
    try {
      scrollerRef.current?.releasePointerCapture(event.pointerId)
    } catch {
      /* already released */
    }
    // Allow click after drag ends on next tick.
    window.setTimeout(() => {
      dragRef.current.moved = false
    }, 0)
  }

  return (
    <section className="forecast" aria-label="5-day forecast">
      <header className="forecast__header">
        <div>
          <h2>5-day outlook</h2>
          <p>
            Drag or scroll sideways in Hourly to move through the 5 days. The
            curve follows temperature at each interval.
          </p>
        </div>
        <div className="segmented" role="group" aria-label="Forecast interval">
          <button
            type="button"
            className={interval === 'daily' ? 'is-active' : ''}
            aria-pressed={interval === 'daily'}
            onClick={() => {
              setInterval('daily')
              setSelected(null)
            }}
          >
            Daily
          </button>
          <button
            type="button"
            className={interval === 'hourly' ? 'is-active' : ''}
            aria-pressed={interval === 'hourly'}
            onClick={() => {
              setInterval('hourly')
              setSelected(null)
            }}
          >
            Hourly
          </button>
        </div>
      </header>

      <div
        ref={scrollerRef}
        className={`forecast__scroller forecast__scroller--${interval}`}
        tabIndex={interval === 'hourly' ? 0 : undefined}
        role={interval === 'hourly' ? 'region' : undefined}
        aria-label={interval === 'hourly' ? 'Scrollable hourly forecast' : undefined}
        onPointerDown={onPointerDown}
        onPointerMove={onPointerMove}
        onPointerUp={endDrag}
        onPointerCancel={endDrag}
      >
        <div
          className={`forecast__plot forecast__plot--${interval}`}
          style={
            interval === 'hourly'
              ? { width: `${plotW}px`, minWidth: `${plotW}px` }
              : undefined
          }
        >
          <div className="forecast__line-layer" aria-hidden="true">
            <svg
              className="forecast__line-svg"
              viewBox={`0 0 ${plotW} ${TRACK_H}`}
              width={plotW}
              height={TRACK_H}
              preserveAspectRatio="none"
            >
              <path className="forecast__line-path" d={path} />
              {linePoints.map((p, i) => (
                <circle
                  key={chart.bars[i]?.key ?? i}
                  className="forecast__line-dot"
                  cx={p.x}
                  cy={p.y}
                  r={interval === 'hourly' ? 3 : 4}
                />
              ))}
            </svg>
          </div>

          <div className={`forecast__chart forecast__chart--${interval}`}>
            {chart.bars.map((bar) => {
              const meta = weatherMeta(bar.code)
              return (
                <button
                  key={bar.key}
                  type="button"
                  className={`forecast__col ${bar.active ? 'is-active' : ''} ${
                    bar.dayLabel ? 'forecast__col--day-start' : ''
                  }`}
                  onClick={bar.onSelect}
                  aria-pressed={bar.active}
                >
                  {bar.dayLabel ? (
                    <span className="forecast__day">{bar.dayLabel}</span>
                  ) : (
                    <span className="forecast__day forecast__day--spacer" aria-hidden="true">
                      &nbsp;
                    </span>
                  )}
                  <span className="forecast__value">{bar.value}</span>
                  <span className="forecast__bar-track" aria-hidden="true">
                    {typeof bar.lowMark === 'number' ? (
                      <span
                        className="forecast__range"
                        style={{
                          bottom: `${bar.lowMark}%`,
                          height: `${Math.max(bar.height - bar.lowMark, 8)}%`,
                        }}
                      />
                    ) : (
                      <span
                        className="forecast__bar"
                        style={{ height: `${bar.height}%` }}
                      />
                    )}
                  </span>
                  <span className="forecast__icon" aria-hidden="true">
                    {meta.icon}
                  </span>
                  <span className="forecast__label">{bar.label}</span>
                  <span className="forecast__precip">
                    {formatPercent(bar.precip)} rain
                  </span>
                  {bar.lowValue ? (
                    <span className="forecast__low">{bar.lowValue}</span>
                  ) : null}
                </button>
              )
            })}
          </div>
        </div>
      </div>

      {detail ? <ForecastDetail detail={detail} timezone={weather.timezone} /> : null}
    </section>
  )
}

function ForecastDetail({
  detail,
  timezone,
}: {
  detail: Selected
  timezone: string
}) {
  if (detail.kind === 'hourly') {
    const { point } = detail
    const meta = weatherMeta(point.weatherCode)
    return (
      <div className="forecast__detail">
        <h3>
          {formatWeekday(point.time, timezone)} · {formatHour(point.time, timezone)}
        </h3>
        <p>
          {meta.icon} {meta.label} · {formatTemp(point.temperature)} (feels{' '}
          {formatTemp(point.apparentTemperature)})
        </p>
        <ul>
          <li>Rain chance {formatPercent(point.precipitationProbability)}</li>
          <li>Precip {formatPrecip(point.precipitation)}</li>
          <li>Humidity {formatPercent(point.humidity)}</li>
          <li>Wind {Math.round(point.windSpeed)} km/h</li>
          <li>Cloud cover {formatPercent(point.cloudCover)}</li>
        </ul>
      </div>
    )
  }

  const { point } = detail
  const meta = weatherMeta(point.weatherCode)
  return (
    <div className="forecast__detail">
      <h3>{formatWeekday(point.date, timezone)}</h3>
      <p>
        {meta.icon} {meta.label} · High {formatTemp(point.tempMax)} / Low{' '}
        {formatTemp(point.tempMin)}
      </p>
      <ul>
        <li>Feels {formatTemp(point.apparentMax)} / {formatTemp(point.apparentMin)}</li>
        <li>Rain chance {formatPercent(point.precipProbabilityMax)}</li>
        <li>Precip total {formatPrecip(point.precipSum)}</li>
        <li>Wind max {Math.round(point.windSpeedMax)} km/h</li>
        <li>UV index max {point.uvIndexMax.toFixed(1)}</li>
        <li>
          Sunrise{' '}
          {point.sunrise
            ? new Intl.DateTimeFormat(undefined, {
                hour: 'numeric',
                minute: '2-digit',
                timeZone: timezone,
              }).format(new Date(point.sunrise))
            : '—'}{' '}
          · Sunset{' '}
          {point.sunset
            ? new Intl.DateTimeFormat(undefined, {
                hour: 'numeric',
                minute: '2-digit',
                timeZone: timezone,
              }).format(new Date(point.sunset))
            : '—'}
        </li>
      </ul>
    </div>
  )
}
