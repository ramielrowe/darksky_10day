import datetime
import json
import os

from dateutil import tz
import flask
from forecastiopy import (ForecastIO, FIODaily, FIOHourly, FIOAlerts)
import redis

TZ_EASTERN = tz.gettz('America/New_York')

REDIS_HOST = os.environ.get('REDIS_HOST')
REDIS_PORT = int(os.environ.get('REDIS_PORT', '6379'))
REDIS_DB = int(os.environ.get('REDIS_PORT', '0'))
REDIS_PASSWORD = os.environ.get('REDIS_PASSWORD')

LAT = float(os.environ.get('LAT', '0.0'))
LON = float(os.environ.get('LON', '0.0'))
API_KEY = os.environ.get('API_KEY', '')
FORECAST_CACHE_MINUTES = int(os.environ.get('FORECAST_CACHE_MINUTES', '30'))
FORECAST_CACHE_RADIUS = float(os.environ.get('FORECAST_CACHE_RADIUS', '8'))
FLASK_STATIC_FOLDER = os.environ.get('FLASK_STATIC_FOLDER', 'static')

APP = flask.Flask(__name__, static_folder=FLASK_STATIC_FOLDER)

REDIS_CLIENT = None


def redis_client():
    global REDIS_CLIENT
    if not REDIS_CLIENT:
        REDIS_CLIENT = redis.Redis(host=REDIS_HOST,
                                   port=REDIS_PORT,
                                   db=REDIS_DB,
                                   password=REDIS_PASSWORD)
    return REDIS_CLIENT


@APP.route("/")
def index():
    return APP.send_static_file('index.html')


@APP.route("/weather")
def weather():
    return flask.jsonify(get_forecast(LAT, LON))


def utc_to_eastern(datetime):
    utc = datetime.replace(tzinfo=tz.UTC)
    return utc.astimezone(TZ_EASTERN)


def unix_to_eastern(timestamp):
    raw_utc = datetime.datetime.fromtimestamp(timestamp)
    return utc_to_eastern(raw_utc)


def get_forecast(lat, lon):
    now = utc_to_eastern(datetime.datetime.utcnow())

    forecasts = redis_client().georadius('forecast', lat, lon, FORECAST_CACHE_RADIUS, unit='km')
    if forecasts:
        forecast = forecasts[0]
        captured = datetime.datetime.fromisoformat(forecast['captured'])
        if captured > now - datetime.timedelta(minutes=FORECAST_CACHE_MINUTES):
            return forecast

    forecast = {
        'captured': now.isoformat(),
        'time': [],
        'days': [],
        'temperature': [],
        'precipitation': [],
        'humidity': [],
        'pressure': [],
        'wind_speed': [],
        'wind_gust': [],
        'daily': [],
        'alerts': [],
    }

    today = datetime.datetime(now.year, now.month, now.day, tzinfo=TZ_EASTERN)
    for i in range(0, 10):
        time = (today + datetime.timedelta(days=i)).isoformat()
        FIO = ForecastIO.ForecastIO(API_KEY, latitude=LAT, longitude=LON, time=time)

        hourly_precip_intense_accum = 0.0
        hourly = FIOHourly.FIOHourly(FIO)
        this_day = None
        for h in range(0, hourly.hours()):
            hour = hourly.get_hour(h)
            eastern = unix_to_eastern(hour['time'])
            fmttime = eastern.strftime("%-d %a %-I:%M %p")
            if eastern.hour == 0 and eastern.minute == 0:
                this_day = eastern.strftime("%-d %a")
            if eastern < now - datetime.timedelta(hours=1):
                continue
            forecast['time'].append(fmttime)
            forecast['temperature'].append(int(hour['temperature']))
            forecast['precipitation'].append(int(hour['precipProbability'] * 100.0))
            forecast['humidity'].append(int(hour['humidity'] * 100.0))
            forecast['pressure'].append(round(hour['pressure'] / 33.864, 2))
            forecast['wind_speed'].append(int(hour['windSpeed']))
            forecast['wind_gust'].append(int(hour.get('windGust', 0)))
            hourly_precip_intense_accum += hour['precipIntensity']

        daily = FIODaily.FIODaily(FIO)
        day = daily.get(0)
        daily_precip_accum = 0.0
        if 'precipAccumulation' in day:
            daily_precip_accum = round(day['precipAccumulation'], 1)

        if daily_precip_accum == 0.0:
            daily_precip_accum = hourly_precip_intense_accum

        forecast['daily'].append({
            'icon': day.get('icon', 'unknown'),
            'summary': day['summary'],
            'precip': {
                'probability': round(day.get('precipProbability', 0.0)*100),
                'accumulation': round(daily_precip_accum, 1),
                'type': day.get('precipType ', 'rain'),
            },
            'temp': {
                'low': day['temperatureLow'],
                'high': day['temperatureHigh'], 
                'apparentLow': day['apparentTemperatureLow'],
                'apparentHigh': day['apparentTemperatureHigh'], 
            }
        })

        if this_day is not None:
            forecast['days'].append(this_day)

    redis_client().geoadd('forecast', lat, lon, forecast)

    return forecast


if __name__ == '__main__':
    APP.config['DEBUG'] = True
    APP.run(host='0.0.0.0', port=8000)
