import math

import numpy as np

from smrf.utils.io import isint

# define some constants
MAXV = 1.0              # vis albedo when gsize = 0
MAXIR = 0.85447         # IR albedo when gsize = 0
IRFAC = -0.02123        # IR decay factor
VFAC = 500.0            # visible decay factor
VZRG = 1.375e-3         # vis zenith increase range factor
IRZRG = 2.0e-3          # ir zenith increase range factor
IRZ0 = 0.1              # ir zenith increase range, gsize=0
BOIL = 373.15           # boiling temperature K
GRAVITY = 9.80665       # gravity (m/s^2)


def growth(t):
    """
    Calculate grain size growth
    From IPW albedo > growth
    """

    a = 4.0
    b = 3.
    c = 2.0
    d = 1.0

    factor = (a+(b*t)+(t*t))/(c+(d*t)+(t*t)) - 1.0

    return(1.0 - factor)


def albedo(telapsed, cosz, gsize, maxgsz, dirt=2):
    """
    Calculate the abedo, adapted from IPW function albedo

    Args:
        telapsed - time since last snow storm (decimal days)
        cosz - cosine local solar illumination angle matrix
        gsize - gsize is effective grain radius of snow after last storm (mu m)
        maxgsz - maxgsz is maximum grain radius expected from grain growth
                  (mu m)
        dirt - dirt is effective contamination for adjustment to visible
               albedo (usually between 1.5-3.0)

    Returns:
        tuple:
        Returns a tuple containing the visible and IR spectral albedo

        - **alb_v** (*numpy.array*) - albedo for visible specturm

        - **alb_ir** (*numpy.array*) -  albedo for ir spectrum

    Created April 17, 2015
    Modified July 23, 2015 - take image of cosz and calculate albedo for
        one time step
    Scott Havens

    """

#     telapsed = np.array(telapsed)

    # check inputs
    if gsize <= 0 or gsize > 500:
        raise Exception("unrealistic input: gsize=%i", gsize)

    if (maxgsz <= gsize or maxgsz > 2000):
        raise Exception("unrealistic input: maxgsz=%i", maxgsz)

    if 1 >= dirt >= 10:
        raise Exception("unrealistic input: dirt=%i", dirt)

    # set initial grain radii for vis and ir
    radius_ir = math.sqrt(gsize)
    range_ir = math.sqrt(maxgsz) - radius_ir
    radius_v = math.sqrt(dirt * gsize)
    range_v = math.sqrt(dirt * maxgsz) - radius_v

    # calc grain growth decay factor
    growth_factor = growth(telapsed + 1.0)

    # calc effective gsizes for vis & ir
    gv = radius_v + (range_v * growth_factor)
    gir = radius_ir + (range_ir * growth_factor)

    # calc albedos for cos(z)=1
    alb_v_1 = MAXV - (gv / VFAC)
    alb_ir_1 = MAXIR * np.exp(IRFAC * gir)

    # calculate effect of cos(z)<1

    # adjust diurnal increase range
    dzv = gv * VZRG
    dzir = (gir * IRZRG) + IRZ0

    # calculate albedo
    alb_v = alb_v_1
    alb_ir = alb_ir_1

    # correct if the sun is up
    ind = cosz > 0.0
    alb_v[ind] += dzv[ind] * (1.0 - cosz[ind])
    alb_ir[ind] += dzir[ind] * (1.0 - cosz[ind])

    return alb_v, alb_ir


