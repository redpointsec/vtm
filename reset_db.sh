#!/bin/bash
rm db.sqlite3 &> /dev/null
python3 manage.py migrate --fake-initial
python3 manage.py loaddata taskManager/fixtures/*
