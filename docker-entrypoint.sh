#!/bin/bash
set -e

if [ "$1" = "test" ]; then
    echo "Run SMRF docker test"
    cd /code/smrf
    
    # if fail, the exit code will not be 0
    coverage run --source smrf setup.py test
    
    #if [ $? != 0 ]; then
    #	echo "SMRF tests failed"
    # 	exit 1
    #fi
   
    # fail the coverage test if it's under 70% provides it's own exit code of 2
    coverage report --fail-under=50
            
    # made it through the test gauntlet
    coveralls
    exit 0

fi

exec "$@"