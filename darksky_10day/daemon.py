import datetime
import json
import os

from dateutil import tz
import flask
from forecastiopy import (ForecastIO, FIOHourly)

LAT=float(os.environ.get('LAT', '0.0'))
LON=float(os.environ.get('LON', '0.0'))
API_KEY=os.environ.get('API_KEY', '')
FORECAST_CACHE_FILE=os.environ.get('FORECAST_CACHE_FILE', '/tmp/forecast.json')
FORECAST_CACHE_MINUTES=int(os.environ.get('FORECAST_CACHE_MINUTES', '30'))
FLASK_STATIC_FOLDER=os.environ.get('FLASK_STATIC_FOLDER', 'static')

APP = flask.Flask(__name__, static_folder=FLASK_STATIC_FOLDER)


@APP.route("/")
def index():
    return APP.send_static_file('index.html')


@APP.route("/weather")
def weather():
    return flask.jsonify(get_forecast())


def get_forecast():
    now = datetime.datetime.now()

    if os.path.isfile(FORECAST_CACHE_FILE):
        with open(FORECAST_CACHE_FILE, 'r') as fp:
            forecast = json.load(fp)
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
        'wind_gust': []
    }

    today = datetime.datetime(now.year, now.month, now.day)
    for i in range(0, 10):
        time = (today + datetime.timedelta(days=i)).isoformat()
        FIO = ForecastIO.ForecastIO(API_KEY, latitude=LAT, longitude=LON, time=time)
        hourly = FIOHourly.FIOHourly(FIO)
        for h in range(0, hourly.hours()):
            hour = hourly.get_hour(h)
            now = datetime.datetime.utcnow()
            raw_utc = datetime.datetime.fromtimestamp(hour['time'])
            if raw_utc < now - datetime.timedelta(hours=1):
                continue
            utc = raw_utc.replace(tzinfo=tz.gettz('UTC'))
            eastern = utc.astimezone(tz.gettz('America/New_York'))
            fmttime = eastern.strftime("%-d %a %-I:%M %p")
            if eastern.hour == 0 and eastern.minute == 0:
                forecast['days'].append(eastern.strftime("%-d %a"))
            forecast['time'].append(fmttime)
            forecast['temperature'].append(int(hour['temperature']))
            forecast['precipitation'].append(int(hour['precipProbability'] * 100.0))
            forecast['humidity'].append(int(hour['humidity'] * 100.0))
            forecast['pressure'].append(round(hour['pressure'] / 33.864, 2))
            forecast['wind_speed'].append(int(hour['windSpeed']))
            forecast['wind_gust'].append(int(hour.get('windGust', 0)))

    with open(FORECAST_CACHE_FILE, 'w') as fp:
        json.dump(forecast, fp)

    return forecast


if __name__ == '__main__':
    APP.config['DEBUG'] = True
    APP.run()