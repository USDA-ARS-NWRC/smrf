import numpy as np


def gradient_d4(dem, dx, dy):
    """
    Calculate the slope and aspect for provided dem,
    this will mimic the original IPW gradient method that
    does a finite difference in the x/y direction

    Given a center cell e and it's neighbors:

    | a | b | c |
    | d | e | f |
    | g | h | i |

    The rate of change in the x direction is
    [dz/dx] = (f - d ) / (2 * dx)

    The rate of change in the y direction is
    [dz/dy] = (h - b ) / (2 * dy)

    The slope is calculated as
    slope_radians = arctan ( sqrt ([dz/dx]^2 + [dz/dy]^2) )

    Args:
        dem: array of elevation values
        dx: cell size along the x axis
        dy: cell size along the y axis

    Returns:
        slope in radians
    """

    # Pad the dem
    dem_pad = np.pad(dem, pad_width=1, mode='edge')

    # top
    dem_pad[0, :] = dem_pad[1, :] + (dem_pad[1, :] - dem_pad[2, :])

    # bottom
    dem_pad[-1, :] = dem_pad[-2, :] + (dem_pad[-2, :] - dem_pad[-1, :])

    # left
    dem_pad[:, 0] = dem_pad[:, 1] + (dem_pad[:, 1] - dem_pad[:, 2])

    # right
    dem_pad[:, -1] = dem_pad[:, -2] - (dem_pad[:, -3] - dem_pad[:, -2])

    # finite difference in the y direction
    dz_dy = (dem_pad[2:, 1:-1] - dem_pad[:-2, 1:-1]) / (2 * dy)

    # finite difference in the x direction
    dz_dx = (dem_pad[1:-1, 2:] - dem_pad[1:-1, :-2]) / (2 * dx)

    slope = np.arctan(np.sqrt(dz_dx**2 + dz_dy**2))
    a = aspect(dz_dx, dz_dy)

    return slope, a


def gradient_d8(dem, dx, dy):
    """
    Calculate the slope and aspect for provided dem,
    using a 3x3 cell around the center

    Given a center cell e and it's neighbors:

    | a | b | c |
    | d | e | f |
    | g | h | i |

    The rate of change in the x direction is
    [dz/dx] = ((c + 2f + i) - (a + 2d + g) / (8 * dx)

    The rate of change in the y direction is
    [dz/dy] = ((g + 2h + i) - (a + 2b + c)) / (8 * dy)

    The slope is calculated as
    slope_radians = arctan ( sqrt ([dz/dx]^2 + [dz/dy]^2) )


    Args:
        dem: array of elevation values
        dx: cell size along the x axis
        dy: cell size along the y axis

    Returns:
        slope in radians
    """

    # Pad the dem
    dem_pad = np.pad(dem, pad_width=1, mode='edge')

    # top
    dem_pad[0, :] = dem_pad[1, :] + (dem_pad[1, :] - dem_pad[2, :])

    # bottom
    dem_pad[-1, :] = dem_pad[-2, :] + (dem_pad[-2, :] - dem_pad[-1, :])

    # left
    dem_pad[:, 0] = dem_pad[:, 1] + (dem_pad[:, 1] - dem_pad[:, 2])

    # right
    dem_pad[:, -1] = dem_pad[:, -2] - (dem_pad[:, -3] - dem_pad[:, -2])

    # finite difference in the y direction
    dz_dy = ((dem_pad[2:, :-2] + 2*dem_pad[2:, 1:-1] + dem_pad[2:, 2:]) -
             (dem_pad[:-2, :-2] + 2*dem_pad[:-2, 1:-1] + dem_pad[:-2, 2:])) / (8 * dy)

    # finite difference in the x direction
    dz_dx = ((dem_pad[:-2, 2:] + 2*dem_pad[1:-1, 2:] + dem_pad[2:, 2:]) -
             (dem_pad[:-2, :-2] + 2*dem_pad[1:-1, :-2] +
              dem_pad[2:, :-2])) / (8 * dx)

    slope = np.arctan(np.sqrt(dz_dx**2 + dz_dy**2))
    a = aspect(dz_dx, dz_dy)

    return slope, a


def aspect(dz_dx, dz_dy):
    """
    Calculate the aspect from the finite difference.
    Aspect is radians from south (aspect 0 is toward
    the south) with range from -pi to pi, with negative 
    values to the west and positive values to the east

    Args:
        dz_dx: finite difference in the x direction
        dz_dy: finite difference in the y direction

    Returns
        aspect in radians
    """

    a = np.arctan2(-dz_dy, -dz_dx)

    return a
