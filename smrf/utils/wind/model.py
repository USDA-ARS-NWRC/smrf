from __future__ import print_function

import os
# import matplotlib.pyplot as plt
# import progressbar
from datetime import datetime

import netCDF4 as nc
import numpy as np

from smrf.utils.wind import wind_c


class wind_model():
    """

    Estimating wind speed and direction is complex terrain can be difficult due
    to the interaction of the local topography with the wind. The methods
    described here follow the work developed by Winstral and Marks (2002) and
    Winstral et al. (2009) :cite:`Winstral&Marks:2002` :cite:`Winstral&al:2009`
    which parameterizes the terrain based on the upwind direction. The
    underlying method calulates the maximum upwind slope (maxus) within a
    search distance to determine if a cell is sheltered or exposed.

    The azimuth **A** is the direction of the prevailing wind for which the
    maxus value will be calculated within a maximum search distance **dmax**.
    The maxus (**Sx**) parameter can then be estimated as the maximum value of
    the slope from the cell of interest to all of the grid cells along the
    search vector. The efficiency in selection of the maximum value can be
    increased by using the techniques from the horizon functio which calculates
    the horizon for each pixel. Therefore, less calculations can be performed.
    Negative **Sx** values indicate an exposed pixel location (shelter pixel
    was lower) and positive **Sx** values indicate a sheltered pixel (shelter
    pixel was higher).

    After all the upwind direction are calculated, the average **Sx** over a
    window is calculated. The average **Sx** accounts for larger lanscape
    obsticles that may be adjacent to the upwind direction and affect the flow.
    A window size in degrees takes the average of all **Sx**.

    Args:
        x: array of x locations
        y: array of y locations
        dem: matrix of the dem elevation values
        nthread: number of threads to use for maxus calculation

    """

    def __init__(self, x, y, dem, nthreads=1):

        self.x = x
        self.y = y
        self.dem = dem
        self.nx = len(x)
        self.ny = len(y)
        self.ngrid = self.ny * self.nx
        self.nthreads = nthreads

        self.dx = np.abs(x[1] - x[0])
        self.dy = np.abs(y[1] - y[0])

        X, Y = np.meshgrid(np.arange(0, self.nx), np.arange(0, self.ny))
        self.X = X
        self.Y = Y
        self.shape = X.shape

    def maxus(self, dmax, inc=5, inst=2, out_file='smrf_maxus.nc'):
        """
        Calculate the maxus values

        Args:
            dmax: length of outlying upwind search vector (meters)
            inc: increment between direction calculations (degrees)
            inst: Anemometer height (meters)
            out_file: NetCDF file for output results

        Returns:
            None, outputs maxus array straight to file
        """

        if (dmax % self.dx != 0):
            raise ValueError('dmax must divide evenly into the DEM')

        self.dmax = dmax
        self.inc = inc
        self.inst_hgt = inst

        # All angles that model will consider.
        swa = np.arange(0, 360, inc)
        self.directions = swa

        # initialize the output file
        self.out_file = out_file
        self.type = 'maxus'
        ex_att = {}
        ex_att['dmax'] = dmax
        # initialize output
        self.output_init(self.type, out_file, ex_att=ex_att)

        # run model over range in wind directions
        for i, angle in enumerate(swa):

            self.maxus_val = self.maxus_angle(angle, self.dmax)
            self.output(self.type, i)

    def tbreak(self, dmax, sepdist, inc=5, inst=2, out_file='smrf_tbreak.nc'):
        """
        Calculate the topobreak values

        Args:
            dmax: length of outlying upwind search vector (meters)
            sepdist: length of local max upwind slope search vector (meters)
            angle: middle upwind direction around which to run model (degrees)
            inc: increment between direction calculations (degrees)
            inst: Anemometer height (meters)
            out_file: NetCDF file for output results

        Returns:
            None, outputs maxus array straight to file

        """

        if (sepdist % self.dx != 0) | (dmax % self.dx != 0):
            raise ValueError(
                'sepdist and dmax must divide evenly into the DEM')

        self.dmax = dmax
        self.sepdist = sepdist
        self.inc = inc
        self.inst_hgt = inst

        # All angles that model will consider.
        swa = np.arange(0, 360, inc)
        self.directions = swa

        # initialize the output file
        self.out_file = out_file
        self.type = 'tbreak'
        # extra attributes
        ex_att = {}
        ex_att['dmax'] = dmax
        ex_att['sepdist'] = sepdist
        # initialize output
        self.output_init(self.type, out_file, ex_att=ex_att)

        # run model over range in wind directions
        for i, angle in enumerate(swa):

            # calculate the maxus value
            maxus_outlying = self.maxus_angle(angle, self.dmax)

            # calculate the local maxus value
            maxus_local = self.maxus_angle(angle, self.sepdist)

            self.maxus_val = maxus_local - maxus_outlying

            self.output(self.type, i)

    def maxus_angle(self, angle, dmax):
        """
        Calculate the maxus for a single direction for a search distance dmax

        Note:
            This will produce different results than the original maxus
            program. The differences are due to:

            1. Using dtype=double for the elevations
            2. Using different type of search method to find the endpoints.

            However, if the elevations are rounded to integers, the cardinal
            directions will reproduce the original results.

        Args:
            angle: middle upwind direction around which to run model (degrees)
            dmax: length of outlying upwind search vector (meters)

        Returns:
            maxus: array of maximum upwind slope values within dmax

        """

        print("Calculating maxus for direction: {}".format(angle))

        angle *= np.pi / 180

        # calculate the endpoints
        # accually use the distances to ensure that we are searching far enough
        Xi = self.X*self.dx + dmax * np.cos(angle-np.pi/2)
        Yi = self.Y*self.dy + dmax * np.sin(angle-np.pi/2)

        self.Xi = np.floor(Xi/self.dx + 0.5)
        self.Yi = np.floor(Yi/self.dy + 0.5)

        # underlying C code similar to Adams
        maxus = wind_c.call_maxus(self.x, self.y, self.dem, self.X, self.Y,
                                  self.Xi, self.Yi, self.inst_hgt,
                                  self.nthreads)

