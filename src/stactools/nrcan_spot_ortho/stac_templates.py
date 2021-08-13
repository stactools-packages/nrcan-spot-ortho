from datetime import datetime
from pystac.extensions.eo import Band, SummariesEOExtension
from pystac.extensions.projection import SummariesProjectionExtension

from pystac import (Catalog, Collection, Extent, Link, Provider, SpatialExtent,
                    TemporalExtent, Summaries)

spot_sensor = {"S4": "SPOT 4", "S5": "SPOT 5"}

image_types = {
    "m20_1": "B1",
    "m20_2": "B2",
    "m20_3": "B3",
    "m20_4": "B4",
    "p10_1": "pan"
}

proj_epsg = {f"utm{str(i).zfill(2)}": 26900 + i for i in range(1, 25)}
proj_epsg["lcc00"] = 3979

spot_catalog = Catalog(
    id="nrcan-spot-ortho",
    description="STAC Catalog for orthorectified SPOT 4 and 5 data of Canada",
    title="STAC Catalog for orthorectified SPOT 4 and 5 data of Canada",
    stac_extensions=None)

spot45_catalog = Catalog(
    id="canada-spot-orthoimages",
    description="STAC Catalog for orthorectified SPOT 4 and 5 data of Canada",
    title="STAC Catalog for orthorectified SPOT 4 and 5 data of Canada",
    stac_extensions=None)

geobase_providers = [
    Provider(
        "Government of Canada",
        "Natural Resources; Strategic Policy and Results Sector",
        ["licensor", "processor"],
        "https://open.canada.ca/data/en/dataset/d799c202-603d-4e5c-b1eb-d058803f80f9"
    ),
    Provider("PCI Geomatics", "info@pci.com", ["processor", "host"],
             "www.pcigeomatics.com"),
    Provider("Sparkgeo", "info@sparkegeo.com", ["processor", "host"],
             "www.sparkgeo.com"),
]

geobase_license = Link(
    "license",
    "https://open.canada.ca/en/open-government-licence-canada",
    "text",
    "Open Government Licence Canada",
)

spot_extents = Extent(
    SpatialExtent([[
        35.324804300674494, -169.69075486542908, 68.02144065697097,
        -15.505275588132838
    ]]),
    TemporalExtent([[
        datetime.strptime("2005-05-01", "%Y-%m-%d"),
        datetime.strptime("2010-10-31", "%Y-%m-%d"),
    ]]),
)

spot_bands = {
    "B1":
    Band(
        dict(name="B1",
             common_name="green",
             description="Green: 500-590nm",
             center_wavelength=0.545,
             full_width_half_max=0.09)),
    "B2":
    Band(
        dict(name="B2",
             common_name="red",
             description="Red: 610-680 nm",
             center_wavelength=0.645,
             full_width_half_max=0.07)),
    "B3":
    Band(
        dict(name="B3",
             common_name="nir",
             description="Near Infrared: 780-890 nm",
             center_wavelength=0.835,
             full_width_half_max=0.11)),
    "B4":
    Band(
        dict(name="B4",
             common_name="swir16",
             description="ShortWave Infrared: 1580-1750 nm",
             center_wavelength=1.665,
             full_width_half_max=0.170)),
}

spot_pan = {
    "S4":
    Band(
        dict(name="pan",
             common_name="pan",
             description="Panchromatic: 610-680 nm",
             center_wavelength=0.645,
             full_width_half_max=0.07)),
    "S5":
    Band(
        dict(name="pan",
             common_name="pan",
             description="Panchromatic: 480-710 nm",
             center_wavelength=0.595,
             full_width_half_max=0.230))
}

spot4_collection = Collection(
    id="canada-spot4-orthoimages",
    description="SPOT 4 orthoimages of Canada",
    extent=spot_extents,
    title="SPOT 4 orthoimages of Canada",
    stac_extensions=[
        "https://stac-extensions.github.io/eo/v1.0.0/schema.json",
        "https://stac-extensions.github.io/projection/v1.0.0/schema.json",
    ],
    license="Proprietery",
    keywords=["SPOT", "Geobase", "orthoimages"],
    providers=geobase_providers,
    summaries=Summaries(
        dict(
            platform=["SPOT 5"],
            instruments=["HRVIR"],
            constellation=["SPOT"],
            gsd=[10, 20],
        )))
eo_ext = SummariesEOExtension(spot4_collection)
eo_ext.bands = list(spot_bands.values()) + [spot_pan["S4"]]
proj_ext = SummariesProjectionExtension(spot4_collection)
proj_ext.epsg = list(proj_epsg.values())

spot5_collection = Collection(
    id="canada-spot5-orthoimages",
    description="SPOT 5 orthoimages of Canada",
    extent=spot_extents,
    title="SPOT 5 orthoimages of Canada",
    stac_extensions=[
        "https://stac-extensions.github.io/eo/v1.0.0/schema.json",
        "https://stac-extensions.github.io/projection/v1.0.0/schema.json",
    ],
    license="Proprietery",
    keywords=["SPOT", "Geobase", "orthoimages"],
    providers=geobase_providers,
    summaries=Summaries(
        dict(
            platform=["SPOT 5"],
            instruments=["HVG"],
            constellation=["SPOT"],
            gsd=[2.5, 5, 10, 20],
        )))
eo_ext = SummariesEOExtension(spot5_collection)
eo_ext.bands = list(spot_bands.values()) + [spot_pan["S5"]]
proj_ext = SummariesProjectionExtension(spot5_collection)
proj_ext.epsg = list(proj_epsg.values())


def build_root_catalog():
    spot4_collection.add_link(geobase_license)
    spot5_collection.add_link(geobase_license)
    spot_catalog.add_child(spot45_catalog)
    spot45_catalog.add_child(spot4_collection)
    spot45_catalog.add_child(spot5_collection)
    return spot_catalog
