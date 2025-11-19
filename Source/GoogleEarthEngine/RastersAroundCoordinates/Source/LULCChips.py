import ee
import geemap
import numpy as np
import rasterio as rio

from Utils import GetNameFromCoordinates

_ = geemap.Map()

'''

1. 
10	#006400	Tree cover
95	#00cf75	Mangroves

2.
30	#ffff4c	Grassland
90	#0096a0	Herbaceous wetland
100	#fae6a0	Moss and lichen

3.
20	#ffbb22	Shrubland

4.
40	#f096ff	Cropland

5. 
60	#b4b4b4	Bare / sparse vegetation
70	#f0f0f0	Snow and ice

6. 
50	#fa0000	Built-up

7. 
80	#0064c8	Permanent water bodies
'''




def DownloadLCLUData(coords, chipSize, targetFolder, lclu, crs, scale):
    targetFile = targetFolder / f'{GetNameFromCoordinates(coords)}_{chipSize}.tif'
    if targetFile.exists():
        return targetFile

    coords = (coords[0].astype(np.float64), coords[1].astype(np.float64))
    point = ee.Geometry.Point(coords).transform(crs)

    circle = point.buffer((chipSize / 2) * scale)

    bound = circle.bounds()

    lclu = lclu.filterBounds(bound).mosaic().setDefaultProjection(crs=crs, scale=scale)

    geemap.download_ee_image(lclu, targetFile, bound, crs, shape=(chipSize, chipSize))
    return targetFile

def ProcessFile(filePath):
    targetFilePath = filePath.parent / f'{filePath.stem}_processed.tif'
    if targetFilePath.exists():
        return targetFilePath

    with rio.open(filePath) as r:
        data = r.read(1)
        data[data == 10] = 1  # 006400	Tree cover
        data[data == 95] = 1  # 00cf75	Mangroves

        data[data == 30] = 2  # ffff4c	Grassland
        data[data == 90] = 2  # 0096a0	Herbaceous wetland
        data[data == 100] = 2  # fae6a0	Moss and lichen

        data[data == 20] = 3  # ffbb22	Shrubland

        data[data == 40] = 4  # f096ff	Cropland

        data[data == 60] = 5  # b4b4b4	Bare / sparse vegetation
        data[data == 70] = 5  # f0f0f0	Snow and ice

        data[data == 50] = 6  # fa0000	Built-up

        data[data == 80] = 7  # 0064c8	Permanent water bodies

        nbCats = 7

        dataLayered = np.zeros([nbCats, data.shape[0], data.shape[1]])
        for k in range(nbCats):
            dataLayered[k,] = (data == (k + 1)) * 1

        profile = r.profile.copy()
        profile.update(count=nbCats, dtype=rio.ubyte)
        with rio.open(targetFilePath, 'w', **profile) as dst:

            dst.write(dataLayered)



def DownloadAndProcessChips(coords, chipSize, targetFolder, lclu, crs, scale):

        filePath = DownloadLCLUData(coords, chipSize, targetFolder, lclu, crs, scale)
        ProcessFile(filePath)