#         # my interpretation of the calculations in Python form
#         maxus = np.zeros((self.ngrid,))
#         pbar = progressbar.ProgressBar(max_value=self.ngrid)
#         j = 0
#         for index in range(5000, self.ngrid):
#             maxus[index] = self.find_maxus(index)
#             j += 1
#             pbar.update(j)
#             if j > 4999:
#                 break
#         pbar.finish()
#         maxus = np.reshape(maxus, self.shape)

        # correct for values that are their own horizon
        maxus[maxus <= -89.0] = 0

        return maxus

    def windower(self, maxus_file, window_width, wtype):
        """
        Take the maxus output and average over the window width

        Args:
            maxus_file: location of the previously calculated maxus values
            window_width: window width about the wind direction
            wtype: type of wind calculation 'maxus' or 'tbreak'

        Return:
            New file containing the windowed values
        """

        # open the previous file and get the directions
        n = nc.Dataset(maxus_file, 'r')
        directions = n.variables['direction'][:]
        self.directions = directions

        # create a new file based on the old file
        name = os.path.splitext(maxus_file)
        out_file = "%s_%iwindow.nc" % (name[0], window_width)
        self.output_init(wtype, out_file)
        self.out_file = out_file

        # determine which directions are required for each single direction
        window_width /= 2
        inc = np.mean(np.diff(directions), dtype=int)

        for i, d in enumerate(directions):

            print("Windowing direction {}".format(d))

            # determine which directions to include
            window_start = d - window_width
            window_end = d + window_width

            # to ensure that it contains the end points
            sl = np.arange(window_start, window_end+1, inc)

            # correct for edge effects
            sl[sl < 0] = sl[sl < 0] + 360
            sl[sl > 360] = sl[sl > 360] - 360

            # determine the indicies to the input file
            idx = self.ismember(directions, sl)

            # grab all the data for all directions and average
            self.maxus_val = np.mean(n.variables[wtype][idx, :], axis=0)

            # put it into the output file
            self.output(wtype, i)

        n.close()

    def ismember(self, a, b):
        bind = {}
        for i, elt in enumerate(b):
            if elt not in bind:
                bind[elt] = True
        return [bind.get(itm, False) for itm in a]

    def find_maxus(self, index):
        """
        Calculate the maxus given the start and end point

        Args:
            index: index to a point in the array

        Returns:
            maxus value for the point
        """

        start_point = np.unravel_index(index, self.shape)

        # determine the points along the endpoint line
        end_point = (self.Yi[start_point], self.Xi[start_point])
        p = self.bresenham(start_point, end_point)

        # ensure the cases where it's on the edge
        p = np.delete(p, np.where(p[:, 0] < 0)[0], axis=0)
        p = np.delete(p, np.where(p[:, 1] < 0)[0], axis=0)
        p = np.delete(p, np.where(p[:, 0] > self.ny)[0], axis=0)
        p = np.delete(p, np.where(p[:, 1] > self.nx)[0], axis=0)

        # determine the relative heights along the path
        h = self.dem[p[:, 0], p[:, 1]]  # - (self.inst_hgt + self.dem[index])

        # find the horizon for each pixel along the path
        hord = self.hord(self.x[p[:, 1]], self.y[p[:, 0]], h)

        # calculate the angle to that point
        pt = p[hord[0], :]   # point that was found for horizon
        d = np.sqrt(np.power(self.x[pt[1]] - self.x[start_point[1]], 2) +
                    np.power(self.y[pt[0]] - self.y[start_point[0]], 2))

        slope = (h[hord[0]] - (h[0] + self.inst_hgt)) / d
        maxus = np.arctan(slope) * 180 / np.pi

        return maxus

    def bresenham(self, start, end):
        """
        Python implementation of the Bresenham algorthim to find
        all the pixels that a line between start and end interscet

        Args:
            start: list of start point
            end: list of end point

        Returns:
            Array path of all points between start and end
        """
