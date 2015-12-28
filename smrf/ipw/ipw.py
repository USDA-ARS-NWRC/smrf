'''
Created on Apr 7, 2015

Adapted from Roger Lew (rogerlew.gmail.com)isnobal.py

@author: Scott Havens
'''

# __version__ = "0.0.1"

# from collections import namedtuple
from glob import glob
import os
# import time
# import warnings

# import h5py
import numpy as np
# from numpy.testing import assert_array_almost_equal
from math import ceil
# import matplotlib.pyplot as plt
# from matplotlib.colors import Normalize, ListedColormap

# from osgeo import gdal, gdalconst, ogr, osr

in_db__vars = tuple('I_lw T_a e_a u T_g S_n'.split())
out_em__vars = tuple('R_n H L_v_E G M delta_Q E_s '
                     'melt ro_predict cc_s'.split())
out_snow__vars = tuple('z_s rho m_s h2o T_s_0 T_s_l T_s z_s_l h2o_sat'.split())

_unpackindx  = lambda L: int(L.split()[2])
_unpackint   = lambda L: int(L.split('=')[1].strip())
_unpackfloat = lambda L: float(L.split('=')[1].strip())
_unpackstr   = lambda L: L.split('=')[1].strip()


class Band:
    """
    Represents a raster band of geospatial data
    """
    def __init__(self, nlines, nsamps):

        # Using classes instead of dicts makes things faster
        # even if though they are more verbose to implement

        # width, height
        self.nlines, self.nsamps = nlines, nsamps

        # basic_image
        self.name = None
        self.bytes = None
        self.fmt = None
        self.frmt = None
        self.bits = None
        self.annot = None
        self.history = []

        # geo
        self.bline = None
        self.bsamp = None
        self.dline = None
        self.dsamp = None
        self.geounits = None
        self.coord_sys_ID = None
        self.geotransform = None
        self.x = None
        self.y = None

        # lq
        self.int_min = 0
        self.int_max = 255
        self.float_min = 0.0
        self.float_max = 1.0
        self.units = None
        self.transform = lambda x: (1.0 - 0.0) * (x / 255) + 0

        self.data = None

    def _parse_geo_readline(self, L0, L1, L2, L3, L4, L5):
        """
        Get the geo header information from readline()
        """
        bline = self.bline = _unpackfloat(L0)
        bsamp = self.bsamp = _unpackfloat(L1)
        dline = self.dline = _unpackfloat(L2)
        dsamp = self.dsamp = _unpackfloat(L3)
        self.geounits = _unpackstr(L4)
        self.coord_sys_ID = _unpackstr(L5)
        self.geotransform = [bsamp - dsamp / 2.0,
                             dsamp, 0.0,
                             bline - dline / 2.0,
                             0.0, dline]
        self.y = bline + np.arange(self.nlines)*dline
        self.x = bsamp + np.arange(self.nsamps)*dsamp
        
        
    def _parse_geo(self, L0, L1, L2, L3, L4, L5):
        """
        Get the geo header information given values
        """
        bline = self.bline = L0
        bsamp = self.bsamp = L1
        dline = self.dline = L2
        dsamp = self.dsamp = L3
        self.geounits = L4
        self.coord_sys_ID = L5
        self.geotransform = [bsamp - dsamp / 2.0,
                             dsamp, 0.0,
                             bline - dline / 2.0,
                             0.0, dline]

    def _parse_lq(self, L0, L1):
        """
        Pulls the scale values from line0 and line1 builds
        a function for transforming integer values to floats
        """
        [[int_min, float_min], [int_max, float_max]] = [L0.split(), L1.split()]
        int_min, float_min, int_max, float_max = map(float, [int_min, float_min, int_max, float_max])
        self.transform = lambda x: (float_max - float_min) * (x / int_max) + float_min
        self.int_min, self.int_max = int_min, int_max
        self.float_min, self.float_max = float_min, float_max

    def __str__(self):
        return '''\
    nlines (height): {0.nlines}
    nsamps (width): {0.nsamps}
    bytes: {0.bytes}
    transform: {0.int_min} -> {0.int_max}
               {0.float_min} -> {0.float_max}
    geo: {0.bline} {0.bsamp} {0.dline} {0.dsamp}
'''.format(self)


