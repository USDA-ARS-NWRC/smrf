import numpy as np


class Susong1999:
    """
    Follows the IPW command mkprecip

    The precipitation phase, or the amount of precipitation falling as rain or
    snow, can significantly alter the energy and mass balance of the snowpack,
    either leading to snow accumulation or inducing melt :cite:`Marks&al:1998`
    :cite:`Kormos&al:2014`. The precipitation phase and initial snow density
    are based on the precipitation temperature (the distributed dew point
    temperature) and are estimated after Susong et al (1999)
    :cite:`Susong&al:1999`. The table below shows the relationship to
    precipitation temperature:

    ========= ======== ============ ===============
    Min Temp  Max Temp Percent snow Snow density
    [deg C]   [deg C]  [%]          [kg/m^3]
    ========= ======== ============ ===============
    -Inf      -5       100          75
    -5        -3       100          100
    -3        -1.5     100          150
    -1.5      -0.5     100          175
    -0.5      0        75           200
    0         0.5      25           250
    0.5       Inf      0            0
    ========= ======== ============ ===============
    """

    # Above table
    TABLE = [
        {
            'temp_min': -1e309,
            'temp_max': -5,
            'snow': 1,
            'density': 75
        },
        {
            'temp_min': -5,
            'temp_max': -3,
            'snow': 1,
            'density': 100
        },
        {
            'temp_min': -3,
            'temp_max': -1.5,
            'snow': 1,
            'density': 150
        },
        {
            'temp_min': -1.5,
            'temp_max': -0.5,
            'snow': 1,
            'density': 175
        },
        {
            'temp_min': -0.5,
            'temp_max': 0.0,
            'snow': 0.75,
            'density': 200
        },
        {
            'temp_min': 0.0,
            'temp_max': 0.5,
            'snow': 0.25,
            'density': 250
        },
        {
            'temp_min': 0.5,
            'temp_max': 1e309,
            'snow': 0,
            'density': 0
        }
    ]

    @staticmethod
    def run(temperature, precipitation):
        """
        Args:
            precipitation - numpy array of precipitation values [mm]

            temperature - array of temperature values, use dew point
                temperature if available [degrees C]

        Returns:
            dictionary:
           - **percent_snow** (*numpy.array*) - Percent of the precipitation
                that is snow in values 0.0-1.0.
           - **rho_s** (*numpy.array*) - Snow density values in kg/m^3.
        """
        ps = np.zeros(precipitation.shape)
        sd = np.zeros(ps.shape)

        # if no precipitation return all zeros
        if np.sum(precipitation) == 0:
            return {'pcs': ps, 'rho_s': sd}

        # Determine the indices and allocate based on the table above
        for row in Susong1999.TABLE:

            # Get values between the temperature ranges that have precipitation
            ind = ((temperature >= row['temp_min'])
                   & (temperature < row['temp_max']))
            # set the percent snow
            ps[ind] = row['snow']

            # set the density
            sd[ind] = row['density']

        # If there is no precipitation at a pixel, don't report a value
        # this may make isnobal crash, I'm not really sure
        ps[precipitation == 0] = 0
        sd[precipitation == 0] = 0

        return {'pcs': ps, 'rho_s': sd}
