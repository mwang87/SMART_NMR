#!/bin/bash

export LC_ALL=C.UTF-8 && celery -A smartclassic_tasks worker -l info -c 1