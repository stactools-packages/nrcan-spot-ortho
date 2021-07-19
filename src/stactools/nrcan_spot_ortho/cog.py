import os
from tempfile import TemporaryDirectory
import pystac
from pystac.extensions.eo import EOExtension
from pystac.extensions.projection import ProjectionExtension
from stactools.nrcan_spot_ortho.stac_templates import image_types
from stactools.nrcan_spot_ortho.geobase_ftp import GeobaseSpotFTP
from stactools.nrcan_spot_ortho.stac_templates import (spot_bands, spot_pan,
                                                       proj_epsg)
from stactools.nrcan_spot_ortho.utils import (CustomStacIO, download_from_ftp,
                                              call, unzip, upload_to_s3,
                                              file_exists)
from urllib.parse import urlparse
import rasterio

pystac.StacIO.set_default(CustomStacIO)


def cogify(input_path, output_path, overwrite):
    """COGify a geotiff at input_path to a cloud optimized geotiff at output_path.
    """
    print(f"COGifying {os.path.basename(input_path)}")
    failure = False
    parsed = urlparse(output_path)

    if (not overwrite) and file_exists(output_path):
        print(f"Skipping {os.path.basename(output_path)}, already COGified.")

    elif parsed.scheme == "s3":
        with TemporaryDirectory() as tmp_dir:
            tmp_path = os.path.join(tmp_dir, os.path.basename(output_path))
            failure = call([
                'gdal_translate', '-of', 'COG', '-co', 'compress=deflate',
                input_path, tmp_path
            ])
            upload_to_s3(parsed, tmp_path)

    else:
        failure = call([
            'gdal_translate', '-of', 'COG', '-co', 'compress=deflate',
            input_path, output_path
        ])

    if failure:
        print(f"Could not COGify to {output_path}")
        raise


def include_cog_asset(item, cog_path, cog_proj):
    """Mutate a STAC item to include a COG at cog_path with the projection cog_proj as an asset.
    """
    # Include the COG as an asset
    cog_filename = os.path.basename(cog_path)
    title = [v for k, v in image_types.items() if k in cog_filename][0]
    asset = pystac.Asset(href=cog_path,
                         media_type=pystac.MediaType.COG,
                         roles=['data'],
                         title=title)

    # Provide band and projection information for the asset
    eo_ext = EOExtension.ext(asset)
    if title == "pan":
        eo_ext.apply([spot_pan[cog_filename[:2].upper()]])
    else:
        eo_ext.apply([spot_bands[title]])
    proj_ext = ProjectionExtension.ext(asset)
    proj_ext.epsg = proj_epsg[cog_proj]
    with rasterio.open(cog_path) as src:
        proj_ext.transform = src.transform
        proj_ext.bbox = src.bounds
        # proj_ext.projjson = src.crs.to_dict(proj_json=True)
        proj_ext.wkt2 = src.crs.wkt
        asset.properties['gsd'] = src.res[0]

    item.assets[title] = asset


