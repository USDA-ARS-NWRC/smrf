import numpy as np
import csv
from smrf import ipw

def read_metadata(mFile, dem):
    """
    Read the metadata csv file
    Args:
        mFile: metadata file
        dem: dem IPW file, if co-location of stations is required

    Returns:
        metadata: metadata array
        dem: opened IPW file
    """

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
    """
    Args:
        csvFile: csv file to read
    Returns:
        data: data from csv file
    """

#     print('Reading data file...')

    data = []
    if csvFile:
        f = open(csvFile,'rU')

        for row in csv.DictReader(f):
            data.append(row)
        f.close()

    return data
