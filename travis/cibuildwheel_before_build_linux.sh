# Eccodes doesn't exist for CentOS 6, fallback to the grip api
# yum install -y grib_api

# Eccodes doesn't support CentOS 6 so force it
curl -o eccodes-2.14.1-1.el7.x86_64.rpm https://download-ib01.fedoraproject.org/pub/epel/7/x86_64/Packages/e/eccodes-2.14.1-1.el7.x86_64.rpm
rpm -ivh --nodeps eccodes-2.14.1-1.el7.x86_64.rpm

python3 -m pip install -r requirements.txt
python3 -m pip install pyeccodes
