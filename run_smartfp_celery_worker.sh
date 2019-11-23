#!/bin/bash

source activate rdkit
celery -A smartfp_tasks worker -l info -c 1