def cogify_item(item, geobase, cog_directory, overwrite, cog_proj="lcc00"):
    """Create COGs from the GeoTIFF asset contained in the passed in STAC item.
    Mutates the item to include assets for the new COGs.

    Args:
        item (pystac.Item): Item that contains assets that will be converted to
            COGs.
        geobase (stactools.spot.GeobaseSpotFTP): FTP connection object, used for
            downloading the zipped imagery files.
        cog_directory (str): A URI of a directory to store COGs. This will be used
            in conjunction with the file names based on the COG asset to store
            the COG data. If None is passed then store COGs in the location given
            by the self_href of the item.
        overwrite (bool): Whether to overwrite existing COG files.
        cog_proj (str): Imagery is stored in LCC projection as well as local UTM
        projections. Choose which of these projections to convert to COG (LCC
        recommended, as it covers all of Canada).
    """
    if cog_directory is None:
        cog_directory = os.path.dirname(item.get_self_href())

    with TemporaryDirectory() as tmp_dir:
        # Get asset names associated with the chosen projection
        asset_names = [k for k in item.assets.keys() if cog_proj in k.lower()]

        for asset_name in asset_names:
            zip_href = item.assets[asset_name].href

            if not overwrite:
                # predict cog file names
                fname_base = os.path.basename(zip_href).replace(
                    f"_{cog_proj}.zip", "")
                bands = range(1, 5) if fname_base[-3:] == "m20" else [1]
                cog_paths = [
                    os.path.join(cog_directory,
                                 f"{fname_base}_{i}_{cog_proj}_cog.tif")
                    for i in bands
                ]

                # check if predicted file names exist and include as asset if so
                exists = False
                for cog_path in cog_paths:
                    if file_exists(cog_path):
                        include_cog_asset(item, cog_path, cog_proj)
                        exists = True

                # skip download/unzip/cogify if any exist (assume all done)
                if exists:
                    print(f"Skipping {asset_name}, already COGified.")
                    continue

            # Download zip file
            zip_path = os.path.join(tmp_dir, os.path.basename(zip_href))
            download_from_ftp(zip_href, zip_path, geobase)

            # Unzip images
            non_cog_paths = [
                f for f in unzip(zip_path, tmp_dir) if '.tif' in f.lower()
            ]

            # For each image, COGify and include as an asset
            for non_cog_path in non_cog_paths:
                # COGify
                cog_filename = (os.path.basename(non_cog_path).replace(
                    '.tif', '_cog.tif'))
                cog_path = os.path.join(cog_directory, cog_filename)
                cogify(non_cog_path, cog_path, overwrite)
                include_cog_asset(item, cog_path, cog_proj)

        # Download the thumbnail to the same location as the COGs, checking
        # if already downloaded first
        tn_href = item.assets["thumbnail"].href
        if cog_directory not in tn_href:
            tn_fname = os.path.basename(tn_href)
            tn_path = os.path.join(cog_directory, tn_fname)
            parsed = urlparse(tn_path)

            if not file_exists(tn_path):
                if (parsed.scheme == "s3"):
                    tmp_tn_path = os.path.join(tmp_dir, tn_fname)
                    download_from_ftp(tn_href, tmp_tn_path, geobase)
                    upload_to_s3(parsed, tmp_tn_path)

                elif not os.path.exists(tn_path):
                    download_from_ftp(tn_href, tn_path, geobase)

            item.assets["thumbnail"].href = tn_path


def cogify_catalog(catalog_path, cog_directory=None, overwrite=False):
    """Crawl a catalog, find zipped imagery hrefs within items, download/unzip/COGify
    these, include the results as new assets.

    Args:
        catalog_path (str): The file path of the root STAC catalog.
        cog_directory (str): A URI of a directory to store COGs. This will be used
            in conjunction with the file names based on the COG asset to store
            the COG data. If None is passed then store COGs in the location given
            by the self_href of the item.
        overwrite (bool): Whether to overwrite existing COG files.
    """
    # Open catalog
    spot_catalog = pystac.read_file(catalog_path)

    count = 0
    for _, _, items in spot_catalog.walk():
        
        for item in items:
            print(f"\n{item.id}...")

            # Reconnect to the Geobase FTP occasionally to avoid timeouts
            if count % 5 == 0:
                geobase = GeobaseSpotFTP()
            count += 1

            # Skip if COGified already and overwrite==False
            cogified = ("B1" in item.assets.keys()) and file_exists(
                item.assets["B1"].href)
            if (not cogified) or (cogified and overwrite):

                # COGify item's assets and save item
                cogify_item(item, geobase, cog_directory, overwrite)
                # spot_catalog.normalize_and_save(os.path.dirname(catalog_path),
                #                                 spot_catalog.catalog_type)
                item.save_object()

            else:
                print(f"Skipping {item.id}, already COGified.")
