FROM python:3.6-alpine

RUN apk add zip curl g++ make libffi-dev git cmake
RUN apk add --repository http://dl-cdn.alpinelinux.org/alpine/edge/testing geos-dev
RUN git clone git://github.com/lloyd/yajl && \
    cd yajl && \
    ./configure && \
    make && \
    make install
RUN curl -L http://download.osgeo.org/libspatialindex/spatialindex-src-1.8.5.tar.gz | tar xz && \
    cd spatialindex-src-1.8.5&& \
    ./configure && \
    make && \
    make install && \
    ldconfig /
ADD main.py /
ADD /data /data
RUN wget https://usbuildingdata.blob.core.windows.net/usbuildings-v1-1/NewMexico.zip  && \
    unzip NewMexico.zip -d /data/
ADD requirements.txt /
VOLUME /out
RUN pip install -r requirements.txt
CMD ["python", "-u", "main.py"]
