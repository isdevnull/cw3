#!/bin/bash
DATA=./data/moskva.geojson
if [ -f "$DATA" ]; then
    echo "$DATA has been already downloaded!"
else 
    echo "$DATA does not exist. Downloading..."
		mkdir ./data
		wget https://dtp-stat.ru/media/opendata/moskva.geojson -P ./data/	
fi
