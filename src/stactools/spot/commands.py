import logging

import click
import pystac

from stactools.spot.stac import build_items
from stactools.spot.stac_templates import build_root_catalog
from stactools.spot.cog import cogify_catalog

logger = logging.getLogger(__name__)


def create_spot_command(cli):
    """Creates a command group for commands dealing with spot data
    """
    @cli.group('spot', short_help="Commands for working with spot data.")
    def spot():
        pass

    @spot.command(
        'convert-index',
        short_help='Convert the SPOT index shapefile to a STAC catalog.')
    @click.argument('index')
    @click.argument('root_href')
    @click.option('-t',
                  '--test',
                  is_flag=True,
                  default=False,
                  help='Run as a test. Doesn\'t require Geobase FTP access.')
    @click.option('-c',
                  '--catalog-type',
                  type=click.Choice([
                      pystac.CatalogType.ABSOLUTE_PUBLISHED,
                      pystac.CatalogType.RELATIVE_PUBLISHED,
                      pystac.CatalogType.SELF_CONTAINED
                  ],
                                    case_sensitive=False),
                  default=pystac.CatalogType.ABSOLUTE_PUBLISHED)
    def convert_command(index, root_href, test, catalog_type):
        """Converts the SPOT Index shapefile to a STAC Catalog.
        """
        # Create a catalog root and collections for each sensor
        spot_catalog = build_root_catalog()
        spot_catalog.normalize_hrefs(root_href)

        # Populate the catalog with items
        build_items(index, spot_catalog, test, root_href, catalog_type)
        spot_catalog.normalize_and_save(root_href, catalog_type)

        print("Finished!")

    @spot.command(
        'cogify-assets',
        short_help='Convert geotiff assets into cloud optimized geotiffs.')
    @click.argument('catalog_path')
    @click.option(
        '-d',
        '--cog-dir',
        default=None,
        help="""The directory to store all COGs. Leave empty to store COGs within
         each relevant STAC item's folder.""")
    @click.option('-o',
                  '--overwrite',
                  type=click.Choice([True, False]),
                  default=False,
                  help="Overwrite existing COGs.")
    def cogify_command(catalog_path, cog_directory, overwrite):
        """Convert geotiff assets into cloud optimized geotiffs.
        """
        cogify_catalog(catalog_path, cog_directory, overwrite)

        print("Finished!")

    return spot
