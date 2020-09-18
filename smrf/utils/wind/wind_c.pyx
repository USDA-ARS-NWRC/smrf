# cython: language_level=3
"""
Cython wrapper to the underlying C code

20160816
"""
import cython
import numpy as np
cimport numpy as np

# Numpy must be initialized. When using numpy from C or Cython you must
# _always_ do that, or you will have segfaults
np.import_array()


cdef extern from "wind_header.h":
    void calc_maxus(int nx, int ny, double *x, double *y, double *z, double *X_start, double *Y_start, 
                    double *X_end, double *Y_end, double height, int nthreads, double *maxus);


@cython.boundscheck(False)
@cython.wraparound(False)
# https://github.com/cython/cython/wiki/tutorials-NumpyPointerToC
def call_maxus(x, y, Z, X, Y, Xi, Yi, double height=3, int nthreads=1):
    '''
    Call the function maxus_grid in calc_wind.c which will iterate over the grid
    within the C code

    Args:
        ad - [nsta x nsta] matrix of distances between stations
        dgrid - [ngrid x nsta] matrix of distances between grid points and stations
        elevations - [nsta] array of station elevations
        weights (return) - [ngrid x nsta] matrix of kriging weights calculated
        nthreads - number of threads to use in parallel processing

    Out:
        weights changed in place

    20160222 Scott Havens
    '''

    cdef int nx, ny
    ny, nx = X.shape[0], X.shape[1]

    # convert the x array to C
    cdef np.ndarray[double, mode="c", ndim=1] x_arr
    x_arr = np.ascontiguousarray(x, dtype=np.float64)

    # convert the x array to C
    cdef np.ndarray[double, mode="c", ndim=1] y_arr
    y_arr = np.ascontiguousarray(y, dtype=np.float64)

    # convert the z array to C
    cdef np.ndarray[double, mode="c", ndim=2] elev
    elev = np.ascontiguousarray(Z, dtype=np.float64)

    # convert the X array to C
    cdef np.ndarray[double, mode="c", ndim=2] X_start
    X_start = np.ascontiguousarray(X, dtype=np.float64)

    # convert the Y array to C
    cdef np.ndarray[double, mode="c", ndim=2] Y_start
    Y_start = np.ascontiguousarray(Y, dtype=np.float64)

    # convert the Xi array to C
    cdef np.ndarray[double, mode="c", ndim=2] X_end
    X_end = np.ascontiguousarray(Xi, dtype=np.float64)

    # convert the Yi array to C
    cdef np.ndarray[double, mode="c", ndim=2] Y_end
    Y_end = np.ascontiguousarray(Yi, dtype=np.float64)

    # convert the dgrid to C
    z = np.zeros_like(X)
    cdef np.ndarray[double, mode="c", ndim=2] maxus
    maxus = np.ascontiguousarray(z, dtype=np.float64)

    calc_maxus(nx, ny, &x_arr[0], &y_arr[0], &elev[0,0], &X_start[0,0], &Y_start[0,0],
                &X_end[0,0], &Y_end[0,0], height, nthreads, &maxus[0,0])

    return maxus
