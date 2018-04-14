#!/bin/bash
rm db.sqlite3 &> /dev/null
python manage.py migrate --fake-initial
python manage.py loaddata taskManager/fixtures/*
