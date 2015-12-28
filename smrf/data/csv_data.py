'''
Read in metadata and data from CSV files

20150810 Scott Havens
'''


import numpy as np
import os, csv
from smrf import ipw





def read_metadata(mFile, dem):
    '''
    Read the metadata csv file
    Args:
        mFile - metadata file
        dem - dem IPW file, if co-location of stations is required
        
    Out:
        metadata - metadata array
        dem - opened IPW file
    '''
    
    print('Reading metadata file...')
    f = open(mFile, 'rU')
    metadata = []
    
    dem = ipw.IPW(dem)

    for row in csv.DictReader(f):
        # determine pixel location of station
        row['X'] = float(row['X'])
        row['Y'] = float(row['Y'])
        
        row['xi'] = np.argmin(abs(row['X'] - dem.bands[0].x))
        row['yi'] = np.argmin(abs(row['Y'] - dem.bands[0].y))
        
        metadata.append(row)  
    f.close()

    return metadata, dem


def read_csv(csvFile):
    '''
    Args:
        csvFile - csv file to read
    Out:
        data - data from csv file
    '''
    
    print('Reading data file...')
    
    f = open(csvFile,'rU')
    data = []
    for row in csv.DictReader(f):
        data.append(row)
    f.close()
    
    return data