Create a Topo
=============

The topo provides SMRF with the following static layers:

1. Digital elevation model
2. Vegetation type
3. Vegetation height
4. Vegetation extinction coefficient
5. Vegetation optical transmissivity
6. Basin mask (optional)

All these layers are stored in a netCDF file, typically referred to the ``topo.nc`` file.

.. note::

    The ``topo.nc`` *must* have projection information. It's just good practice.

Generating the topo
-------------------

While the ``topo.nc`` file can be generated manually, a great option is to use `basin_setup <https://github.com/USDA-ARS-NWRC/basin_setup>`_
which creates a topo file that is compatible with SMRF and AWSM. To get a minimal topo file generated, the following are necessary:

1. Pour point file in ``bna`` format
2. Docker

``basin_setup`` will perform auto basin delineation for the watershed and will output shapefiles for the basin and sub basins. Next,
``basin_setup`` will generate the ``topo.nc`` file with all the necessary variables for SMRF.

See the ``basin_setup`` `documentation <https://github.com/USDA-ARS-NWRC/basin_setup>`_ for more details.

Vegetation
----------

The vegetation data comes from the `LandFire dataset <https://www.landfire.gov/>`_ and contains the vegetation type and height
at 30 meters. The vegetation is important in the following locations within SMRF

1. Adds sheltering in the wind distribution in the :mod:`Winstral wind model <smrf.distribute.wind.winstral>`
2. WindNinja log law roughness :mod:`scaling <smrf.distribute.wind.wind_ninja>`
3. Precipitation redistribution interference in the :mod:`Winstral precipitation <smrf.distribute.precipitation>` rescaling model
4. Albedo :mod:`decay date method <smrf.envphys.radiation.decay_alb_power>`
5. Vegetation correction to :mod:`solar radiation <smrf.distribute.solar>`
6. Vegetation correction to :mod:`thermal radiation <smrf.distribute.thermal>`

Vegetation type is configured in SMRF as ``veg_<type>``. For example, to add sheltering for vegetation type 3011, the configuration
option ``veg_3011`` will be set to the value needed, say ``10.0``. SMRF will apply the value ``10.0`` to any cells with vegetation
type 3011.