class IPW:
    """
    Represents a IPW file container
    """
    def __init__(self, fname=None, epsg=32611):
        """
        IPW(fname[, rescale=True])

        Parameters
        ----------
        fname : string
           path to the IPW container
           if "in.", "em.", or "snow." are in fname
           band names will be pulled from the cooresponding
           global varlist:
               in_db__vars
               out_em__vars
               out_snow__vars

        rescale : bool (default = True)
            Specifies whether data should be rescaled to singles
            based on the lq map or whether they should remain uint8/16

        epsg : int (default = 32611)
             North America Centric Cheat Sheet
            -----------------------------------------------
            UTM Zone 10 Northern Hemisphere (WGS 84)  32610
            UTM Zone 11 Northern Hemisphere (WGS 84)  32611
            UTM Zone 12 Northern Hemisphere (WGS 84)  32612
            UTM Zone 13 Northern Hemisphere (WGS 84)  32613
            UTM Zone 14 Northern Hemisphere (WGS 84)  32614
            UTM Zone 15 Northern Hemisphere (WGS 84)  32615
            UTM Zone 16 Northern Hemisphere (WGS 84)  32616
            UTM Zone 17 Northern Hemisphere (WGS 84)  32617
            UTM Zone 18 Northern Hemisphere (WGS 84)  32618
            UTM Zone 19 Northern Hemisphere (WGS 84)  32619

        """
        global in_db__vars, out_em__vars, out_snow__vars

        self.epsg = epsg    # this should just be stored as an attribute
                            # it produces alot of book-keeping otherwise
                            
        # read a file or create an empty object
        if fname is not None:
            self.read(fname)
            
        else:
            self.fname = None
            self.bands = []
            self.bip = None
            self.byteorder = [0,1,2,3]
            self.nlines = None
            self.nsamps = None
            self.nbands = None
            self.geohdr = None


    def read(self, fname):
        '''
        Read the IPW file into the various bands
        Turns the data into a numpy array of float32
        '''
        
        # read the data to a list of lines
        fid = open(fname, 'rb')
        readline = fid.readline  # dots make things slow (and ugly)
        tell = fid.tell

        bands = []
        byteorder = None
        nlines = None
        nsamps = None
        nbands = None
        geo = None

        # size of the file we are reading in bytes
        st_size = os.fstat(fid.fileno()).st_size
        while 1:  # while 1 is faster than while True
            line = readline()

            # fail safe, haven't needed it, but if this is running
            # on a server not a bad idea to have it here
            if tell() == st_size:
                raise Exception('Unexpectedly reached EOF')

            if '!<header> basic_image_i' in line:
                byteorder = map(int, readline().split('=')[1].strip())
                nlines = _unpackint(readline())
                nsamps = _unpackint(readline())
                nbands = _unpackint(readline())

                # initialize the band instances in the bands list
                bands = [Band(nlines, nsamps) for j in xrange(nbands)]

            elif '!<header> basic_image' in line:
                indx = _unpackindx(line)    # band number
                bytes = bands[indx].bytes = _unpackint(readline())
