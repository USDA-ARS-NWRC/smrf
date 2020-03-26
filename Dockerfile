# SMRF is built on the IPW
FROM usdaarsnwrc/ipw:latest

MAINTAINER Scott Havens <scott.havens@ars.usda.gov>

ARG REQUIREMENTS=''

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
    libeccodes-dev \
    libeccodes-tools \
    && rm -rf /var/lib/apt/lists/* \
    && apt autoremove -y curl

####################################################
# SMRF
####################################################

COPY . / /code/smrf/

RUN mkdir /data \
    && cd /code/smrf \
    && python3 -m pip install --no-cache-dir --upgrade pip \
    && python3 -m pip install --no-cache-dir setuptools wheel \
    && python3 -m pip install --no-cache-dir -r /code/smrf/requirements${REQUIREMENTS}.txt \
    && python3 setup.py build_ext --inplace \
    && python3 setup.py install \
    # && rm -r /root/.cache/pip \
    && apt-get autoremove -y gcc

####################################################
# Create a shared data volume
####################################################

VOLUME /data
WORKDIR /data

COPY ./docker-entrypoint.sh /
RUN chmod +x /docker-entrypoint.sh
ENTRYPOINT ["/docker-entrypoint.sh"]
CMD ["/bin/bash"]
