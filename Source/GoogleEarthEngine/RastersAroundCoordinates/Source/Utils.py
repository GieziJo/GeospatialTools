import numpy as np


def GetNameFromCoordinates(coords):
    coord_x = coords[0]
    coord_y = coords[1]
    coord_x_num = int(np.trunc(coord_x))
    coord_y_num = int(np.trunc(coord_y))

    coord_x -= coord_x_num
    coord_y -= coord_y_num

    coord_x = np.abs(coord_x)
    coord_y = np.abs(coord_y)

    coord_x *= 100000
    coord_y *= 100000

    coord_x = int(np.trunc(coord_x))
    coord_y = int(np.trunc(coord_y))

    coord_x_str = f'{coord_x_num}_{coord_x}'
    coord_y_str = f'{coord_y_num}_{coord_y}'

    return f'{coord_x_str}_{coord_y_str}'