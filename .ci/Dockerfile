# This Dockerfile is used for the pixel-by-pixel tests for the aas-timeseries
# package - we use a docker image to ensure exact reproducibility over time.
# We don't install all dependencies for aas-timeseries here, just those that
# might matter for the rendering - e.g. we install PyQt because the Qt
# WebEngine rendering might change over time.

FROM ubuntu:18.04

ENV DEBIAN_FRONTEND=noninteractive
ENV DISPLAY=:99.0

# Install Python, git, and the dependencies for Qt
RUN apt-get update
RUN apt-get install -y xvfb git sudo \
                       python3 python3-dev python3-pip python3-wheel \
                       python3.7 python3.7-dev \
                       libgtk2.0-dev libgl1-mesa-glx libegl1-mesa libxrandr2 \
                       libxss1 libxcursor1 libxcomposite1 libasound2 libxi6 \
                       libxtst6 libnss3 libxslt1.1 libxkbcommon-x11-0

# Copy over xvfb script
COPY start-xvfb /usr/bin

# Install a more recent version of pip
RUN python3.6 -m pip install pip --upgrade
RUN python3.7 -m pip install pip --upgrade

# Install PyQt5
RUN python3.6 -m pip install PyQt5==5.12.2 PyQtWebEngine==5.12.1
RUN python3.7 -m pip install PyQt5==5.12.2 PyQtWebEngine==5.12.1

# Set up locale correctly
RUN apt-get install -y language-pack-en
ENV LANG en_US.UTF-8

# Set up user
RUN useradd -ms /bin/bash testuser
