#!/bin/bash
set -e

if [ "$1" = "test" ]; then
    echo "Run SMRF docker test"
    cd /code/smrf
    coverage run --source smrf setup.py test
    
    coverage report --fail-under=70
        
    if [ $? = 2]; then
    	exit 1
    fi
    
    coveralls
    exit 0

fi

exec "$@"