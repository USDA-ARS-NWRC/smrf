"""
Compare the maxus netCDF files
"""



import matplotlib.pyplot as plt
import netCDF4 as nc
import numpy as np

#------------------------------------------------------------------------------
# compare with the original outputs
print 'loading comparison...'

# SMRF maxus
w = nc.Dataset('/home/scotthavens/Documents/Projects/smrf/examples/smrf_maxus.nc')

# Adam maxus
m = nc.Dataset('/home/scotthavens/Documents/Projects/smrf/examples/maxus.nc')

for i,d in enumerate(w.variables['direction'][:]):

#     i = 3

    wmxs = w.variables['maxus'][i,:]
    
    mxs = m.variables['maxus'][i,:]
    
    
    # mxs = np.loadtxt('/media/Drobo1/BRB/BRB-wy09/spatial_WRF_OG/data/topo/maxus/maxus30m/maxus690_0.asc', skiprows=6)
    # mxs = np.loadtxt('/home/scotthavens/Documents/Projects/smrf/smrf/utils/wind/maxus_0.asc', skiprows=6)
    
      
#     plt.imshow(wmxs - mxs)
#     plt.colorbar()
#     plt.show()
    
    # plt.plot(w.maxus_val[1,:] - mxs[1,:])
    # plt.show()
    
    sz = (5000*5000)
    
    H,xedges,yedges = np.histogram2d(np.reshape(wmxs,sz), np.reshape(mxs,sz), bins=100)
    Hm = np.ma.masked_where(H == 0, H)
    
    im = plt.imshow(Hm, interpolation='nearest', origin='low',
                    extent=[xedges[0], xedges[-1], yedges[0], yedges[-1]])
    
    plt.plot([-60,60],[-60,60],'r')
    
    plt.title(d)
    plt.show()
    

w.close()
m.close()
