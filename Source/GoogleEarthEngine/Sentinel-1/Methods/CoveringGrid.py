import geopandas as gpd
import geemap

import shapely

import unicodedata
import re

_ = geemap.Map()

def slugify(value):
    value = unicodedata.normalize('NFKD', value).encode('ascii', 'ignore').decode('ascii')
    value = re.sub(r'[^\w\s-]', '', value)
    value = re.sub(r'[-\s]+', '-', value).strip('-_')
    return value


# create a covering grid over the geometry, save the grid for futur references
# set override to true when you call this to regenerate the grid
def GetCoveringGrid(outputDataFolder, pathToShapefile, crs, resolution, pixelsWidth, override=False):

    coveringGridPath = outputDataFolder/'Shapefiles'/f'CoveringGrid_{pathToShapefile.stem}_{slugify(crs)}_{resolution}_{pixelsWidth}.geojson'
    coveringGridPath.parent.mkdir(exist_ok=True, parents=True)

    if (not coveringGridPath.exists()) or override:
        shape = gpd.read_file(pathToShapefile)
        gdf = shape.to_crs('EPSG:3857')

        # Get the extent of the shapefile
        total_bounds = gdf.total_bounds

        # Get minX, minY, maxX, maxY
        minX, minY, maxX, maxY = total_bounds

        # Create a fishnet
        x, y = (minX, minY)
        geom_array = []

        # Polygon Size
        square_size = pixelsWidth * resolution
        while y <= maxY:
            while x <= maxX:
                geom = shapely.geometry.Polygon(
                    [(x, y), (x, y + square_size), (x + square_size, y + square_size), (x + square_size, y), (x, y)])
                geom_array.append(geom)
                x += square_size
            x = minX
            y += square_size

        fishnet = gpd.GeoDataFrame(geom_array, columns=['geometry']).set_crs('EPSG:3857')

        fishnet = fishnet[fishnet.intersects(gdf.geometry.unary_union)]

        fishnet = fishnet.to_crs(crs)

        fishnet['ItemID'] = range(len(fishnet))

        fishnet.to_file(coveringGridPath)

    fishnet = gpd.read_file(coveringGridPath)
    gridElements = []
    for k in range(len(fishnet)):
        geomsubset = fishnet.iloc[k:k + 2, :].head(1)
        gridElements.append(geemap.gdf_to_ee(geomsubset).first())
    fishnet['geeFeature'] = gridElements

    return fishnet