#                 bands[indx].frmt = ('uint8', 'uint16')[bytes == 2]
                bands[indx].frmt = 'uint' + str(bytes*8)
                bands[indx].bits = _unpackint(readline())

                # see if there is any other information
                last_pos = fid.tell()
                line = readline()
                 
                while line[0] != '!':
                    
                    key = line.split('=')[0].strip()
                    val = line.split('=')[1].strip()
                    
                    if key == 'annot':
                        bands[indx].annot = val
                    elif key == 'history':
                        bands[indx].history.append(val)
                    elif key == 'fmt':
                        bands[indx].fmt = val
                        
                    last_pos = fid.tell()
                    line = readline()
                 
                # set pointer back one line
                fid.seek(last_pos)

            elif '!<header> geo' in line:
                indx = _unpackindx(line)
                bands[indx]._parse_geo_readline(*[readline() for i in xrange(6)])
                geo = 1

            elif '!<header> lq' in line:
                indx = _unpackindx(line)
                line1 = fid.readline()
                if 'units' in line1:
                    bands[indx].units = _unpackstr(line1)

                    bands[indx]._parse_lq(_unpackstr(readline()),
                                          _unpackstr(readline()))
                else:
                    bands[indx]._parse_lq(_unpackstr(line1),
                                          _unpackstr(readline()))

            if '\f' in line:  # feed form character separates the
                break         # image header from the binary data

        # attempt to assign names to the bands
        assert nbands == len(bands)

        if 'in.' in fname:
            varlist = in_db__vars
        elif 'em.' in fname:
            varlist = out_em__vars
        elif 'snow.' in fname:
            varlist = out_snow__vars
        else:
            varlist = ['band%02i'%i for i in xrange(nbands)]

        assert len(varlist) >= nbands

        for b, name in zip(bands, varlist[:nbands]):
            b.name = name

        # Unpack the binary data using numpy.fromfile
        # because we have been reading line by line fid is at the
        # first data byte, we will read it all as one big chunk
        # and then put it into the appropriate bands
        #
        # np.types allow you to define heterogenous arrays of mixed
        # types and reference them with keys, this helps us out here
        dt = np.dtype([(b.name, b.frmt) for b in bands])

        bip = sum([b.bytes for b in bands])  # bytes-in-pixel
        required_bytes = bip * nlines * nsamps
        assert (st_size - tell()) >= required_bytes

        # this is way faster than looping with struct.unpack
        # struct.unpack also starts assuming there are pad bytes
        # when format strings with different types are supplied
        data = np.fromfile(fid, dt, count=nlines*nsamps)

        # Separate into bands
        data = data.reshape(nlines, nsamps)
        for b in bands:
#             if rescale:
#                 b.data = np.array(data[b.name],dtype=np.float32)
                b.data = np.array(b.transform(data[b.name]),
                                dtype=np.float32)
#             else:
#                 b.data = np.array(data[b.name],
#                                   dtype=np.dtype(b.frmt))

        # clean things up
        self.fname = fname
#         self.rescale = rescale
#         self.name_dict = dict(zip(varlist, range(nbands)))
        self.bands = bands
        self.bip = bip
        self.byteorder = byteorder
        self.nlines = nlines
        self.nsamps = nsamps
        self.nbands = nbands
        self.geohdr = geo

        fid.close()

    def write(self, fileName, nbits=8):
        """
        Write the IPW data to file
        fileName - file to write to
        nbits - number of bits for each band default=8
        """

        # set the bits, bytes, and int_max for each band
        # have to convert nbits one to float then back at the end for ceil to work
        for i, b in enumerate(self.bands):
            self.bands[i].name = 'band%02i'%i
            self.bands[i].bits = nbits
            bytes = self.bands[i].bytes = int(ceil(float(nbits)/8))
            self.bands[i].frmt = 'uint' + str(bytes*8)
            self.bands[i].int_min = 0
            self.bands[i].int_max = 2**nbits - 1
            float_max = np.amax(self.bands[i].data)
            float_min = np.amin(self.bands[i].data)
            
            # correct if the min and max are the same
            if float_max == float_min:
                float_max += 1
            
            self.bands[i].float_max = float_max
            self.bands[i].float_min = float_min
            
        # prepare the headers        
        last_line = "!<header> image -1 $Revision: 1.5 $"

        with open(fileName, 'wb') as f:
            
            # write the global variables
            for l in self._write_basic_image_i():
                f.write(l + '\n')
            
            # write any basic_image headers
            for l in self._write_basic_image():
                f.write(l + '\n')
            
            # write the geo headers, if there
            if self.geohdr is not None:
                for l in self._write_geo_hdr():
                    f.write(l + '\n')
                    
            # write the linear quantization (lq) headers
            for l in self._write_lq_hdr():
                f.write(l + '\n')
                
            # if other headers are required, then put them here
                        
            # write the last header line to the file
            f.write(last_line + '\f\n')

            # Convert the data to a structured array write the binary data
            data = self._convert_float_to_int(nbits)
