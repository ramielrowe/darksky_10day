FROM python:3.7-alpine

RUN pip install python-dateutil flask forecastiopy gunicorn redis requests

ADD . /src
RUN cd /src && python setup.py install && pip install gunicorn

CMD ["gunicorn", "darksky_10day.daemon:APP", "-b", ":8000"]
