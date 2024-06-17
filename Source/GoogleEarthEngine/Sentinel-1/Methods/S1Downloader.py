import ee
import geopandas as gpd
import geemap
import multiprocessing as mutlilibrary

from functools import partial


_ = geemap.Map()


# sentinel-1 collection
Sen1Collection = ee.ImageCollection("COPERNICUS/S1_GRD")

filters = [
    ee.Filter.listContains("transmitterReceiverPolarisation", "VV"), \
    ee.Filter.listContains("transmitterReceiverPolarisation", "VH"), \
    ee.Filter.equals("instrumentMode", "IW") \
    ]

Sen1Collection = Sen1Collection.filter(filters)

# Get image for date and boundary
def GetImage(date, geometry, projectCRS):
    startDate = ee.Date(date)
    filteredCollection = Sen1Collection.filterBounds(geometry).filterDate(startDate, startDate.advance(1, 'Day'))

    collectionSize = filteredCollection.size().getInfo()
    if not (collectionSize > 0):
        return None

    image = filteredCollection.mosaic()

    crs = filteredCollection.first().select('VV').projection().crs().getInfo()

    image = image.setDefaultProjection(crs).reproject(projectCRS)

    return image


def GetImageGeometry(date, geom, crs):
    startDate = ee.Date(date)
    filteredCollection = Sen1Collection.filterBounds(geom).filterDate(startDate, startDate.advance(1, 'Day'))

    collectionSize = filteredCollection.size().getInfo()
    if not (collectionSize > 0):
        return None

    imageBoundaries = ee.FeatureCollection(ee.Feature(filteredCollection.geometry().dissolve()))
    imageGeometry = geemap.ee_to_gdf(imageBoundaries).to_crs(crs).iloc[0].geometry

    return imageGeometry


# download a single chip element
def DownloadChip(element_index, imageLibrary, crs, chipSize):
    RoI = imageLibrary.iloc[element_index].geeFeature.geometry()

    chipPath = imageLibrary.iloc[element_index].Path
    targetFolder = chipPath.parent

    if (not targetFolder.exists()):
        targetFolder.mkdir(parents=True)

    chipPath = chipPath.as_posix()

    image = imageLibrary.iloc[element_index].Image

    geemap.download_ee_image(image, chipPath, crs=crs, region=RoI, shape=(chipSize, chipSize))

    # with contextlib.redirect_stdout(None):
    # geemap.ee_export_image(image, chipPath, region=RoI, file_per_band=False, dimensions=(chipSize, chipSize))


def GetGEEImage(element_index, grid, date, crs):
    RoI = grid.iloc[element_index].geeFeature.geometry()
    return GetImage(date, RoI, crs)


def GetImageLibrary(grid, imageGeometry, date, crs, chipPathFunction, nbCores):
    grid = grid.copy()
    intersects = grid.intersects(imageGeometry).values
    grid = grid.iloc[intersects, :]

    chipsPath = [chipPathFunction(itemID, date) for itemID in grid.ItemID.values]
    grid['Path'] = chipsPath

    doesntExists = [not chipPath.exists() for chipPath in chipsPath]
    grid = grid.iloc[doesntExists, :]

    print('Building image library')
    gridLen = len(grid)

    if not (nbCores > 1):
        images = []
        for element_index in range(gridLen):
            print(f"{element_index + 1} / {gridLen}", end='\r')
            image = GetGEEImage(element_index, grid, date, crs)
            images.append(image)
    else:
        with mutlilibrary.Pool(nbCores) as pool:
            images = pool.map(partial(GetGEEImage, grid=grid, date=date, crs=crs), range(gridLen))

    print()
    grid['Image'] = images
    grid = grid.dropna()
    print(f'Done bulding GEE requirements, {len(grid)} left to download')
    return grid


# download all the chips for a given date
def DownloadAllChipsForDate(coveringGrid, date, crs, chipSize, chipPathFunction, nbCores):
    # check if there is images to download for this date, if not, abort
    df = gpd.GeoDataFrame(columns=['geometry'])
    df.loc[0] = coveringGrid.unary_union.convex_hull
    df = df.set_geometry('geometry').set_crs(coveringGrid.crs)
    geom = geemap.gdf_to_ee(df).first().geometry()

    imageGeometry = GetImageGeometry(date, geom, coveringGrid.crs)
    if imageGeometry == None:
        print('no image found')
        return

    imageLibrary = GetImageLibrary(coveringGrid, imageGeometry, date, crs, chipPathFunction, nbCores)

    if len(imageLibrary) == 0:
        return

    if not (nbCores > 1):
        num_tasks = len(coveringGrid)
        for k in range(num_tasks):
            print(f"{k} / {num_tasks}", end='\r')
            DownloadChip(k, imageLibrary=imageLibrary, crs=crs, chipSize=chipSize)
        return

    with mutlilibrary.Pool(nbCores) as pool:
        num_tasks = len(imageLibrary)
        # tqdm.tqdm(pool.imap_unordered(partial(DownloadChip, imageLibrary=imageLibrary, crs=crs, chipSize=chipSize), range(num_tasks)), total=num_tasks)
        pool.map(partial(DownloadChip, imageLibrary=imageLibrary, crs=crs, chipSize=chipSize),range(num_tasks))