#             for i in range(data.shape[0]):
#                 data[i,:,:].tofile(f)
            data.tofile(f)

            # close the file
            f.close()
            
            return None


    def _write_basic_image_i(self):
        '''
        Create the first 5 lines of the IPW file for byteorder, nlines, nsamps,
        and nbands
        '''
        firstLine = "!<header> basic_image_i -1 $Revision: 1.11 $"
        
        # byteorder from array to string
        byteorder = ''.join(str(x) for x in self.byteorder) 
        
        firstLines = [firstLine,
                      "byteorder = {0} ".format(byteorder),
                      "nlines = {0} ".format(self.nlines),
                      "nsamps = {0} ".format(self.nsamps),
                      "nbands = {0} ".format(self.nbands)]
        
        return firstLines
        
        
    def _write_basic_image(self):
        '''
        Create the basic_image headers for each band
        
        self.name = None
        self.bytes = None
        self.fmt = None
        self.bits = None
        self.annot = None
        self.history = []
        '''
        
        lines = []
        
        for i, band in enumerate(self.bands):
            lines += ["!<header> basic_image {0} $Revision: 1.11 $".format(i),
                           "bytes = {0} ".format(band.bytes),
                           "bits = {0} ".format(band.bits)]
            
            if band.fmt is not None:
                lines += ["fmt = {0} ".format(band.fmt)]

            if band.annot is not None:
                lines += ['annot = {0} '.format(band.annot)]
            
            if band.history:
                for l in band.history:
                    lines += ["history = {0} ".format(l)]
            
        return lines
    
    
    def _write_lq_hdr(self):
        '''
        Create the linear quantization (lq) headers
        '''
        
        lines = []
        
        # build the linear quantization (lq) headers
        for i, b in enumerate(self.bands):
            int_min = int(b.int_min)
            int_max = int(b.int_max)
    
            # IPW writes integer floats without a dec point, so remove if necessary
            float_min = \
                (b.float_min, int(b.float_min))[b.float_min == int(b.float_min)]
            float_max = \
                (b.float_max, int(b.float_max))[b.float_max == int(b.float_max)]
                
#             if float_max == float_min:
#                 float_max += 1
#                 float_min -= 1
                
            # determine if there are units
            if b.units is not None:
                lines += ["!<header> lq {0} $Revision: 1.6 $".format(i),
                            "units = {0} ".format(b.units), 
                            "map = {0} {1} ".format(int_min, float_min),
                            "map = {0} {1} ".format(int_max, float_max)]
            else:
                lines += ["!<header> lq {0} $Revision: 1.6 $".format(i),
                            "map = {0} {1} ".format(int_min, float_min),
                            "map = {0} {1} ".format(int_max, float_max)]
            
        return lines
    
    
    def _write_geo_hdr(self):
        '''
        Create the geo headers
        '''
        
        lines = []
        
        # build the geographic header
        for i, b in enumerate(self.bands):
            bline = int(b.bline)
            bsamp = int(b.bsamp)
            dline = int(b.dline)
            dsamp = int(b.dsamp)
            units = b.geounits
            coord_sys_ID = b.coord_sys_ID
    
            lines += ["!<header> geo {0} $Revision: 1.7 $".format(i),
                            "bline = {0} ".format(bline),
                            "bsamp = {0} ".format(bsamp),
                            "dline = {0} ".format(dline),
                            "dsamp = {0} ".format(dsamp),
                            "units = {0} ".format(units),
                            "coord_sys_ID = {0} ".format(coord_sys_ID)]
    
        return lines
    
    
    def _convert_float_to_int(self, nbits):
        """
        Convert the data floating point data to mapped integer
        """

        # define a structure array
        dt = np.dtype([(b.name, b.frmt) for b in self.bands])
        data_int = np.zeros((self.nlines, self.nsamps,), dt)


#         data_int = []
        for b in self.bands:
    
            # no need to include b.int_min, it's always zero
            map_fn = lambda x: \
                np.round(
                    ((x - b.float_min) * b.int_max)/(b.float_max - b.float_min))
    
