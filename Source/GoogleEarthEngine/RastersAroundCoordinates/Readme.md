# Data download

This repo contains code to download raster images around a set of coordinates using GEE.

The main launcher is `Source/GetChips.ipynb`

Each chip is named by converting the coordinates into a string following the function in `Source/Utils.py` `GetNameFromCoordinates(coords)`.
Modify this function to change the way the coordinates are handled in the name.