def decay_alb_power(veg, veg_type, start_decay, end_decay,
                    t_curr, pwr, alb_v, alb_ir):
    """
    Find a decrease in albedo due to litter acccumulation. Decay is based on
    max decay, decay power, and start and end dates. No litter decay occurs
    before start_date. Fore times between start and end of decay,

    .. math::
      \\alpha = \\alpha - (dec_{max}^{\\frac{1.0}{pwr}} \\times
      \\frac{t-start}{end-start})^{pwr}

    Where :math:`\\alpha` is albedo, :math:`dec_{max}` is the maximum decay
    for albedo, :math:`pwr` is the decay power, :math:`t`, :math:`start`,
    and :math:`end` are the current, start, and end times for the litter decay.

    Args:
        start_decay: date to start albedo decay (datetime)
        end_decay: date at which to end albedo decay curve (datetime)
        t_curr: datetime object of current timestep
        pwr: power for power law decay
        alb_v: numpy array of albedo for visibile spectrum
        alb_ir: numpy array of albedo for IR spectrum

    Returns:
        tuple:
        Returns a tuple containing the corrected albedo arrays
        based on date, veg type
        - **alb_v** (*numpy.array*) - albedo for visible specturm

        - **alb_ir** (*numpy.array*) -  albedo for ir spectrum


    Created July 18, 2017
    Micah Sandusky

    """
    # Calculate hour past start of decay
    t_diff_hr = t_curr - start_decay
    t_diff_hr = t_diff_hr.days*24.0 + \
        t_diff_hr.seconds/3600.0  # only need hours here

    # Calculate total time of decay
    t_decay_hr = (end_decay - start_decay)
    t_decay_hr = t_decay_hr.days*24.0 + \
        t_decay_hr.seconds/3600.0  # only need hours here

    # correct for veg
    alb_dec = np.zeros_like(alb_v)

    # Don't decay if before start
    if t_diff_hr <= 0.0:
        alb_dec = alb_dec * 0.0

    # Use max decay if after start
    elif t_diff_hr > t_decay_hr:
        # Use default
        alb_dec = alb_dec + veg['default']
        # Decay based on veg type
        for k, v in veg.items():
            if isint(k):
                alb_dec[veg_type == int(k)] = v

    # Power function decay if during decay period
    else:
        # Use defaults
        max_dec = veg['default']
        tao = (t_decay_hr) / (max_dec**(1.0/pwr))

        # Add default decay to array of zeros
        alb_dec = alb_dec + ((t_diff_hr) / tao)**pwr

        # Decay based on veg type
        for k, v in veg.items():
            max_dec = v
            tao = (t_decay_hr) / (max_dec**(1.0/pwr))

            # Set albedo decay at correct veg types
            if isint(k):
                alb_dec[veg_type == int(k)] = ((t_diff_hr) / tao)**pwr

    alb_v_d = alb_v - alb_dec
    alb_ir_d = alb_ir - alb_dec

    return alb_v_d, alb_ir_d


def decay_alb_hardy(litter, veg_type, storm_day, alb_v, alb_ir):
    """
    Find a decrease in albedo due to litter acccumulation
    using method from :cite:`Hardy:2000` with storm_day as input.

    .. math::
        lc = 1.0 - (1.0 - lr)^{day}

    Where :math:`lc` is the fractional litter coverage and :math:`lr` is
    the daily litter rate of the forest. The new albedo is a weighted
    average of the calculated albedo for the clean snow and the albedo
    of the litter.

    Note: uses input of l_rate (litter rate) from config
    which is based on veg type. This is decimal percent litter
    coverage per day

    Args:
        litter: A dictionary of values for default,albedo,41,42,43 veg types
        veg_type: An image of the basin's NLCD veg type
        storm_day: numpy array of decimal day since last storm
        alb_v: numpy array of albedo for visibile spectrum
        alb_ir: numpy array of albedo for IR spectrum
        alb_litter: albedo of pure litter

    Returns:
        tuple:
        Returns a tuple containing the corrected albedo arrays
        based on date, veg type
        - **alb_v** (*numpy.array*) - albedo for visible specturm

        - **alb_ir** (*numpy.array*) -  albedo for ir spectrum

    Created July 19, 2017
    Micah Sandusky

    """
    # array for decimal percent snow coverage
    sc = np.zeros_like(alb_v)
    # calculate snow coverage default veg type
    l_rate = litter['default']
    alb_litter = litter['albedo']

    sc = sc + (1.0-l_rate)**(storm_day)

    # calculate snow coverage based on veg type
    for k, v in litter.items():

        l_rate = litter[k]
        if isint(k):
            sc[veg_type == int(k)] = (
                1.0 - l_rate)**(storm_day[veg_type == int(k)])

    # calculate litter coverage
    lc = np.ones_like(alb_v) - sc

    # weighted average to find decayed albedo
    alb_v_d = alb_v*sc + alb_litter*lc
    alb_ir_d = alb_ir*sc + alb_litter*lc

    return alb_v_d, alb_ir_d
