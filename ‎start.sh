#!/bin/bash

cd taxi_bot
python manage.py migrate --noinput
python manage.py collectstatic --noinput
gunicorn exam_app.wsgi:application --bind 0.0.0.0:8000
