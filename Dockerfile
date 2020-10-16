# Multi-stage SMRF docker build
FROM python:3.6-slim-buster as builder

RUN mkdir /install \
    && mkdir /build \
    && apt-get update -y \
    && apt-get install -y --no-install-recommends \
    gcc \
    git \
    libssl-dev \
    libyaml-dev \
    libhdf5-serial-dev \
    curl \
    libeccodes-tools \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get autoremove -y curl

COPY . /build
WORKDIR /build

RUN python3 -m pip install --no-cache-dir --upgrade pip \
    && python3 -m pip install --no-cache-dir setuptools wheel \
    && python3 -m pip install --no-cache-dir --user .[tests] \
    && python3 setup.py bdist_wheel \
    && python3 setup.py build_ext --inplace

##############################################
# main image
##############################################
FROM python:3.6-slim-buster

COPY --from=builder /root/.local /usr/local

RUN apt-get update -y \
    && apt-get install -y --no-install-recommends libeccodes-tools \
    && python3 -m pip install --no-cache-dir nose \
    && nosetests -vv --exe smrf \
    && python3 -m pip uninstall -y nose \
    && rm -rf /var/lib/apt/lists/*

# Create a shared data volume
VOLUME /data
WORKDIR /data

CMD ["/bin/bash"]
