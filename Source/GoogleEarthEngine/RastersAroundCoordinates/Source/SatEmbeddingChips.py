import ee
import geemap
import numpy as np

from Utils import GetNameFromCoordinates

_ = geemap.Map()

def DownloadGoogleSatEmbeddingChip(coords, chipSize, targetFolder, crs, scale):
    # for year in range(2019, 2025):
    for year in [2024]:
        targetFile = targetFolder / f'{GetNameFromCoordinates(coords)}_{chipSize}_{year}.tif'
        if targetFile.exists():
            continue

        coords = (np.round(coords[0].astype(np.float64), decimals=5), np.round(coords[1].astype(np.float64), decimals=5))
        point = ee.Geometry.Point(coords).transform(crs)

        circle = point.buffer((chipSize / 2) * scale)

        bound = circle.bounds()

        # dataset = ee.ImageCollection("projects/mldp-partners/assets/preview/efm_v2_preview")
        dataset = ee.ImageCollection("GOOGLE/SATELLITE_EMBEDDING/V1/ANNUAL")
        dataset = dataset.filterDate(ee.Date(f'{year}-01-01'), ee.Date(f'{year}-12-31')).filterBounds(bound).mosaic().setDefaultProjection(crs=crs, scale=scale)

        try:
            geemap.download_ee_image(dataset, targetFile, bound, crs, shape=(chipSize, chipSize))
        except:
            print(f'Failed to download {targetFile}')


def DownloadAndProcessChips(coords, chipSize, targetFolder, crs, scale):
        DownloadGoogleSatEmbeddingChip(coords, chipSize, targetFolder, crs, scale)