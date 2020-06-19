FROM ubuntu:18.04

ARG REQUIREMENTS=''

####################################################
# System requirements
####################################################

RUN apt-get update -y \
    && apt-get install -y --no-install-recommends libblas-dev \
    gcc \
    git \
    liblapack-dev \
    libatlas-base-dev \
    libssl-dev \
    libyaml-dev \
    libhdf5-serial-dev \
    python3-dev \
    python3-pip \
    curl \
    libeccodes-tools \
    ncdu \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get autoremove -y curl

####################################################
# SMRF
####################################################

COPY . / /code/smrf/

RUN mkdir /data \
    && cd /code/smrf \
    && python3 -m pip install --no-cache-dir --upgrade pip \
    && python3 -m pip install --no-cache-dir setuptools wheel \
    && python3 -m pip install --no-cache-dir -r /code/smrf/requirements${REQUIREMENTS}.txt \
    && python3 setup.py bdist_wheel \
    && python3 setup.py build_ext --inplace \
    && python3 setup.py install \
    # Can delete /code/smrf
    && apt-get autoremove -y gcc git

####################################################
# Create a shared data volume
####################################################

VOLUME /data
WORKDIR /data

COPY ./docker-entrypoint.sh /
RUN chmod +x /docker-entrypoint.sh
ENTRYPOINT ["/docker-entrypoint.sh"]
CMD ["/bin/bash"]
