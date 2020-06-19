import numpy as np

from smrf.envphys.constants import EMISS_VEG, FREEZE, STEF_BOLTZ


def thermal_correct_canopy(th, ta, tau, veg_height, height_thresh=2):
    """
    Correct thermal radiation for vegitation.  It will only correct
    for pixels where the veg height is above a threshold. This ensures
    that the open areas don't get this applied.  Vegitation temp
    is assumed to be at air temperature

    Args:
        th: thermal radiation
        ta: air temperature [C]
        tau: transmissivity of the canopy
        veg_height: vegitation height for each pixel
        height_thresh: threshold hold for height to say that there is veg in
            the pixel

    Returns:
        corrected thermal radiation

    Equations from Link and Marks 1999 :cite:`Link&Marks:1999`

    20150611 Scott Havens
    """

    # thermal emitted from the canopy
    veg = STEF_BOLTZ * EMISS_VEG * np.power(ta + FREEZE, 4)

    # pixels with canopy above the threshold
    ind = veg_height > height_thresh

    # correct incoming thermal
    th[ind] = tau[ind] * th[ind] + (1 - tau[ind]) * veg[ind]

    return th
