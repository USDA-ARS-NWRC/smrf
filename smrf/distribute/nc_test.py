import pandas as pd
import xarray as xr
from matplotlib import pyplot as plt

def read_nc(fname):
    nc = netCDF4.Dataset(fname)
    p = nc.variables['precip']
    time = nc.variables['time']
    # jd = netCDF4.num2date(times[:],times.units)
    # hs = pd.Series(h[:,station],index=jd)
    #
    # fig = plt.figure(figsize=(12,4))
    # ax = fig.add_subplot(111)
    # hs.plot(ax=ax,title='%s at %s' % (h.long_name,nc.id))
    # ax.set_ylabel(h.units)


def update_image(*args):
    pass

def animate(fname):
    fig = plt.figure()
    ds = xr.open_dataset(fname, chunks={'year': 1})
    df = ds.to_dataframe()
    df = pd.DataFrame(data)

if __name__ == "__main__":
    animate("/home/micahjohnson/Desktop/test_output/precip.nc","precip")
