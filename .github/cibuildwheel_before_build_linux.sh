#/usr/bin/env bash

# Eccodes is only for CentOS 7 so the manylinux2010 image does not work
yum install -y eccodes

python3 -m pip install -r requirements.txt
