#!/bin/bash

celery -A smartclassic_tasks worker -l info -c 1