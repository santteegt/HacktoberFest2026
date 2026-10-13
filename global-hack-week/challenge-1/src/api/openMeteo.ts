import type { DailyPoint, HourlyPoint, WeatherBundle } from './types'

type ForecastResponse = {
  latitude: number
  longitude: number
  timezone: string
  current: Record<string, number | string>
  hourly: Record<string, Array<number | string | null>>
  daily: Record<string, Array<number | string | null>>
}

function num(value: number | string | null | undefined, fallback = 0): number {
  if (value == null || value === '') return fallback
  const n = typeof value === 'number' ? value : Number(value)
  return Number.isFinite(n) ? n : fallback
}

export async function fetchWeather(
  latitude: number,
  longitude: number,
  signal?: AbortSignal,
): Promise<WeatherBundle> {
  const url = new URL('https://api.open-meteo.com/v1/forecast')
  url.searchParams.set('latitude', String(latitude))
  url.searchParams.set('longitude', String(longitude))
  url.searchParams.set('timezone', 'auto')
  url.searchParams.set('forecast_days', '5')
  url.searchParams.set(
    'current',
    [
      'temperature_2m',
      'relative_humidity_2m',
      'apparent_temperature',
      'is_day',
      'precipitation',
      'weather_code',
      'cloud_cover',
      'pressure_msl',
      'wind_speed_10m',
      'wind_direction_10m',
      'wind_gusts_10m',
    ].join(','),
  )
  url.searchParams.set(
    'hourly',
    [
      'temperature_2m',
      'relative_humidity_2m',
      'apparent_temperature',
      'precipitation_probability',
      'precipitation',
      'weather_code',
      'cloud_cover',
      'wind_speed_10m',
    ].join(','),
  )
  url.searchParams.set(
    'daily',
    [
      'weather_code',
      'temperature_2m_max',
      'temperature_2m_min',
      'apparent_temperature_max',
      'apparent_temperature_min',
      'sunrise',
      'sunset',
      'uv_index_max',
      'precipitation_sum',
      'precipitation_probability_max',
      'wind_speed_10m_max',
    ].join(','),
  )

  const res = await fetch(url, { signal })
  if (!res.ok) throw new Error(`Weather fetch failed (${res.status})`)
  const data = (await res.json()) as ForecastResponse

  const times = data.hourly.time as string[]
  const hourly: HourlyPoint[] = times.map((time, i) => ({
    time,
    temperature: num(data.hourly.temperature_2m?.[i]),
    apparentTemperature: num(data.hourly.apparent_temperature?.[i]),
    humidity: num(data.hourly.relative_humidity_2m?.[i]),
    precipitationProbability: num(data.hourly.precipitation_probability?.[i]),
    precipitation: num(data.hourly.precipitation?.[i]),
    weatherCode: num(data.hourly.weather_code?.[i]),
    windSpeed: num(data.hourly.wind_speed_10m?.[i]),
    cloudCover: num(data.hourly.cloud_cover?.[i]),
  }))

  const dates = data.daily.time as string[]
  const daily: DailyPoint[] = dates.map((date, i) => ({
    date,
    weatherCode: num(data.daily.weather_code?.[i]),
    tempMax: num(data.daily.temperature_2m_max?.[i]),
    tempMin: num(data.daily.temperature_2m_min?.[i]),
    apparentMax: num(data.daily.apparent_temperature_max?.[i]),
    apparentMin: num(data.daily.apparent_temperature_min?.[i]),
    precipSum: num(data.daily.precipitation_sum?.[i]),
    precipProbabilityMax: num(data.daily.precipitation_probability_max?.[i]),
    windSpeedMax: num(data.daily.wind_speed_10m_max?.[i]),
    uvIndexMax: num(data.daily.uv_index_max?.[i]),
    sunrise: String(data.daily.sunrise?.[i] ?? ''),
    sunset: String(data.daily.sunset?.[i] ?? ''),
  }))

  return {
    latitude: data.latitude,
    longitude: data.longitude,
    timezone: data.timezone,
    current: {
      time: String(data.current.time),
      temperature: num(data.current.temperature_2m),
      apparentTemperature: num(data.current.apparent_temperature),
      humidity: num(data.current.relative_humidity_2m),
      weatherCode: num(data.current.weather_code),
      cloudCover: num(data.current.cloud_cover),
      pressureMsl: num(data.current.pressure_msl),
      windSpeed: num(data.current.wind_speed_10m),
      windDirection: num(data.current.wind_direction_10m),
      windGusts: num(data.current.wind_gusts_10m),
      precipitation: num(data.current.precipitation),
      isDay: num(data.current.is_day) === 1,
    },
    hourly,
    daily,
  }
}
