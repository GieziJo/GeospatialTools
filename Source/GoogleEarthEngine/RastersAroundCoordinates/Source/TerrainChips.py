import ee
import geemap
import rioxarray as rioxr
import numpy as np

from Utils import GetNameFromCoordinates

_ = geemap.Map()


def DownloadTerrainData(coords, chipSize, targetFolder, terrain, layer, crs, scale):
    targetFile = targetFolder / f'{GetNameFromCoordinates(coords)}_{chipSize}.tif'
    if targetFile.exists():
        return targetFile

    coords = (np.round(coords[0].astype(np.float64), decimals=5), np.round(coords[1].astype(np.float64), decimals=5))
    point = ee.Geometry.Point(coords).transform(crs)

    circle = point.buffer((chipSize / 2) * scale)

    bound = circle.bounds()

    terrain = terrain.filterBounds(bound).mosaic().setDefaultProjection(crs=crs, scale=scale).select(layer)

    geemap.download_ee_image(terrain, targetFile, bound, crs, shape=(chipSize, chipSize))
    return targetFile


def NormaliseRelativeTerrainData(elevationFilePath, minElevation, maxElevation, station_coords, scale, crs, terrain, layer):
    targetFilePath = elevationFilePath.parent / f'{elevationFilePath.stem}_normalised_relative.tif'
    if targetFilePath.exists():
        return targetFilePath
    station_point = ee.Geometry.Point(station_coords)
    station_elevation = geemap.ee_to_df(terrain.filterBounds(station_point).mosaic().select(layer).sampleRegions(
        collection=ee.FeatureCollection(ee.Feature(station_point)), scale=scale, projection=crs))[layer].values[0]

    with rioxr.open_rasterio(elevationFilePath) as src:
        src.values = np.interp(src.values, [minElevation, maxElevation], (-1.0, 1.0))
        src -= np.interp(station_elevation, [minElevation, maxElevation], (-1.0, 1.0))
        src.rio.to_raster(targetFilePath, driver='GTiff')
    return targetFilePath

def NormaliseTerrainData(elevationFilePath, minElevation, maxElevation):
    targetFilePath = elevationFilePath.parent / f'{elevationFilePath.stem}_normalised.tif'
    if targetFilePath.exists():
        return targetFilePath

    with rioxr.open_rasterio(elevationFilePath) as src:
        src.values = np.interp(src.values, [minElevation, maxElevation], (-1.0, 1.0))
        src.rio.to_raster(targetFilePath, driver='GTiff')
    return targetFilePath


def GetTifSubsets(subsets, file, chipSize):
    for subset in subsets:
        targetFilePath = file.parent / file.name.replace(str(chipSize), str(subset))
        if targetFilePath.exists():
            return
        start = (chipSize - subset) // 2
        end = start + subset

        with rioxr.open_rasterio(file) as src:
            src = src[:, start:end, start:end]
            src.rio.to_raster(targetFilePath, driver='GTiff')

def DownloadAndProcessChips(coords, chipSize, targetFolder, terrain, layer, crs, scale):

        DownloadTerrainData(coords, chipSize, targetFolder, terrain, layer, crs, scale)