import numpy as np

from .utils import check_temperature
from .piecewise_suosong_1999 import PiecewiseSusong1999


class Marks2017:
    """
    A new accumulated snow density model that accounts for compaction. The
    model builds upon :func:`~smrf.envphys.snow.piecewise_susong1999` by
    adding effects from compaction. Of four mechanisms for compaction, this
    model accounts for compaction by destructive metamorphism and overburden.
    These two processes are accounted for by calculating a proportionality
    using data from Kojima, Yosida and Mellor. The overburden is in part
    estimated using total storm deposition, where storms are defined in
    :func:`~smrf.envphys.storms.tracking_by_station`. Once this is determined
    the final snow density is applied through the entire storm only varying
    with hourly temperature.

    Snow Density:
        .. math::
            \\rho_{s} = \\rho_{ns} + (\\Delta \\rho_{c} + \\Delta
            \\rho_{m}) \\rho_{ns}

    Overburden Proportionality:
        .. math::
            \\Delta \\rho_{c} = 0.026 e^{-0.08 (T_{z} - T_{snow})}
            SWE*  e^{-21.0 \\rho_{ns}}

    Metamorphism Proportionality:
        .. math::
            \\Delta \\rho_{m} = 0.01 c_{11} e^{-0.04 (T_{z} - T_{snow})}

            c_{11} = c_min + (T_{z} - T_{snow}) C_{factor} + 1.0

    Constants:
        .. math::
            C_{factor} = 0.0013

            Tz = 0.0

            ex_{max} = 1.75

            exr = 0.75

            ex_{min} = 1.0

            c1r = 0.043

            c_{min} = 0.0067

            c_{fac} = 0.0013

            T_{min} = -10.0

            T_{max} = 0.0

            T_{z} = 0.0

            T_{r0} = 0.5

            P_{cr0} = 0.25

            P_{c0} = 0.75
    """

    # These should be used but unsure why not
    # ex_max = 1.75
    # exr = 0.75
    # ex_min = 1.0
    # #c1_min = 0.026
    # #c1_max = 0.069
    # c1r = 0.043
    # c_min = 0.0067
    # cfac = 0.0013
    T_MIN = -10.0
    T_MAX = 0.0
    TZ = 0.0
    # Tr0 = 0.5
    # Pcr0 = 0.25
    # Pc0 = 0.75

    RHO_WATER = 1000.0

    @staticmethod
    def run(tpp, pp):
        """
        Args:
            tpp: Numpy array of a single hour of temperature, use dew point if
                available [degrees C].
            pp: Numpy array representing the total amount of precipitation
                deposited during a storm in millimeters

        Returns:
            dictionary:
              - **rho_s** (*numpy.array*) - Density of the fresh snow in
                  kg/m^3.
              - **swe** (*numpy.array*) - Snow water equivalent.
              - **pcs** (*numpy.array*) - Percent of the precipitation that is
                  snow in values 0.0-1.0.
              - **rho_ns** (*numpy.array*) - Density of the uncompacted snow,
                  which is equivalent to the output from
                  :func:`~smrf.envphys.snow.piecewise_susong1999`.
              - **d_rho_c** (*numpy.array*) - Proportional coefficient for
                  compaction from overburden.
              - **d_rho_m** (*numpy.array*) - Proportional coefficient for
                  compaction from melt.
              - **rho_s** (*numpy.array*) - Final density of the snow [kg/m^3].
              - **rho** (*numpy.array*) - Density of the precipitation, which
                  continuously ranges from low density snow to pure liquid
                  water
                  (50-1000 kg/m^3).
              - **zs** (*numpy.array*) - Snow height added from the
                  precipitation

        """

        rho_ns = d_rho_m = d_rho_c = zs = rho_s = swe = pcs = np.zeros(
            tpp.shape
        )
        rho = np.ones(tpp.shape)

        if np.any(pp > 0):

            # check the precipitation temperature
            tpp, tsnow = check_temperature(
                tpp, t_max=Marks2017.T_MAX, t_min=Marks2017.T_MIN
            )

            # Calculate the percent snow and initial uncompacted density
            result = PiecewiseSusong1999.run(
                tpp, pp, t_max=Marks2017.T_MAX, t_min=Marks2017.T_MIN
            )
            pcs = result['pcs']
            rho_orig = result['rho_s']

            swe = pp * pcs

            # Calculate the density only where there is swe
            swe_ind = swe > 0.0
            if np.any(swe_ind):

                s_pcs = pcs[swe_ind]
                s_pp = pp[swe_ind]
                s_swe = swe[swe_ind]
                # transforms to a 1D array, will put back later
                s_tsnow = tsnow[swe_ind]

                # transforms to a 1D array, will put back later
                s_rho_ns = rho_orig[swe_ind]

                # Convert to a percentage of water
                s_rho_ns = s_rho_ns/Marks2017.RHO_WATER

                # proportional total storm mass compaction
                s_d_rho_c = (0.026 * np.exp(-0.08 * (Marks2017.TZ - s_tsnow))
                             * s_swe * np.exp(-21.0 * s_rho_ns))

                ind = (s_rho_ns * Marks2017.RHO_WATER) >= 100.0
                c11 = np.ones(s_rho_ns.shape)

                # c11[ind] = (c_min + ((Tz - s_tsnow[ind]) * cfac)) + 1.0

                c11[ind] = np.exp(-0.046*(s_rho_ns[ind]*1000.0-100.0))

                s_d_rho_m = 0.01 * c11 * np.exp(
                    -0.04 * (Marks2017.TZ - s_tsnow)
                )

                # Snow density, depth & combined liquid and snow density
                s_rho_s = s_rho_ns + ((s_d_rho_c + s_d_rho_m) * s_rho_ns)

                s_zs = s_swe / s_rho_s

                # a mixture of snow and liquid
                s_rho = s_rho_s.copy()
                mix = (s_swe < s_pp) & (s_pcs > 0.0)
                if np.any(mix):
                    s_rho[mix] = \
                        (s_pcs[mix] * s_rho_s[mix]) + (1.0 - s_pcs[mix])

                s_rho[s_rho > 1.0] = 1.0

                # put the values back into the larger array
                rho_ns[swe_ind] = s_rho_ns
                d_rho_m[swe_ind] = s_d_rho_m
                d_rho_c[swe_ind] = s_d_rho_c
                zs[swe_ind] = s_zs
                rho_s[swe_ind] = s_rho_s
                rho[swe_ind] = s_rho
                pcs[swe_ind] = s_pcs

        # convert densities from proportions, to kg/m^3 or mm/m^2
        rho_ns = rho_ns * Marks2017.RHO_WATER
        rho_s = rho_s * Marks2017.RHO_WATER
        rho = rho * Marks2017.RHO_WATER

        return {
            'swe': swe,
            'pcs': pcs,
            'rho_ns': rho_ns,
            'd_rho_c': d_rho_c,
            'd_rho_m': d_rho_m,
            'rho_s': rho_s,
            'rho': rho,
            'zs': zs
        }
