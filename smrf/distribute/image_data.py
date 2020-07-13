import logging

import numpy as np

from smrf.spatial import dk, grid, idw, kriging


class image_data():
    """
    A base distribution method in SMRF that will ensure all variables are
    distributed in the same manner.  Other classes will be initialized
    using this base class.

    .. code-block:: Python

        class ta(smrf.distribute.image_data):
            '''
            This is the ta class extending the image_data base class
            '''

    Args:
        variable (str): Variable name for the class

    Returns:
        A :mod:`!smrf.distribute.image_data` class instance

    Attributes:
        variable: The name of the variable that this class will become
        [variable_name]: The :py:attr:`variable` will have the distributed data
        [other_attribute]: The distributed data can also be stored as another
            attribute specified in
            :mod:`~smrf.distribute.image_data._distribute`
        config: Parsed dictionary from the configuration file for the variable
        stations: The stations to be used for the variable, if set, in
            alphabetical order
        metadata: The metadata Pandas dataframe containing the station
            information from :mod:`smrf.data.loadData` or
            :mod:`smrf.data.loadGrid`
        idw: Inverse distance weighting instance from
            :mod:`smrf.spatial.idw.IDW`
        dk: Detrended kriging instance from :mod:`smrf.spatial.dk.dk.DK`
        grid: Gridded interpolation instance from :mod:`smrf.spatial.grid.GRID`

    """

    BASE_THREAD_VARIABLES = frozenset()
    OUTPUT_VARIABLES = {}

    def __init__(self, variable):

        self.variable = variable
        setattr(self, variable, None)

        self.gridded = False

        self._logger = logging.getLogger(self.__class__.__module__)
        self._thread_variables = None

    @property
    def thread_variables(self):
        if self._thread_variables is None:
            self._thread_variables = list(self.BASE_THREAD_VARIABLES)

        return self._thread_variables

    @thread_variables.setter
    def thread_variables(self, value):
        self._thread_variables = value

    def add_thread_variables(self, variables):
        """Add a list or single variable to the thread variables

        Args:
            variables (list or str): List or string of variables to add
        """

        if isinstance(variables, str):
            variables = list((variables, ))

        self.thread_variables = self.thread_variables + variables

    @property
    def output_variables(self):
        ov = {}
        for key, value in self.OUTPUT_VARIABLES.items():
            value['module'] = self.__class__.__module__.split('.')[-1]
            ov[key] = value
        return ov

    def getConfig(self, cfg):
        """
        Check the configuration that was set by the user for the variable
        that extended this class. Checks for standard distribution parameters
        that are common across all variables and assigns to the class instance.
        Sets the :py:attr:`config` and :py:attr:`stations` attributes.

        Args:
            cfg (dict): dict from the [variable]
        """

        # check of gridded interpolation
        self.gridded = False
        if 'distribution' in cfg.keys():
            if cfg['distribution'] == 'grid':
                self.gridded = True

        self.getStations(cfg)
        self.config = cfg

    def getStations(self, config):
        """
        Determines the stations from the [variable] section of the
        configuration file.

        Args:
            config (dict): dict from the [variable]
        """
        stations = None

        # determine the stations that will be used, alphabetical order
        if "stations" in config.keys():
            if config["stations"] is not None:
                stations = config['stations'].sort()

        self.stations = stations

    def _initialize(self, topo, metadata):
        """
        Initialize the distribution based on the parameters in
        :py:attr:`config`.

        Args:
            topo: :mod:`smrf.data.loadTopo.Topo` instance contain topographic
                data and infomation
            metadata: metadata Pandas dataframe containing the station metadata
                from :mod:`smrf.data.loadData` or :mod:`smrf.data.loadGrid`

        Raises:
            Exception: If the distribution method could not be determined, must
                be idw, dk, or grid

        To do:
            - make a single call to the distribution initialization
            - each dist (idw, dk, grid) takes the same inputs and returns the
                same
        """

        self.min = self.config['min']
        if self.min is None:
            self.min = -np.inf

        self.max = self.config['max']
        if self.max is None:
            self.max = np.inf

        # pull out the metadata subset
        if self.stations is not None:
            metadata = metadata.loc[self.stations]
        else:
            self.stations = metadata.index.values
        self.metadata = metadata

        # Old DB used X and Y, New DB uses utm_x, utm_y
        try:
            self.mx = metadata.utm_x.values
            self.my = metadata.utm_y.values
        except Exception:
            self.mx = metadata.X.values
            self.my = metadata.Y.values

        self.mz = metadata.elevation.values

        if "distribution" in self.config.keys():
            if self.config['distribution'] == 'idw':
                # inverse distance weighting
                self.idw = idw.IDW(
                    self.mx, self.my, topo.X, topo.Y, mz=self.mz,
                    GridZ=topo.dem, power=self.config['idw_power'])

            elif self.config['distribution'] == 'dk':
                # detrended kriging
                self.dk = dk.DK(
                    self.mx, self.my, self.mz, topo.X, topo.Y,
                    topo.dem,
                    self.config)

            elif self.config['distribution'] == 'grid':
                # linear interpolation between points
                self.grid = grid.GRID(
                    self.config, self.mx, self.my, topo.X,
                    topo.Y,
                    mz=self.mz,
                    GridZ=topo.dem,
                    mask=topo.mask,
                    metadata=metadata)

            elif self.config['distribution'] == 'kriging':
                # generic kriging
                self.kriging = kriging.KRIGE(
                    self.mx, self.my, self.mz, topo.X,
                    topo.Y,
                    topo.dem,
                    self.config)

            else:
                raise Exception(
                    "Could not determine the distribution method for "
                    "{}".format(self.variable))

    def _distribute(self, data, other_attribute=None, zeros=None):
        """
        Distribute the data using the defined distribution method in
        :py:attr:`config`

        Args:
            data: Pandas dataframe for a single time step
            other_attribute (str): By default, the distributed data matrix goes
                into self.variable but this specifies another attribute in self
            zeros: data values that should be treated as zeros (not used)

        Raises:
            Exception: If all input data is NaN
        """

        # get the data for the desired stations
        # this will also order it correctly how air_temp was initialized
        data = data[self.stations]

        if np.sum(data.isnull()) == data.shape[0]:
            raise Exception("{}: All data values are NaN"
                            "".format(self.variable))

        if self.config['distribution'] == 'idw':
            if self.config['detrend']:
                v = self.idw.detrendedIDW(
                    data.values,
                    self.config['detrend_slope'],
                    zeros=zeros)
            else:
                v = self.idw.calculateIDW(data.values)

        elif self.config['distribution'] == 'dk':
            v = self.dk.calculate(data.values)

        elif self.config['distribution'] == 'grid':
            if self.config['detrend']:
                v = self.grid.detrendedInterpolation(
                    data,
                    self.config['detrend_slope'],
                    self.config['grid_method'])
            else:
                v = self.grid.calculateInterpolation(
                    data.values,
                    self.config['grid_method'])

        elif self.config['distribution'] == 'kriging':
            v, ss = self.kriging.calculate(data.values)
            setattr(self, '{}_variance'.format(self.variable), ss)

        if other_attribute is not None:
            setattr(self, other_attribute, v)
        else:
            setattr(self, self.variable, v)

    def post_processor(self, output_func):
        """
        Each distributed variable has the oppurtunity to do post processing on
        a sub variable. This is necessary in cases where the post proecessing
        might need to be done on a different timescale than that of the main
        loop.

        Should be redefined in the individual variable module.
        """
        pass
