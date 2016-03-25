"""
C implementation of some radiation functions
"""


import cython
import numpy as np
cimport numpy as np


# Numpy must be initialized. When using numpy from C or Cython you must
# _always_ do that, or you will have segfaults
np.import_array()


cdef extern from "topotherm.h":
    void topotherm(int ngrid, double *ta, double *tw, double *z, double *skvfac, int nthreads, double *thermal);

    

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