#             data_int.append(map_fn(b.data))
            data_int[b.name] = (map_fn(b.data))
    
        # change to np array with correct datatype
#         x = np.array(data_int)
#         nbytes = self._bits_to_bytes(nbits)
#         x = x.astype('uint' + str(8*nbytes))
#         x = x.astype('int' + str(nbits))

        return data_int
    
    def _bits_to_bytes(self, nbits):
        '''
        Convert bits to equiavalent bytes
        '''
        nbytes = int(ceil(float(nbits)/8))
        
        return nbytes
        

    def __getitem__(self, key):
        return self.bands[self.name_dict[key]]


    def new_band(self, data):
        '''
        Create a new band in IPW that is placed at the end if bands already
        exist.
        '''
        
        # get the size of data
        nlines, nsamps = data.shape
              
        # check if there are other bands
        if self.nbands is not None:
            assert nlines == self.nlines
            assert nsamps == self.nsamps
        else:
#             self.byteorder = [0,1,2,3]
            self.nlines = nlines
            self.nsamps = nsamps
            
               
        # create a new empty band
        band = Band(nlines,nsamps)
        
        # add the data
        band.data = data
        
        # add to the end of IPW bands
        self.bands.append(band)
        
        # adjust the number of band value
        self.nbands = len(self.bands)


    def add_geo_hdr(self, coordinates, d, units, csys, band='all'):
        '''
        Add geo header information to the band
        
        Args:
        coordinates -- [u, v] The coordinates of image line 0 and sample 0 in csys are u and v, respectively.
        d --  [dx, dy] The distances between adjacent image lines and samples in csys are du and dv, respectively.
        units -- u, v, du, and dv are specified in units (e.g., "meters", "km").
        csys -- The geodetic coordinate system identifier is csys (e.g., "UTM", "Lambert").  See the manual for  mkproj
              for a list of standard names for coordinate systems.
        band (optional) -- [0,1,4,...] The "geo" header will be applied only to the specified bands (default: all bands).
        
        if 'all' for band number then do all, or a subset from array?
        
        # geo
        self.bline = None
        self.bsamp = None
        self.dline = None
        self.dsamp = None
        self.geounits = None
        self.coord_sys_ID = None
        self.geotransform = None
        
         mkgeoh -o coord,coord -d incr,incr -u units -c csys [-b band,...] [-f] [image]
        '''
        
        # Check the inputs
        if len(coordinates) != 2:
            raise SyntaxError('Coordinates must have two values [u, v]')
        
        if len(d) != 2:
            raise SyntaxError('d must have two values [du, dv]')
        
        
        if band == 'all':
            band = range(0,self.nbands)     # all bands
        elif type(band) == int:
            band = [band]                   # single band
            
            
            
        # loop through each band and add the header
        for bidx in band:
            
            self.bands[bidx]._parse_geo(coordinates[0],
                                        coordinates[1],
                                        d[0],
                                        d[1],
                                        units,
                                        csys)
            
        self.geohdr = 1
            
#             def _parse_geo(self, L0, L1, L2, L3, L4, L5):
#         """
#         sets attributes and builds GDAL ordered
#         geotransform list
#         """
#         bline = self.bline = _unpackfloat(L0)
#         bsamp = self.bsamp = _unpackfloat(L1)
#         dline = self.dline = _unpackfloat(L2)
#         dsamp = self.dsamp = _unpackfloat(L3)
#         self.geounits = _unpackstr(L4)
#         self.coord_sys_ID = _unpackstr(L5)
#         self.geotransform = [bsamp - dsamp / 2.0,
#                              dsamp, 0.0,
#                              bline - dline / 2.0,
#                              0.0, dline]
#         
        
        
        
        
        
        

