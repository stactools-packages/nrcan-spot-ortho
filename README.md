# stactools-spot

A subpackage of stactools for working with [SPOT](https://open.canada.ca/data/en/dataset/d799c202-603d-4e5c-b1eb-d058803f80f9) data.

This subpackage converts the [Geobase Index shapefile](http://ftp.maps.canada.ca/pub/nrcan_rncan/image/spot/geobase_orthoimages/index/GeoBase_Orthoimage_Index.zip), that describes the SPOT image extents, to a STAC catalog.

Usage:
```
stac spot convert-index [index shapefile location] [root href] -c [catalog type]
```
The root href can be a local or S3 path. The default catalog type is `pystac.CatalogType.ABSOLUTE_PUBLISHED`.

The STAC catalog created contains assets with hrefs pointing to zipped imagery on the Geobase FTP. These can be be downloaded, unzipped and converted to COGs with:
```
stac spot cogify-assets [catalog path] -d [COG directory] -o [overwrite]
```

By default the COGs will be written into the same directory's as their respective STAC items, and will __not__ overwrite existing COGs. The STAC will be updated with the COG assets during this process.

A complete SPOT STAC, including COGs, can be found [here](). An API for this STAC can be found [here]().