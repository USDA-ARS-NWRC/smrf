import numpy as np
import datetime
import pandas as pd
from datetime import datetime, timedelta
from smrf.data import mysql_data
from netCDF4 import Dataset
start = datetime(2017,10,1,0,0)
end = datetime(2017,10,1,23,0)

Boise_utm_n = 4829843.53
Boise_utm_e = 563336.71

#Elevation trend
multiplier = 1.50

span = 5000
half_width = span/2
station_data = {'precip': {'min':0,'max':50},
        'air_temp': {'min':-5,'max':10},
        'vapor_pressure': {'min':500,'max':1000},
        'wind_speed': {'min':0,'max':25},
        'wind_direction': {'min':0,'max':45},
        'cloud_factor': {'min':0.2,'max':0.5},
        }

stations = ['BL','BR','UL','UR']
#Setup station data to be centered on boise
c = ["primary_id",
    "secondary_id",
    "station_name",
    "state",
    "country",
    "latitude",
    "longitude",
    "elevation",
    "mesowest_network_id",
    "network_name",
    "status",
    "primary_provider_id",
    "primary_provider",
    "secondary_provider_id",
    "secondary_provider",
    "tertiary_provider_id",
    "tertiary_provider",
    "wims_id",
    "utm_x",
    "utm_y"]
#Made up stations names
station_data["metadata"] = pd.DataFrame(columns = c, index = stations)

#Get the timesetps correctly in the time zone
dates = mysql_data.date_range(start, end,
                          timedelta(minutes=60.0))

blank = pd.DataFrame(columns = stations, index = dates)
blank.index.to_datetime()


for col in station_data['metadata']:
    if col == "primary_id":
        station_data['metadata'][col] = stations
    elif col == "secondary_id":
        station_data['metadata'][col] = ['Bottom Left corner',
                                         'Bottom Right corner',
                                         'Upper left corner',
                                         'Upper right mid slope']
    elif col == "utm_x":
        station_data['metadata'][col] = [Boise_utm_e - half_width,
                                         Boise_utm_e + half_width,
                                         Boise_utm_e - half_width,
                                         Boise_utm_e + 0.5*half_width]
    elif col == "utm_y":
        station_data['metadata'][col] = [Boise_utm_n - half_width,
                                         Boise_utm_n - half_width,
                                         Boise_utm_n + half_width,
                                         Boise_utm_n + 0.5*half_width]

    elif col == "elevation":
        d = Dataset('topo.nc','r')
        dem = d.variables['dem']
        station_data['metadata'][col] = [dem[0,0], dem[-1,0],dem[0,-1],dem[38,38]]

    else:
        station_data['metadata'][col] = [np.NaN for i in stations]

elev = np.array(dem).max()

# Assign Station Data
for k,v in station_data.items():
    if k != "metadata":
        data = blank.copy()

        f = np.linspace(v["min"],v['max'],len(dates))

        for sta in blank.columns:
            data[sta] = f
        #Coherence in trends
        if k in ['air_temp','vapor_pressure']:
            m = 1/multiplier
        else:
            m = multiplier

        trend = m/elev

        data = data.mul(trend*station_data['metadata']['elevation']+1)
        print k
        print data
        data.to_csv(k+".csv",date_format="%m/%d/%y %H:%M",index_label='date_time')

station_data['metadata'].to_csv('metadata.csv')

d.close()

#metadata
#air_temp
#vapor_pressure
#precip
#wind_speed
#wind_direction
#cloud_factor
