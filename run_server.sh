#!/bin/bash

source activate rdkit
gunicorn -w 8 -b 0.0.0.0:5000 --timeout 3600 --keep-alive 3600 main:app --access-logfile /app/logs/access.log
#python ./main.py
