# cython: embedsignature=True
# cython: language_level=3
"""
C implementation of some radiation functions
"""


import cython
import numpy as np

cimport numpy as np

# Numpy must be initialized. When using numpy from C or Cython you must
# _always_ do that, or you will have segfaults
np.import_array()


cdef extern from "envphys_c.h":
    void topotherm(int ngrid, double *ta, double *tw, double *z, double *skvfac, int nthreads, double *thermal);
    void dewpt(int ngrid, double *ea, int nthreads, double tol, double *dpt);
    void iwbt(int ngrid, double *ta, double *td,	double *z, int nthreads, double tol, double *tw);


@cython.boundscheck(False)
@cython.wraparound(False)
# https://github.com/cython/cython/wiki/tutorials-NumpyPointerToC
def ctopotherm(np.ndarray[double, mode="c", ndim=2] ta,
               np.ndarray[double, mode="c", ndim=2] tw,
               np.ndarray[double, mode="c", ndim=2] z,
               np.ndarray[double, mode="c", ndim=2] skvfac,
               np.ndarray[double, mode="c", ndim=2] thermal not None,
               int nthreads=1):
    '''
    Call the function krige_grid in krige.c which will iterate over the grid
    within the C code

    Args:
        ta, tw, z, skvfac
    Out:
        thermal changed in place

    20160325 Scott Havens
    '''

    cdef int ngrid
    ngrid = ta.shape[0] * ta.shape[1]

    # convert the ta array to C
    cdef np.ndarray[double, mode="c", ndim=2] ta_arr
    ta_arr = np.ascontiguousarray(ta, dtype=np.float64)

    # convert the tw array to C
    cdef np.ndarray[double, mode="c", ndim=2] tw_arr
    tw_arr = np.ascontiguousarray(tw, dtype=np.float64)

    # convert the ta array to C
    cdef np.ndarray[double, mode="c", ndim=2] z_arr
    z_arr = np.ascontiguousarray(z, dtype=np.float64)

    # convert the skvfac to C
    cdef np.ndarray[double, mode="c", ndim=2] skvfac_arr
    skvfac_arr = np.ascontiguousarray(skvfac, dtype=np.float64)

    # call the C function
    topotherm(ngrid, &ta_arr[0,0], &tw_arr[0,0], &z_arr[0,0], &skvfac_arr[0,0], nthreads, &thermal[0,0])

    return None


@cython.boundscheck(False)
@cython.wraparound(False)
# https://github.com/cython/cython/wiki/tutorials-NumpyPointerToC
def cdewpt(np.ndarray[double, mode="c", ndim=2] vp,
               np.ndarray[double, mode="c", ndim=2] dwpt not None,
               float tolerance=0,
               int nthreads=1):
    '''

    Args:
        vp
    Out:
        dwpt changed in place

    20160505 Scott Havens
    '''

    cdef int ngrid
    ngrid = vp.shape[0] * vp.shape[1]

    # convert the ta array to C
    cdef np.ndarray[double, mode="c", ndim=2] vp_arr
    vp_arr = np.ascontiguousarray(vp, dtype=np.float64)

    # call the C function
    dewpt(ngrid, &vp_arr[0,0], nthreads, tolerance, &dwpt[0,0])

    return None


@cython.boundscheck(False)
@cython.wraparound(False)
# https://github.com/cython/cython/wiki/tutorials-NumpyPointerToC
def cwbt(np.ndarray[double, mode="c", ndim=2] ta,
         np.ndarray[double, mode="c", ndim=2] td,
         np.ndarray[double, mode="c", ndim=2] z,
         np.ndarray[double, mode="c", ndim=2] tw not None,
         float tolerance=0,
         int nthreads=1):
    '''
    Call the function iwbt in iwbt.c which will iterate over the grid
    within the C code

    Args:
        ta, td, z
    Out:
        tw changed in place (wet bulb temperature)

    20180611 Micah Sandusky
    '''

    cdef int ngrid
    ngrid = ta.shape[0] * ta.shape[1]

    # convert the ta array to C
    cdef np.ndarray[double, mode="c", ndim=2] ta_arr
    ta_arr = np.ascontiguousarray(ta, dtype=np.float64)

    # convert the dew point array to C
    cdef np.ndarray[double, mode="c", ndim=2] td_arr
    td_arr = np.ascontiguousarray(td, dtype=np.float64)

    # convert the ta array to C
    cdef np.ndarray[double, mode="c", ndim=2] z_arr
    z_arr = np.ascontiguousarray(z, dtype=np.float64)

    # call the C function
    iwbt(ngrid, &ta_arr[0,0], &td_arr[0,0], &z_arr[0,0], nthreads, tolerance, &tw[0,0])

    return None
