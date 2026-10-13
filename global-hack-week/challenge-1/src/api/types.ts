export type Place = {
  id: string
  name: string
  latitude: number
  longitude: number
  admin1?: string
  country?: string
  timezone?: string
  source: 'geo' | 'search'
}

export type CurrentWeather = {
  time: string
  temperature: number
  apparentTemperature: number
  humidity: number
  weatherCode: number
  cloudCover: number
  pressureMsl: number
  windSpeed: number
  windDirection: number
  windGusts: number
  precipitation: number
  isDay: boolean
}

export type HourlyPoint = {
  time: string
  temperature: number
  apparentTemperature: number
  humidity: number
  precipitationProbability: number
  precipitation: number
  weatherCode: number
  windSpeed: number
  cloudCover: number
}

export type DailyPoint = {
  date: string
  weatherCode: number
  tempMax: number
  tempMin: number
  apparentMax: number
  apparentMin: number
  precipSum: number
  precipProbabilityMax: number
  windSpeedMax: number
  uvIndexMax: number
  sunrise: string
  sunset: string
}

export type WeatherBundle = {
  latitude: number
  longitude: number
  timezone: string
  current: CurrentWeather
  hourly: HourlyPoint[]
  daily: DailyPoint[]
}
