# SMRF is built on the IPW
FROM scotthavens/ipw:latest

MAINTAINER Scott Havens <scott.havens@ars.usda.gov>

####################################################
# System requirements
####################################################

RUN apt-get update -y && \
    apt-get install -y libblas-dev \
	liblapack-dev \
	libatlas-base-dev \
	libffi-dev \
	libssl-dev \
	libyaml-dev \
	libfreetype6-dev \
	libpng-dev \
	libhdf5-serial-dev \
	python2.7-dev \
	python-pip \
        python-tk

####################################################
# SMRF
####################################################

RUN mkdir -p /code/smrf && mkdir /data
COPY . / /code/smrf/

RUN cd /code/smrf \
    && pip install -r /code/smrf/requirements.txt \
    && python setup.py install

####################################################
# Create a shared data volume
####################################################

VOLUME /data
WORKDIR /data

ENTRYPOINT ["/bin/bash"]
#CMD ["run_smrf", "/code/smrf/test_data/testConfig.ini"]








