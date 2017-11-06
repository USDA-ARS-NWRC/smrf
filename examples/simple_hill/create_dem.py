from netCDF4 import Dataset
import numpy as np

def make_quartered(n, v1=None, v2=None, v3=None, v4=None ):
    """
    Quarters the DEM and places values in each quadrant
    """

    array = np.zeros((n,n))

    x_0 = n/2
    y_0 = n/2

    y,x = np.ogrid[0:n, 0:n]

    qt1 = (y<=y_0) & (x<=x_0)
    qt2 = (y>=y_0) & (x<=x_0)
    qt3 = (y>y_0) & (x>x_0)
    qt4 = (y<y_0) & (x>x_0)

    array[qt1] = v1
    array[qt2] = v2
    array[qt3] = v3
    array[qt4] = v4

    return array

def make_circle_mask(center, radius, n):
    """
    Makes a mask thats a circle
    """
    a = center[0]
    b = center[1]
    r = radius

    y,x = np.ogrid[0:n, 0:n]
    mask = (x-a)**2 + (y-b)**2 <= r**2

    array = np.zeros((n, n))
    array[mask] = 1
    return array

def makeGaussian(size, fwhm = 3, center=None):
    """ Make a square gaussian kernel.
    size is the length of a side of the square
    fwhm is full-width-half-maximum, which
    can be thought of as an effective radius.
    """

    x = np.arange(0, size, 1, float)
    y = x[:,np.newaxis]

    if center is None:
        x0 = y0 = size // 2
    else:
        x0 = center[0]
        y0 = center[1]

    return np.exp(-4*np.log(2) * ((x-x0)**2 + (y-y0)**2) / fwhm**2)


X = 50
Y = 50
step = 100 #meters
center = (25,25)

d = Dataset('topo.nc','w',format='NETCDF4')
d.createDimension('x',X)
d.createDimension('y',Y)

x = d.createVariable('x',np.float64,('x',))
y = d.createVariable('y',np.float64,('y'))
x[:] = np.arange(0,X*step,step)
y[:] = np.arange(0,Y*step,step)

#Veg Height
veg_height = d.createVariable('veg_height',np.float64,('y','x'))
veg_height[:] = make_quartered(X,v1=0.3,v2=3,v3=6,v4=0.5)

#veg_type
veg_type = d.createVariable('veg_type',np.float64,('y','x'))
veg_type[:] = make_quartered(X,v1=81,v2=52,v3=43,v4=71)

#Mask
mask = d.createVariable('mask',np.float64,('y','x'))
mask[:] = make_circle_mask(center,20,50)

#veg transmissivity
veg_tau = d.createVariable('veg_tau',np.float64,('y','x'))
veg_tau[:] = make_quartered(X,v1=1,v2=1,v3=0.2,v4=1)

#Vegetation extension coefficient
veg_k = d.createVariable('veg_k',np.float64,('y','x'))
veg_k[:] = make_quartered(X,v1=0,v2=0,v3=0.04,v4=1)

#Make a small peak
dem = d.createVariable('dem',np.float64,('y','x'))
dem[:] = 1000*(makeGaussian(X, fwhm= 25, center=center))

d.close()
