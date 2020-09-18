# cython: embedsignature=True
# cython: language_level=3
'''
Compiling dk's kriging function

20160205 Scott Havens
'''


import cython
import numpy as np

cimport numpy as np
from cpython cimport Py_INCREF, PyObject
from libc.stdlib cimport free

# Numpy must be initialized. When using numpy from C or Cython you must
# _always_ do that, or you will have segfaults
np.import_array()


cdef extern from "dk_header.h":
    double *krige(int nsta, double *ad, double *dgrid, double *elevations);
    void krige_grid(int nsta, int ngrid, double *ad, double *dgrid, double *elevations, int nthreads, double *weights);
#     int lusolv(int n, double **a, double *x)



@cython.boundscheck(False)
@cython.wraparound(False)
# https://github.com/cython/cython/wiki/tutorials-NumpyPointerToC
def call_grid(object ad, object dgrid,
              np.ndarray[double, mode="c", ndim=1] elevations, 
              np.ndarray[double, mode="c", ndim=2] weights not None,
              int nthreads=1):
    '''
    Call the function krige_grid in krige.c which will iterate over the grid
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

    cdef int nsta, ngrid
    ngrid, nsta = dgrid.shape[0], dgrid.shape[1]

    # convert the ad array to C
    cdef np.ndarray[double, mode="c", ndim=2] ad_arr
    ad_arr = np.ascontiguousarray(ad, dtype=np.float64)

    # convert the dgrid to C
    cdef np.ndarray[double, mode="c", ndim=2] grid
    grid = np.ascontiguousarray(dgrid, dtype=np.float64)

    # call the C function
    krige_grid(nsta, ngrid, &ad_arr[0,0], &grid[0,0], &elevations[0], nthreads, &weights[0,0])

    return None


# @cython.boundscheck(False)
# @cython.wraparound(False)
# def run(object ad, object dgrid,
#                np.ndarray[double, mode="c", ndim=1] elevations,
#                np.ndarray[double, mode="c", ndim=2] weights not None):
#     '''
#     Instead of calling the krige_grid, iterate over the grid here and
#     add parallel support
#
#     This isn't working or finished
#     '''
#
#     cdef double *w
#     cdef np.ndarray w_arr
#
#     cdef int nsta, ngrid
#     ngrid, nsta = dgrid.shape[0], dgrid.shape[1]
#
#     # convert the ad array to C
#     cdef np.ndarray[double, mode="c", ndim=2] ad_arr
#     ad_arr = np.ascontiguousarray(ad, dtype=np.float64)
#
#     # convert the dgrid to C
#     cdef np.ndarray[double, mode="c", ndim=2] grid
#     grid = np.ascontiguousarray(dgrid, dtype=np.float64)
#
#     for i in range(ngrid):
#
#         w = krige(nsta, &ad_arr[0,0], &grid[i,0], &elevations[0]);
#
#         # convert C array to Python object
#         array_wrapper = ArrayWrapper()
#         array_wrapper.set_data(nsta, <void*> w)
#         w_arr = np.array(array_wrapper, copy=False)
#         # Assign our object to the 'base' of the ndarray object
#         w_arr.base = <PyObject*> array_wrapper
#         # Increment the reference count, as the above assignement was done in
#         # C, and Python does not know that there is this additional reference
#         Py_INCREF(array_wrapper)
#
#
#         weights[i] = w_arr
#
#     return None


# @cython.boundscheck(False)
# @cython.wraparound(False)
# def call_func(int l, int nsta, object ad,
#                np.ndarray[double, mode="c", ndim=1] dgrid,
#                np.ndarray[double, mode="c", ndim=1] elevations):
#
#     cdef double *array
#     cdef np.ndarray ndarray
#
#     cdef np.ndarray[double, mode="c", ndim=2] arr
#     arr = np.ascontiguousarray(ad, dtype=np.float64)
#
#
#     print 'here python'
#
# #     cdef a = <double**> ad.data
#
#     # call the C function
#     array = krige(nsta, &arr[0,0], &dgrid[0], &elevations[0])
#
# #     array = krige(nsta, <double**> arr.data, &dgrid[0], &elevations[0])
#
#
#
#
# #     # convert C array to Python object
# #     array_wrapper = ArrayWrapper()
# #     array_wrapper.set_data(nsta, <void*> array)
# #     ndarray = np.array(array_wrapper, copy=False)
# #     # Assign our object to the 'base' of the ndarray object
# #     ndarray.base = <PyObject*> array_wrapper
# #     # Increment the reference count, as the above assignement was done in
# #     # C, and Python does not know that there is this additional reference
# #     Py_INCREF(array_wrapper)
#
#
#     return ndarray

# We need to build an array-wrapper class to deallocate our array when
# the Python object is deleted.
# https://gist.github.com/GaelVaroquaux/1249305

# cdef class ArrayWrapper:
#     cdef void* data_ptr
#     cdef int size
#
#     cdef set_data(self, int size, void* data_ptr):
#         """ Set the data of the array
#         This cannot be done in the constructor as it must recieve C-level
#         arguments.
#         Parameters:
#         -----------
#         size: int
#             Length of the array.
#         data_ptr: void*
#             Pointer to the data
#         """
#         self.data_ptr = data_ptr
#         self.size = size
#
#     def __array__(self):
#         """ Here we use the __array__ method, that is called when numpy
#             tries to get an array from the object."""
#         cdef np.npy_intp shape[1]
#         shape[0] = <np.npy_intp> self.size
#         # Create a 1D array, of length 'size'
#         ndarray = np.PyArray_SimpleNewFromData(1, shape,
#                                                np.NPY_INT, self.data_ptr)
#         return ndarray
#  
#     def __dealloc__(self):
#         """ Frees the array. This is called by Python when all the
#         references to the object are gone. """
#         free(<void*>self.data_ptr)