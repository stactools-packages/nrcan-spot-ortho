import logging

import click
import pystac

from stactools.nrcan_spot_ortho.stac import build_items
from stactools.nrcan_spot_ortho.stac_templates import build_root_catalog
from stactools.nrcan_spot_ortho.cog import cogify_catalog

logger = logging.getLogger(__name__)


def create_spot_command(cli):
    """Creates a command group for commands dealing with orthorectified SPOT
    4 and 5 data
    """
    @cli.group('nrcan-spot-ortho',
               short_help='Commands for ortho SPOT 4 and 5 data over Canada.')
    def spot():
        pass

    @spot.command(
        'convert-index',
        short_help='Convert ortho SPOT 4 and 5 index shapefile to STAC catalog.'
    )
    @click.argument('index')
    @click.argument('root_href')
    @click.option('-c',
                  '--catalog-type',
                  type=click.Choice([
                      pystac.CatalogType.ABSOLUTE_PUBLISHED,
                      pystac.CatalogType.RELATIVE_PUBLISHED,
                      pystac.CatalogType.SELF_CONTAINED
                  ],
                                    case_sensitive=False),
                  default=pystac.CatalogType.ABSOLUTE_PUBLISHED)
    def convert_command(index, root_href, catalog_type):
        """Converts the SPOT Index shapefile to a STAC Catalog.
        """
        # Create a catalog root and collections for each sensor
        spot_catalog = build_root_catalog()
        spot_catalog.normalize_hrefs(root_href)

        # Populate the catalog with items
        test = 'spot_index_test.shp' in index
        build_items(index, spot_catalog, test, root_href, catalog_type)
        spot_catalog.normalize_and_save(root_href, catalog_type)

        print("Finished!")

    @spot.command(
        'cogify-assets',
        short_help='Convert geotiff assets into cloud optimized geotiffs.')
    @click.argument('catalog_path')
    @click.option(
        '-d',
        '--cog-directory',
        default=None,
        help="""The directory to store all COGs. Leave empty to store COGs within
         each relevant STAC item's folder.""")
    @click.option('-o',
                  '--overwrite',
                  is_flag=True,
                  default=False,
                  help="Overwrite existing COGs.")
    def cogify_command(catalog_path, cog_directory, overwrite):
        """Convert geotiff assets into cloud optimized geotiffs.
        """
        cogify_catalog(catalog_path, cog_directory, overwrite)

        print("Finished!")

    return spot
