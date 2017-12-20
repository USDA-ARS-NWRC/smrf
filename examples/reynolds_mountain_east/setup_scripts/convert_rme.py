import pandas as pd
from datetime import datetime
from subprocess import check_output
import os

"""
Script for converting the 25 year RME dataset to be ran with SMRF
"""

out_dir = './station_data/'
in_dir = './raw_data/'
#met_data
#By the cabin
rme_176_met = {'primary_id':'RME_176',
           "utm_x": 519611,
           "utm_y": 4768129,
           "latitude": 43.065611,
           "longitude":-116.75914250157894,
           "zone": 11,
           "elevation": 2093}
#In the grove
rmesp_met = {'primary_id': 'RMESP',
         "utm_x": 519976,
         "utm_y": 4768323,
         "latitude": 43.067348,
         "longitude": -116.75465273389469,
         "zone": 11,
         "elevation": 2056}

#Dictionary for mapping the column names to the required names
met_data_map = {'air_temp':'Ta',
                'wind_speed':'ws',
                'wind_direction':'wd',
                'solar':'Si',
                'dew_point':'DPT',
                'precip':'SH'}

#Dictionary for holding all the data frames
data = {}
raw_data = {}
raw_precip = {}

#Get raw files in pandas dataframes using tab separated
print("Creating opening raw datasets...")
raw_data["RME_176"] = pd.read_csv(in_dir + 'met_exposed.txt', sep = '\t')
raw_data["RMESP"] = pd.read_csv(in_dir + 'met_sheltered.txt', sep = '\t')
raw_precip["RME_176"] = pd.read_csv(in_dir + 'ppt_exposed.txt', sep = '\t')
raw_precip['RMESP'] = pd.read_csv(in_dir + 'ppt_sheltered.txt', sep = '\t')

#Metadata setup
rme_176 = pd.Series(rme_176_met)
rmesp = pd.Series(rmesp_met)
data['metadata'] = pd.DataFrame([rme_176,rmesp])
data['metadata'].set_index('primary_id',inplace=True)
data['metadata'].to_csv(out_dir + 'metadata.csv')

#Formulate the datatime index
d = []
print("Creating datetime index...")

for i,row in raw_data["RME_176"].iterrows():
    d.append(datetime(year=int(row['Yr']),month = int(row['M']), day = int(row['D']), hour = int(row['H'])))

#Create output DF
print("Generating Dataframes...")
for k in ['precip','solar','vapor_pressure','wind_direction','wind_speed','air_temp','dew_point']:
    if k == 'precip':
        ind = raw_precip['RME_176'].index
    else:
        ind = raw_data['RME_176'].index

    data[k] = pd.DataFrame(columns=["date_time","RME_176","RMESP"], index = ind,dtype=float)

#Assign met data into individual df with stations as the column names
for var,m_var in met_data_map.items():
    print("Assigning {0} data using {1}...".format(var,m_var))
    if var == 'precip':
        sta_data = raw_precip
    else:
        sta_data = raw_data

    for sta,met_df in sta_data.items():
        try:
            if var=='dew_point':
                with open('./vp.txt','w+') as f:
                    f.writelines([str(i)+'\n' for i in met_df[m_var].values])
                    f.close()

                output = check_output('satvp < ./vp.txt',shell=True)
                data['vapor_pressure'][sta] = [float(s) for s in output.split('\n')[0:-1]]
                os.remove('./vp.txt')
            else:
                data[var][sta] = met_df[m_var].values
        except Exception as e:
            print e
            print("Missing {0} data for station {1}".format(var,sta))
    if var == 'dew_point':
        var = 'vapor_pressure'
    print("Writing {0}...".format(var))
    data[var]['date_time'] = d
    data[var].set_index('date_time', drop=True, inplace=True)
    d_out = data[var].truncate(before = datetime(1998,01,01,0,0), after = datetime(1998,02,01,0,0))
    d_out.to_csv(out_dir + '{0}.csv'.format(var))
