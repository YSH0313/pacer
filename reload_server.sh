#!/bin/bash
#docker stop $(docker ps -q --filter ancestor=pacer_pacer)
docker rm -f $(docker ps -q --filter ancestor=pacer_pacer)
docker rmi --force $(docker images | grep pacer_pacer | awk '{print $3}')
docker-compose up -d
