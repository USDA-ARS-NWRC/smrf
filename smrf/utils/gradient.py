import numpy as np


def gradient_d4(dem, dx, dy):
    """
    Calculate the slope and aspect for provided dem,
    this will mimic the original IPW gradient method that
    does a finite difference in the x/y direction

    Args:
        dem: array of elevation values
        dx: cell size along the x axis
        dy: cell size along the y axis
    """

    # Pad the dem
    dem_pad = np.pad(dem, pad_width=1, mode='edge')

    # top
    dem_pad[0, :] = dem_pad[1, :] + (dem_pad[1, :] - dem_pad[2, :])

    # bottom
    dem_pad[-1, :] = dem_pad[-2, :] + (dem_pad[-3, :] - dem_pad[-2, :])

    # left
    dem_pad[:, 0] = dem_pad[:, 1] + (dem_pad[:, 1] - dem_pad[:, 2])

    # right
    dem_pad[:, -1] = dem_pad[:, -2] - (dem_pad[:, -3] - dem_pad[:, -2])

    # finite difference in the x direction
    dz_dy = (dem_pad[2:, 1:-1] - dem_pad[:-2, 1:-1]) / (2 * dy)
    dz_dx = (dem_pad[1:-1, 2:] - dem_pad[1:-1, :-2]) / (2 * dx)

    slope_radians = np.arctan(np.sqrt(dz_dx**2 + dz_dy**2))

    return slope_radians
