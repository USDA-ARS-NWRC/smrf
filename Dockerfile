# SMRF is built on the IPW
FROM usdaarsnwrc/ipw:latest

MAINTAINER Scott Havens <scott.havens@ars.usda.gov>

####################################################
# System requirements
####################################################

RUN apt-get update -y \
    && apt-get install -y --no-install-recommends libblas-dev \
    git \
    liblapack-dev \
    libatlas-base-dev \
    libffi-dev \
    libssl-dev \
    gfortran \
    libyaml-dev \
    libfreetype6-dev \
    libpng-dev \
    libhdf5-serial-dev \
    python3-dev \
    python3-pip \
    python3-tk \
    curl \
    libgrib-api-dev \
    && cd /code \
    && curl -L https://github.com/USDA-ARS-NWRC/weather_forecast_retrieval/archive/master.tar.gz | tar xz \
    && rm -rf /var/lib/apt/lists/* \
    && apt remove -y curl \
    && apt autoremove -y

####################################################
# SMRF
####################################################

COPY . / /code/smrf/

RUN mkdir /data \
    && cd /code/smrf \
    && python3 -m pip install --upgrade pip \
    && python3 -m pip install setuptools wheel \
    && python3 -m pip install -r /code/smrf/requirements.txt \
    && python3 setup.py build_ext --inplace \
    && python3 setup.py install \
    && python3 -m compileall . \
    && cd /code/weather_forecast_retrieval-master \
    && python3 -m pip install pyproj==1.9.5.1 \
    && python3 -m pip install -r requirements_dev.txt \
    && python3 setup.py install \
    && rm -r /root/.cache/pip

####################################################
# Create a shared data volume
####################################################

VOLUME /data
WORKDIR /data

COPY ./docker-entrypoint.sh /
RUN chmod +x /docker-entrypoint.sh
ENTRYPOINT ["/docker-entrypoint.sh"]
CMD ["/bin/bash"]
