#!/bin/bash

pgrep redis-server || redis-server &
celery -A "server.worker.worker" worker -c 4