#     def colorize(self, dst_fname, band, colormap, ymin=None, ymax=None,
#                  drivername='Gtiff'):
#         """
#         colorize(band[, colormap][, ymin=None][, ymax=None])
# 
#         Build a colorized georeferenced raster of a band
# 
#         Parameters
#         ----------
#         band : int or string
#             index of band, 1st band is "0"
#             string name of raster band e.g. "ro_predicted"
# 
#         colormap : string
#             name of a matplotlib.colors colormap
# 
#         ymin : None or float
#             float specifies the min value for normalization
#             None will use min value of data
# 
#         ymax : None or float
#             float specifies the max value for normalization
#             None will use max value of data
#         """
#         bands = self.bands
#         nsamps, nlines = self.nsamps, self.nlines
# 
#         # find band
#         try:
#             band = bands[int(band)]
#         except:
#             band = self[band]
# 
#         # build normalize function
#         if ymin is None:
#             ymin = (0.0, band.float_min)[self.rescale]
# 
#         if ymax is None:
#             ymax = (2.0**band.bits - 1.0, band.float_max)[self.rescale]
# 
#         assert ymax > ymin
# 
#         norm_func = Normalize(ymin, ymax, clip=True)
# 
#         # colorize band
#         cm = plt.get_cmap(colormap)
#         rgba = np.array(cm(norm_func(band.data)) * 255.0, dtype=np.uint8)
# 
#         # find geotransform
#         for b in bands:
#             gt0 = b.geotransform
#             if gt0 is not None:
#                 break
# 
#         # initialize raster
#         driver = GetDriverByName(drivername)
#         ds = driver.Create(dst_fname, nsamps, nlines,
#                            4, gdalconst.GDT_Byte)
# 
#         # set projection
#         if epsg is not None:
#             proj = osr.SpatialReference()
#             status = proj.ImportFromEPSG(epsg)
#             if status != 0:
#                 warnings.warn('Importing epsg %i return error code %i'
#                               % (epsg, status))
#             ds.SetProjection(proj.ExportToWkt())
# 
#         # set geotransform
#         if gt0 is None:
#             warnings.warn('Unable to find a geotransform')
#         else:
#             # set transform
#             ds.SetGeoTransform(gt0)
# 
#         # write data
#         for i in xrange(4):
#             ds.GetRasterBand(i+1).WriteArray(rgba[:, :, i])
# 
#         ds = None  # Writes and closes file

