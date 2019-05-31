This folder contains a Dockerfile defining a docker image that can be used
for the pixel-by-pixel image tests, which require a very stable and reproducible
environment. To build, use e.g.::

    docker build . -t aperiosoftware/aas-timeseries-image-tests:1.1

with the version number updated as necessary. Then publish with::

    docker push aperiosoftware/aas-timeseries-image-tests:1.1
