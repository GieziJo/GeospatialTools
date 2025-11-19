import ee
import geemap
import numpy as np

from Utils import GetNameFromCoordinates

_ = geemap.Map()

def DownloadTerrainData(coords, chipSize, targetFolder, terrain, crs, scale, type='slope'):
    targetFile = targetFolder / f'{GetNameFromCoordinates(coords)}_{chipSize}.tif'
    if targetFile.exists():
        return

    coords = (np.round(coords[0].astype(np.float64), decimals=5), np.round(coords[1].astype(np.float64), decimals=5))
    point = ee.Geometry.Point(coords).transform(crs)

    circle = point.buffer((chipSize / 2) * scale)

    bound = circle.bounds()

    terrain = terrain.mosaic().setDefaultProjection(crs=crs, scale=scale)
    if type == 'slope':
            terrain = ee.Terrain.slope(terrain).multiply(ee.Number.expression('Math.PI')).divide(180.0).tan()
    elif type=='aspect':
        terrain = ee.Terrain.aspect(terrain).multiply(ee.Number.expression('Math.PI')).divide(180.0)
        terrain = terrain.cos().rename(['eastness']).addBands(terrain.sin().rename(['northness']))
    else:
        return

    geemap.download_ee_image(terrain, targetFile, bound, crs, shape=(chipSize, chipSize))
    return

def DownloadAndProcessChips(coords, chipSize, targetFolder, terrain, crs, scale, type):
    DownloadTerrainData(coords, chipSize, targetFolder, terrain, crs, scale, type)
