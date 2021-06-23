import logging

import click
import pystac

from stactools.spot.stac import build_items
from stactools.spot.stac_templates import build_catalog

logger = logging.getLogger(__name__)


def create_spot_command(cli):
    """Creates a command group for commands dealing with spot data
    """
    @cli.group('spot', short_help="Commands for working with spot data")
    def spot():
        pass

    @spot.command('convert-index',
                  short_help='Convert SPOT index shapefile to STAC catalog')
    @click.argument('index')
    @click.argument('root_href')
    @click.argument('test', default=False)
    @click.option('-c',
                  '--catalog-type',
                  type=click.Choice([
                      pystac.CatalogType.ABSOLUTE_PUBLISHED,
                      pystac.CatalogType.RELATIVE_PUBLISHED,
                      pystac.CatalogType.SELF_CONTAINED
                  ],
                                    case_sensitive=False),
                  default=pystac.CatalogType.RELATIVE_PUBLISHED)
    def convert_command(index, root_href, test, catalog_type):
        """Converts the SPOT Index shapefile to a STAC Catalog.
        """
        GeobaseSTAC = build_catalog()
        build_items(index, GeobaseSTAC, test)
        GeobaseSTAC.normalize_and_save(root_href, catalog_type)
        print("Finished!")

    return spot
