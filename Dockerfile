# SMRF is built on a ubuntu 16.04 image
FROM ubuntu:16.04

MAINTAINER Scott Havens <scott.havens@ars.usda.gov>

# Add user
RUN useradd smrf

# create a working directory
RUN mkdir -p /code
RUN chown -R smrf:smrf /code
WORKDIR /code

####################################################
# System requirements
####################################################

RUN apt-get update -y

RUN apt-get install -y build-essential \
	wget \
	libblas-dev \
	liblapack-dev \
	libatlas-base-dev \
	gfortran \
	libffi-dev \
	libssl-dev \
	libyaml-dev \
	libfreetype6-dev \
	libpng-dev \
	man \
	libhdf5-serial-dev \
	libnetcdf-dev \
	netcdf-bin \
	netcdf-doc \
	python2.7-dev \
	python-pip \
	python-setuptools

####################################################
# IPW
####################################################

# add the bash profile so that the paths get set
COPY bash_profile /home/smrf/.bash_profile
#RUN more /home/ipw/.bash_profile
#RUN chown -R smrf: /home/smrf/ipw

#RUN echo "IPW=/code/ipw-2.3.0" >> /.bash_profile
#RUN echo "export IPW" >> /.bash_profile
#RUN echo "PATH=`$IPW/path user`:$PATH" >> /.bash_profile
#RUN echo "MANPATH=`$IPW/path man`:$MANPATH" >> /.bash_profile
#RUN echo "export WORKDIR=/usr/local/tmp" >> /.bash_profile


# create the IPW environment variables for compiling
ENV IPW=/code/ipw-v2.3.0
ENV WORKDIR=/tmp

# lets compile IPW
WORKDIR /code
RUN cd /code \
	&& mkdir ipw-v2.3.0 \
	&& wget https://github.com/USDA-ARS-NWRC/ipw/archive/v2.3.0.tar.gz \
    && tar -xf /code/v2.3.0.tar.gz -C /code/ipw-v2.3.0 \
    && cd /code/ipw-v2.3.0 \
    && pwd \
	&& ./code/ipw-v2.3.0/configure \
	&& make \
	&& make install
    

RUN 
	
#RUN cp $IPW/bin/* /usr/local/bin



####################################################
# SMRF
####################################################

#COPY /smrf/ /code/smrf

# get the SciPy Stack
#RUN apt-get install -y python-numpy \
#	python-scipy \
#	python-matplotlib \
#	cython \
#	python-pandas	

# update the version for some of the core packages
#RUN easy_install cython==0.23.4
#RUN easy_install numpy==1.11.0
#RUN easy_install scipy==0.17.0
#RUN easy_install pandas==0.17.1

#RUN pip install -r /code/smrf/requirements.txt

#WORKDIR /code/smrf
#RUN python setup.py build_ext --inplace
#RUN python setup.py install



####################################################
# Create a shared data volume
####################################################

# We need to create an empty file, otherwise the volume will
# belong to root.
# This is probably a Docker bug.
RUN mkdir /data
RUN touch /data/placeholder
RUN chown -R smrf:smrf /data
RUN chmod 755 -R /data
VOLUME /data



RUN chown -R smrf: /home/smrf
USER smrf
WORKDIR /data

# ENTRYPOINT ["/bin/bash", "--login"]
CMD ["python"]








