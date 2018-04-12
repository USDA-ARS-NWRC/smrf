"""
Created on Apr 7, 2015

Adapted from Roger Lew (rogerlew.gmail.com)isnobal.py

@author: Scott Havens
"""

from glob import glob
import os
import sys
import numpy as np
from math import ceil


in_db__vars = tuple('I_lw T_a e_a u T_g S_n'.split())
out_em__vars = tuple('R_n H L_v_E G M delta_Q E_s '
                     'melt ro_predict cc_s'.split())
out_snow__vars = tuple('z_s rho m_s h2o T_s_0 T_s_l T_s z_s_l h2o_sat'.split())


def _unpackindx(L):
    return int(L.split()[2])


def _unpackint(L):
    return int(L.split('=')[1].strip())


def _unpackfloat(L):
    return float(L.split('=')[1].strip())


def _unpackstr(L):
    return L.split('=')[1].strip()


def _decode(s):
    return s.decode('utf-8')


def map_fn(x, float_min, float_max, int_min, int_max):
    return np.round(((x - float_min) * (int_max - int_min)) /
                    (float_max - float_min))


# _unpackindx  = lambda L: int(L.split()[2])
# _unpackint   = lambda L: int(L.split('=')[1].strip())
# _unpackfloat = lambda L: float(L.split('=')[1].strip())
# _unpackstr   = lambda L: L.split('=')[1].strip()
# _decode      = lambda s: s.decode('utf-8')


# for reading binary files
PY_VERSION = 2
if sys.version_info > (3, 0):
    PY_VERSION = 3


def readline3(fid):
    """
    Read a line from a binary file in Python3 and decode
    """
    return fid.readline().decode('utf-8')


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
        int_min, float_min, int_max, float_max = \
            map(float, [int_min, float_min, int_max, float_max])
        self.transform = \
            lambda x: (float_max - float_min) * (x / int_max) + float_min
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

        # this should just be stored as an attribute
        # it produces alot of book-keeping otherwise
        self.epsg = epsg

        # read a file or create an empty object
        if fname is not None:
            if PY_VERSION == 2:
                self.read(fname)
            else:
                self.read3(fname)

        else:
            self.fname = None
            self.bands = []
            self.bip = None
            self.byteorder = [0, 1, 2, 3]
            self.nlines = None
            self.nsamps = None
            self.nbands = None
            self.geohdr = None

    def read(self, fname):
        """
        Read the IPW file into the various bands
        Turns the data into a numpy array of float32
        """

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
            line = _decode(readline())

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
                bands = [Band(nlines, nsamps) for j in range(nbands)]

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

                    if len(line) == 0:
                        break

                # set pointer back one line
                fid.seek(last_pos)

            elif '!<header> geo' in line:
                indx = _unpackindx(line)
                bands[indx]._parse_geo_readline(
                    *[readline() for i in range(6)])
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
            varlist = ['band%02i' % i for i in range(nbands)]

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

    def read3(self, fname):
        """
        Read the IPW file into the various bands
        Turns the data into a numpy array of float32
        This is meant for Python3 which has different ways
        of ready binary files than Python2
        """

        # read the data to a list of lines
        fid = open(fname, 'rb')

        bands = []
        byteorder = None
        nlines = None
        nsamps = None
        nbands = None
        geo = None

        # size of the file we are reading in bytes
        st_size = os.fstat(fid.fileno()).st_size
        while 1:  # while 1 is faster than while True
            line = readline3(fid)

            # fail safe, haven't needed it, but if this is running
            # on a server not a bad idea to have it here
            if fid.tell() == st_size:
                raise Exception('Unexpectedly reached EOF')

            if '!<header> basic_image_i' in line:
                byteorder = list(map(int,
                                     readline3(fid).split('=')[1].strip()))
                nlines = _unpackint(readline3(fid))
                nsamps = _unpackint(readline3(fid))
                nbands = _unpackint(readline3(fid))

                # initialize the band instances in the bands list
                bands = [Band(nlines, nsamps) for j in range(nbands)]

            elif '!<header> basic_image' in line:
                indx = _unpackindx(line)    # band number
                bytes = bands[indx].bytes = _unpackint(readline3(fid))
