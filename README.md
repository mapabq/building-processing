# Albuquerque OpenStreetMap Building import processing

## Overview

a Python >=3.6 script for processing Microsoft buildings footprints for bulk import into OpenStreetMap. 

### Methodology

Buildings are grouped in census tracts by census blocks if the census block does not already contain OpenStreetMap user contributions of buildings where ``` building="yes" ``` (as of February 11 2019). Current OSM building data is held in the [abq_building.geojson](./data/abq_building.geojson) file. Census blocks are held in the [blocks_wgs84.geojson](./data/blocks_wgs84.geojson) file. The Microsoft building footprint data for New Mexico can be downloaded [here](https://usbuildingdata.blob.core.windows.net/usbuildings-v1-1/NewMexico.zip). 


### C/C++ dependencies

* [libspatialindex](http://libspatialindex.github.io/)
* [libffi](https://github.com/libffi/libffi)
* [yajl](https://github.com/lloyd/yajl)

### Python

Python dependencies are managed with [pipenv](https://pipenv.readthedocs.io/en/latest/) after cloning the repo run:
```py
pipenv install
```

[libaries used](./Pipfile)

Code is formatted with [black](https://github.com/ambv/black)

### Docker  
A Dockerfile is provided for running the script in a container to keep host dependencies clean, this is probably the easiest way to run the script. Requires a volume argument to save data on host system.
```
git clone 
cd abq-buildings-process
docker build . -t mapabq-building-split
docker run -v /path/to/out/folder:/out mapabq-building-split
```