#     def translate(self, dst_fname, writebands=None,
#                   drivername='Gtiff', multi=True):
#         """
#         translate(dst_dataset[, bands=None][, drivername='GTiff']
#                   [, multi=True])
# 
#         translates the data to a georeferenced tif.
# 
#         Parameters
#         ----------
#         dst_fname : string
#            path to destination file without extension.
#            Assumes folder exists.
# 
#         writebands : None or iterable of integers
#             Specifies which bands to write to file.
#             Bands are written in the order specifed.
# 
#             If none, all bands will be written to file
#             The first band is "0" (like iSNOBAL, not like GDAL)
# 
#         multi : bool (default True)
#             True write each band to its own dataset
#             False writes all the bands to a single dataset
#         """
#         if writebands is None:
#             writebands = range(self.nbands)
# 
#         if multi:
#             for i in writebands:
#                 self._translate(dst_fname + '.%02i'%i, [i], drivername)
#         else:
#             self._translate(dst_fname, writebands, drivername)
# 
#     def _translate(self, dst_fname, writebands=None, drivername='Gtiff'):
#         epsg = self.epsg
#         rescale = self.rescale
#         bands = self.bands
#         nbands = self.nbands
#         nlines, nsamps = self.nlines, self.nsamps
# 
#         if writebands is None:
#             writebands = range(nbands)
# 
#         num_wb = len(writebands)
# 
#         assert num_wb >= 1
# 
#         # The first band of the inputs doesn't have a
#         # geotransform. I'm sure this is a feature and not a bug ;)
#         #
#         # Check to make sure the defined geotransforms are the same
#         #
#         # Haven't really found any cases where multiple bands have
#         # different projections. Is this really a concern?
#         gt_override = 0
# 
#         # search write bands for valid transform
#         for i in writebands:
#             gt0 = bands[i].geotransform
#             if gt0 is not None:
#                 break
# 
#         if gt0 is None:
#             # search all bands for valid transform
#             for b in bands:
#                 gt0 = b.geotransform
#                 if gt0 is not None:
#                     gt_override = 1
#                     break
#             if gt0 is None:
#                 raise Exception('No Projection Found')
#             else:
#                 warnings.warn('Using Projection from another band')
# 
#         if not gt_override:
#             for i in writebands:
#                 gt = bands[i].geotransform
#                 if gt is None:
#                     continue
#                 assert_array_almost_equal(gt0, gt)
# 
#         # If the data hasn't been rescaled all bands are written as
#         # Float 32. If the data has not been scaled the type is
#         # Uint8 if all channels are Uint8 and Uint16 otherwise
#         if rescale:
#             gdal_type = gdalconst.GDT_Float32
#         else:
#             if all([bands[i].bytes == 1 for i in writebands]):
#                 gdal_type = gdalconst.GDT_Byte
#             else:
#                 gdal_type = gdalconst.GDT_UInt16
# 
#         # initialize raster
#         driver = gdal.GetDriverByName(drivername)
#         ds = driver.Create(dst_fname + '.tif', nsamps, nlines,
#                            num_wb, gdal_type)
# 
#         # set projection
#         if epsg is not None:
#             proj = osr.SpatialReference()
#             status = proj.ImportFromEPSG(epsg)
#             if status != 0:
#                 warnings.warn('Importing epsg %i return error code %i'
#                               %(epsg, status))
#             ds.SetProjection(proj.ExportToWkt())
# 
#         # set geotransform
#         ds.SetGeoTransform(gt0)
# 
#         # write data
#         j = 1
#         for i in writebands:
#             ds.GetRasterBand(j).WriteArray(bands[i].data)
#             j += 1
# 
#         ds = None  # Writes and closes file

    def __str__(self):
        s = ['''\
IPW({0.fname})
---------------------------------------------------------
byteorder: {0.byteorder}
nlines: {0.nlines}
nsamps: {0.nsamps}
nbands: {0.nbands}
'''.format(self)]

        for i, b in enumerate(self.bands):
            s.append('\nBand %i\n'%i)
            s.append(str(b))

        return ''.join(s)


def _packgrp(root, grp, wc, varlist, nbands=None):
    fns = glob(wc)

    assert len(fns) > 0

    ipw0 = IPW(fns[0])
    shape = (ipw0.nlines * ipw0.nsamps,
             len(fns),
             (nbands, ipw0.nbands)[nbands is None])
    data = np.zeros(shape, np.float32)

    for i, fn in enumerate(fns):
        ipw = IPW(fn)
        for j, b in enumerate(ipw.bands):
            assert varlist[j] == b.name
            data[:, i, j] = b.data.flatten()

    root.create_group(grp)
    for i, key in enumerate(varlist):
        root[grp].create_dataset(key, data=data[:, :, i])


# def packToHd5(in_path, out_path=None, fname=None):
#     """
#     packToHd5(in_path[, out_path][, fname=None])
# 
#     Packs input and output data into an hdf5 container
# 
#     Parameters
#     in_path : string
#         path to file containing input IPW files
# 
#     out_path : string
#         path to file containing output IPW files
# 
#     """
#     if fname is None:
#         fname = 'insnobal_data.hd5'
# 
#     if not os.path.isdir(in_path):
#         raise Exception('in_path should be a directory')
# 
#     if out_path is None:
#         out_path = in_path
# 
#     if not os.path.isdir(out_path):
#         raise Exception('out_path should be a directory')
# 
#     root = h5py.File(fname, 'w')
# 
#     # Process in_db files
#     # Some of the input files have 5 bands, some have 6
#     wc = os.path.join(in_path, 'in.*')
#     _packgrp(root, 'in_db', wc, in_db__vars, nbands=6)
# 
#     # Process out_em files
#     wc = os.path.join(out_path, 'em.*')
#     _packgrp(root, 'out_em', wc, out_em__vars)
# 
#     # Process out_snow files
#     wc = os.path.join(out_path, 'snow.*')
#     _packgrp(root, 'out_snow', wc, out_snow__vars)
# 
#     root.close()
#     