#                 bands[indx].frmt = ('uint8', 'uint16')[bytes == 2]
                bands[indx].frmt = 'uint' + str(bytes*8)
                bands[indx].bits = _unpackint(readline3(fid))

                # see if there is any other information
                last_pos = fid.tell()
                line = readline3(fid)

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
                    line = readline3(fid)

                    if len(line) == 0:
                        break

                # set pointer back one line
                fid.seek(last_pos)

            elif '!<header> geo' in line:
                indx = _unpackindx(line)
                bands[indx]._parse_geo_readline(
                    *[readline3(fid) for i in range(6)])
                geo = 1

            elif '!<header> lq' in line:
                indx = _unpackindx(line)
                line1 = readline3(fid)
                if 'units' in line1:
                    bands[indx].units = _unpackstr(line1)

                    bands[indx]._parse_lq(_unpackstr(readline3(fid)),
                                          _unpackstr(readline3(fid)))
                else:
                    bands[indx]._parse_lq(_unpackstr(line1),
                                          _unpackstr(readline3(fid)))

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
            varlist = ['band%02i' % i for i in range(nbands)]

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
        assert (st_size - fid.tell()) >= required_bytes

        # this is way faster than looping with struct.unpack
        # struct.unpack also starts assuming there are pad bytes
        # when format strings with different types are supplied
        data = np.fromfile(fid, dt, count=nlines*nsamps)

        # Separate into bands
        data = data.reshape(nlines, nsamps)
        for b in bands:
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

        Args:
            fileName - file to write to
            nbits - number of bits for each band default=8
        """

        # set the bits, bytes, and int_max for each band
        # have to convert nbits one to float then back at the end
        # for ceil to work
        for i, b in enumerate(self.bands):
            self.bands[i].name = 'band%02i' % i
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

        with open(fileName, 'w') as f:

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
        """
        Create the first 5 lines of the IPW file for byteorder, nlines, nsamps,
        and nbands
        """
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
        """
        Create the basic_image headers for each band

        self.name = None
        self.bytes = None
        self.fmt = None
        self.bits = None
        self.annot = None
        self.history = []
        """

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
        """
        Create the linear quantization (lq) headers
        """

        lines = []

        # build the linear quantization (lq) headers
        for i, b in enumerate(self.bands):
            int_min = int(b.int_min)
            int_max = int(b.int_max)

            # IPW writes integer floats without a dec point,
            # so remove if necessary
            float_min = int_match(b.float_min)
            float_max = int_match(b.float_max)

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
        """
        Create the geo headers
        """

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
            data_int[b.name] = map_fn(b.data,
                                      b.float_min,
                                      b.float_max,
                                      0,
                                      b.int_max)

        return data_int

    def _bits_to_bytes(self, nbits):
        """
        Convert bits to equiavalent bytes
        """
        return int(ceil(float(nbits)/8))

    def __getitem__(self, key):
        return self.bands[self.name_dict[key]]

    def new_band(self, data):
        """
        Create a new band in IPW that is placed at the end if bands already
        exist.
        """

        # get the size of data
        nlines, nsamps = data.shape

        # check if there are other bands
        if self.nbands is not None:
            assert nlines == self.nlines
            assert nsamps == self.nsamps
        else:
            # self.byteorder = [0,1,2,3]
            self.nlines = nlines
            self.nsamps = nsamps

        # create a new empty band
        band = Band(nlines, nsamps)

        # add the data
        band.data = data

        # add to the end of IPW bands
        self.bands.append(band)

        # adjust the number of band value
        self.nbands = len(self.bands)

    def add_geo_hdr(self, coordinates, d, units, csys, band='all'):
        """
        Add geo header information to the band

        Args:
            coordinates: [u, v] The coordinates of image line 0 and sample 0
                in csys are u and v, respectively.
            d: [dx, dy] The distances between adjacent image lines and samples
                in csys are du and dv, respectively.
            units: u, v, du, and dv are specified in units (e.g., "meters",
                "km").
            csys: The geodetic coordinate system identifier is csys (e.g.,
                "UTM", "Lambert").  See the manual for  mkproj for a list of
                standard names for coordinate systems.
            band (optional): [0,1,4,...] The "geo" header will be applied only
                to the specified bands (default: all bands).

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
        """

        # Check the inputs
        if len(coordinates) != 2:
            raise SyntaxError('Coordinates must have two values [u, v]')

        if len(d) != 2:
            raise SyntaxError('d must have two values [du, dv]')

        if band == 'all':
            band = range(0, self.nbands)     # all bands
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
            s.append('\nBand %i\n' % i)
            s.append(str(b))

        return ''.join(s)

def int_match(val):
    """
    (Devel team is unsure if this is the case. This description is our
    interpretation of pre-existing code that was re-written to be up-to-date
    with deprecations. We are confident it behaves the same as it did before.)

    IPW writes in the header a integer represented as a float in python without
    the decimal. So sometimes we have to proactively check and pass a int to
    the header function.

    e.g. float_min == 1.00, IPW writes 1
    Args:
        val: an potential int represented as float.
    Returns:
        result: the val is casted as int if val is equivalent to itself casted
                as an int
    """
    int_val = int(val)
    return int_val if val == int_val else val




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
