import ee
import geemap
import numpy as np

from Utils import GetNameFromCoordinates

_ = geemap.Map()


# I create composites for S2 (one per season), but if you need individual
# dates, I can rewrite the code for that
# Note: this only downloads the 10 meters bands


# Spring: Begins around March 20th or 21st (vernal equinox).
# Summer: Begins around June 21st or 22nd (summer solstice).
# Autumn: Begins around September 22nd or 23rd (autumnal equinox).
# Winter: Begins around December 21st or 22nd (winter solstice

def GetDates(year, q):
    if q == 0:
        return f'{year - 1}-12-21', f'{year}-03-21'
    if q == 1:
        return f'{year}-03-21', f'{year}-06-22'
    if q == 2:
        return f'{year}-06-22', f'{year}-09-23'
    if q == 3:
        return f'{year}-09-23', f'{year}-12-21'


def GetChip(year, q, coords, chipSize, targetFolder, crs, scale):
    targetFile = targetFolder / f'{GetNameFromCoordinates(coords)}_{chipSize}_{year}_{q}.tif'
    if targetFile.exists():
        return

    date_start, date_end = GetDates(year, q)
    date_start = ee.Date(date_start)
    date_end = ee.Date(date_end)

    coords = (np.round(coords[0].astype(np.float64), decimals=5), np.round(coords[1].astype(np.float64), decimals=5))
    point = ee.Geometry.Point(coords).transform(crs)

    circle = point.buffer((chipSize / 2) * scale)

    bound = circle.bounds()

    s2 = ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED')

    csPlus = ee.ImageCollection('GOOGLE/CLOUD_SCORE_PLUS/V1/S2_HARMONIZED')

    QA_BAND = 'cs'

    CLEAR_THRESHOLD = 0.65

    s2_filtered = s2.filterDate(date_start, date_end).filterBounds(bound)

    composite = s2_filtered.linkCollection(csPlus, [QA_BAND]) \
        .map(lambda img: img.updateMask(img.select(QA_BAND).gte(CLEAR_THRESHOLD))).median()

    composite = composite.setDefaultProjection(crs=crs, scale=scale).select(['B2', 'B3', 'B4', 'B8'])

    geemap.download_ee_image(composite, targetFile, bound, crs, shape=(chipSize, chipSize))


def DownloadS2Chip(coords, chipSize, targetFolder, crs, scale, year_start, year_end):
    for year in range(year_start, year_end + 1):
        for q in range(4):
            GetChip(year, q, coords, chipSize, targetFolder, crs, scale)
