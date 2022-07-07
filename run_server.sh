#!/bin/bash

source activate rdkit
gunicorn -w 2 --threads 2 -b 0.0.0.0:5000 --timeout 120 --keep-alive 120 main:app --access-logfile /app/logs/access.log
#python ./main.py
