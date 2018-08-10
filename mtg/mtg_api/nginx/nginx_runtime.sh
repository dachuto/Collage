#!/usr/bin/env bash
mkdir -p logs
touch logs/access.log
> logs/access.log
touch logs/error.log
> logs/error.log
./sbin/nginx -s stop
./sbin/nginx

