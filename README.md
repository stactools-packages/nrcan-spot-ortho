[![Binder](https://mybinder.org/badge_logo.svg)](https://mybinder.org/v2/gh/stactools-packages/template/main?filepath=docs/installation_and_basic_usage.ipynb)

# stactools-nrcan-spot-ortho

A subpackage of stactools for working with [orthorectified SPOT 4 and 5 data over Canada](https://open.canada.ca/data/en/dataset/d799c202-603d-4e5c-b1eb-d058803f80f9).

This subpackage converts the [Geobase Index shapefile](http://ftp.maps.canada.ca/pub/nrcan_rncan/image/spot/geobase_orthoimages/index/GeoBase_Orthoimage_Index.zip), that describes the orthorectified SPOT 4 and 5 image extents, to a STAC catalog. 

Usage:
```
stac nrcan-spot-ortho convert-index [index location] [root_href]
```
The root href can be a local or S3 path. The default catalog type is `pystac.CatalogType.ABSOLUTE_PUBLISHED`.

The STAC catalog created contains assets with hrefs pointing to zipped imagery on the Geobase FTP. These can be be downloaded, unzipped and converted to COGs with:
```
stac nrcan-spot-ortho cogify-assets [catalog path] -d [COG directory]
```

By default the COGs will be written into the same directory's as their respective STAC items, and will __not__ overwrite existing COGs (use `--overwrite` to do so). The STAC will be updated with the COG assets during this process.

A complete orthorectified SPOT 4 and 5 STAC, including COGs, can be found [here](https://geobase-spot.s3.ca-central-1.amazonaws.com/catalog.json).