#         start = list(start)
#         end = list(end)
        path = []

        x0 = start[0]
        y0 = start[1]
        x1 = end[0]
        y1 = end[1]

        steep = abs(y1 - y0) > abs(x1 - x0)
        backward = x0 > x1

        if steep:
            x0, y0 = y0, x0
            x1, y1 = y1, x1
        if backward:
            x0, x1 = x1, x0
            y0, y1 = y1, y0

        dx = x1 - x0
        dy = abs(y1 - y0)
        error = dx / 2
        y = y0

        if y0 < y1:
            ystep = 1
        else:
            ystep = -1

        for x in range(x0, x1+1):
            if steep:
                path.append((y, x))
            else:
                path.append((x, y))

            error -= dy

            if error <= 0:
                y += ystep
                error += dx

        if backward:
            path.reverse()

        return np.array(path)

    def hord(self, x, y, z):
        '''
        Calculate the horizon pixel for all z
        This mimics the simple algorthim from Dozier 1981 but
        was adapated for use in finding the maximum upwind slope

        Works backwards from the end but looks forwards for
        the horizon

        Args:
            x: x locations for the points
            y: y locations for the points
            z: elevations for the points

        Returns:
            array of the horizon index for each point

        '''

        N = len(z)  # number of points to look at
    #     offset = 1      # offset from current point to start looking

        # preallocate the h array
        h = np.zeros(N, dtype=int)
        h[N-1] = N-1
        i = N - 2

        # work backwarks from the end for the pixels
        while i >= 0:
            h[i] = i
            j = i + 1   # looking forward
            found = False

            while not found:

                d_i = np.sqrt(np.power(x[i] - x[j], 2) +
                              np.power(y[i] - y[j], 2))
                d_h = np.sqrt(np.power(x[i] - x[h[j]], 2) +
                              np.power(y[i] - y[h[j]], 2))

                pt_i = self._slope(0, z[i]+self.inst_hgt, d_i, z[j])
                pt_h = self._slope(0, z[i]+self.inst_hgt, d_h, z[h[j]])

                if (pt_i < pt_h):
                    if (j == N-1):
                        found = True
                        h[i] = j
                    else:
                        j = h[j]
                else:
                    found = True
                    if (pt_i > pt_h):
                        h[i] = j
                    else:
                        h[i] = h[j]

            i -= 1

        return h

    def _slope(self, xi, zi, xj, zj):
        '''
        Slope between the two points
        '''

        return (zj - zi) / (xj - float(xi))

    def output_init(self, ptype, filename, ex_att=None):
        """
        Initialize a NetCDF file for outputing the maxus values or tbreak

        Args:
            ptype: type of calculation that will be saved, either 'maxus' or
                'tbreak'
            filename: filename to save the output into
            ex_att:   extra attributes to add
        """

        if ptype == 'maxus':
            var = 'maxus'
            desc = 'Maximum upwind slope'

        elif ptype == 'tbreak':
            var = 'tbreak'
            desc = 'tbreak'

        else:
            raise ValueError('''Could not determine what to output, check type
                            value (maxus or tbreak)''')

        dimensions = ('Direction', 'y', 'x')

        s = nc.Dataset(filename, 'w', 'NETCDF4')

        s.createDimension(dimensions[0], len(self.directions))
        s.createDimension(dimensions[1], self.ny)
        s.createDimension(dimensions[2], self.nx)

        # create the variables
        s.createVariable('direction', 'i', dimensions[0])
        s.createVariable('y', 'f', dimensions[1])
        s.createVariable('x', 'f', dimensions[2])
        s.createVariable(var, 'f', dimensions)

        # define some attributes
        setattr(s.variables['y'], 'units', 'meters')
        setattr(s.variables['y'], 'description', 'UTM, north south')
        setattr(s.variables['x'], 'units', 'meters')
        setattr(s.variables['x'], 'description', 'UTM, east west')
        setattr(s.variables['direction'], 'units', 'bearing')
        setattr(s.variables['direction'], 'description',
                'Wind direction from North')
        setattr(s.variables[var], 'units', 'angle')
        setattr(s.variables[var], 'description', desc)
        setattr(s, 'dateCreated', datetime.now().isoformat())

        # set attributes
        if ex_att is not None:
            for key, value in ex_att.items():
                setattr(s, key, value)

        s.variables['y'][:] = self.y
        s.variables['x'][:] = self.x

    def output(self, ptype, index):
        """
        Output the data into the out file that has previously been initialized.

        Args:
            ptype: type of calculation that will be saved, either 'maxus'
                or 'tbreak'
            index: index into the file for where to place the output
        """

        s = nc.Dataset(self.out_file, 'r+')
        s.variables['direction'][:] = self.directions
        s.variables[ptype][index, :] = self.maxus_val
        s.close()
