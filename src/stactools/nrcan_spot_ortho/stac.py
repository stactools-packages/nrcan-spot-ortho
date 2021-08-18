from datetime import datetime
import os
import fiona
import json
from pyproj import crs, Transformer
from pystac import (
    Catalog,
    StacIO,
    Asset,
    Item,
    MediaType,
    SpatialExtent,
)
from pystac.extensions.projection import ProjectionExtension
from shapely.geometry import box
from shapely.ops import transform as shapely_transform
from stactools.nrcan_spot_ortho.geobase_ftp import GeobaseSpotFTP
from stactools.nrcan_spot_ortho.utils import (bbox, transform_geom,
                                              CustomStacIO)
from stactools.nrcan_spot_ortho.stac_templates import (spot_sensor, proj_epsg)

StacIO.set_default(CustomStacIO)
null = None


def create_year_catalog(sensor, year, ortho_collection):
    """
    sensor: "S4" or "S5"
    year: image acquisition year
    """
    spot_catalog = Catalog(
        id=f"{sensor}_{year}",
        description=f"{spot_sensor[sensor]} images for {year}",
        title=f"{sensor}_{year}",
        stac_extensions=None)
    ortho_collection.add_child(spot_catalog)
    return spot_catalog


def create_item(name, feature, collection):
    """Create a STAC item for SPOT

    Args:
        name (str): SPOT ID.
        feature (dict): geojson feature.
        collection (pystac.Collection): pySTAC collection object.

    Returns:
        item (pystac.Item): The created STAC item for the given feature.
    """
    item = Item(
        id=name,
        geometry=feature["geometry"],
        bbox=list(bbox(feature)),
        properties={},
        datetime=datetime.strptime(name[14:22], "%Y%m%d"),
        collection=collection,
        stac_extensions=[
            "https://stac-extensions.github.io/eo/v1.0.0/schema.json",
            "https://stac-extensions.github.io/projection/v1.0.0/schema.json"
        ])
    # eo_ext = EOExtension.ext(item)
    # eo_ext.apply(list(spot_bands.values()) + [spot_pan[sensor]])
    proj_ext = ProjectionExtension.ext(item)
    proj_ext.epsg = null  # Assume LCC projection (proj:epsg only accepts 1 number)
    return item


def build_items(index_geom, spot_catalog, test, root_href, catalog_type):
    """Build the STAC items for orthorectified SPOT 4 and 5 over Canada.

    Args:
        index_geom (str): File path of fiona-readable file (e.g. a shapefile)
        that contains the SPOT images geometries.
        spot_catalog (pystac.Catalog): The catalog within which to build items.
        test (bool): Whether this is part of a test. A test run uses a local item
        template and doesn't require a connection to the Geobase FTP server.
        root_href (str): The root href and output location of the catalog.
        catalog_type (pystac.CatalogType): The type of catalog.

    Returns:
        spot_catalog (pystac.Catalog): A catalog that includes all items listed
        within the index_geom.
    """
    with fiona.open(index_geom) as src:
        # Create a transformer for shapefile proj --> WGS84
        src_crs = crs.CRS(src.crs)  # ['init']
        dest_crs = crs.CRS("WGS84")
        transformer = Transformer.from_crs(src_crs, dest_crs)

        # Transform the shapefile extent to WGS84 for the collection bbox
        extent = box(*src.bounds)
        collection_bbox = shapely_transform(transformer.transform, extent)

        # Set spatial extent for collections
        for sensor in ["spot4", "spot5"]:
            ortho_collection = spot_catalog.get_child(
                "canada-spot-orthoimages").get_child(
                    f"canada-{sensor}-orthoimages")
            ortho_collection.extent.spatial = SpatialExtent(
                [list(collection_bbox.bounds)])

        # Open a Geobase FTP connection
        if test:
            hrefs_path = os.path.join(os.path.dirname(index_geom),
                                      'spot_hrefs_test.json')
            with open(hrefs_path, 'r') as f:
                hrefs = json.load(f)
        else:
            geobase = GeobaseSpotFTP()

        count = 0
        for f in src:

            # Get the WGS84 bbox for the item polygon
            feature_out = f.copy()
            new_coords = transform_geom(transformer,
                                        f["geometry"]["coordinates"])
            feature_out["geometry"]["coordinates"] = new_coords

            # Get the collection for the item's sensor
            name = feature_out["properties"]["NAME"]
            sensor = name[:2]
            sensor_full = spot_sensor[sensor].lower().replace(" ", "")
            year = name.split("_")[3][:4]
            ortho_collection = spot_catalog.get_child(
                "canada-spot-orthoimages").get_child(
                    f"canada-{sensor_full}-orthoimages")

            # Get/create the catalog for the item's year
            if not ortho_collection.get_child(f"{sensor}_{year}"):
                year_catalog = create_year_catalog(sensor, year,
                                                   ortho_collection)
            else:
                year_catalog = ortho_collection.get_child(f"{sensor}_{year}")

            # Create item and add to catalog
            new_item = create_item(name, feature_out, ortho_collection)
            year_catalog.add_item(new_item)

            fnames = geobase.list_contents(
                name) if not test else hrefs["hrefs"]
            for i, fname in enumerate(fnames):
                # Include asset information for Geobase zipped imagery
                # STAC parses hrefs starting with "ftp." as relative
                title = fname[-13:-4]
                # gsd = float(title.split("_")[0][1:])
                contents = {
                    "m": "Multi-band",
                    "p": "Panchromatic"
                }.get(title[0])
                spot_file = Asset(href=fname.replace("ftp.", "http://ftp."),
                                  title=title,
                                  media_type="application/zip",
                                  roles=['data'])

                # Include projection information
                proj_ext = ProjectionExtension.ext(spot_file)
                proj = [p for p in proj_epsg.keys() if p in fname.lower()][0]
                proj_ext.epsg = proj_epsg[proj]
                spot_file.description = f"{contents} imagery in EPSG:{proj_epsg[proj]}"

                new_item.add_asset(title, spot_file)

            # Add the thumbnail asset
            href_tn = geobase.get_thumbnail(name) if not test else hrefs["tn"]
            new_item.add_asset(
                key="thumbnail",
                asset=Asset(
                    href=href_tn.replace("ftp.", "http://ftp."),
                    title=None,
                    media_type=MediaType.JPEG,
                    roles=['thumbnail'],
                ),
            )

            count += 1
            print(f"{count}... {new_item.id}")

        spot_catalog.normalize_and_save(root_href, catalog_type)

    return spot_catalog
