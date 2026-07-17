#!/bin/sh

# Start cron daemon
cron

# Start Nginx in foreground
nginx -g "daemon off;"
