# E536 — Grand Falls ScienceBase metadata/file-listing probe (2026-11-11)

## Question

Can the official ScienceBase REST API expose the public item metadata and attached-file listings for the Grand Falls field datasets, resolving E535's current data-access uncertainty without downloading large raster, image or time-series payloads?

## Pinned item set

The manifest at data/grand_falls_sciencebase_item_manifest.csv records five official USGS Data Catalog item IDs and their DOI relationships:

- 2022–2023 ripple photogrammetry: item 662bccfad34ea70bd5f11f88, DOI 10.5066/P9FRH62D.
- 2023–2024 integrated sediment transport release: item 67bf94acd34e8876fcbfc91b, DOI 10.5066/P13HPPYM.
- 2024 photogrammetry component: item 67b78df2d34e1a2e835b13b7, also DOI 10.5066/P13HPPYM; it is not an independent release or site.
- 2009–2014 long-term meteorology: item 68c05cbbd4be025f1dac0cd4, DOI 10.5066/P1TJFD9N.
- April–July 2023 meteorological component: item 662ac4a0d34ea70bd5f0bc9c, DOI 10.5066/P9YQLHHB.

The 2009–2014 meteorology release is a newly identified temporal extension for the same Grand Falls site, not another positive site. The catalog describes 10-minute interval-averaged air temperature, wind speed/direction, maximum wind speed and cumulative precipitation.

## Probe design

- Read-only GET requests to the official ScienceBase catalog item JSON endpoint.
- For each item, query its direct child listing using the documented parentId filter.
- Do not download raw DEMs, orthomosaics, imagery, weather series or sediment files.
- Record HTTP status, response SHA-256, response size, item ID/title/access level, direct file count and bounded child summaries.
- Store only file names, sizes, content types, URL host and URL path. Strip all URL query strings.
- Enforce HTTPS and an exact ScienceBase catalog host/path allowlist; cap metadata responses at 5 MiB and child summaries at 100.
- Preserve 403/404/network errors as access results rather than pretending the item is empty.

## Source documentation

USGS documents that ScienceBase items can be read as JSON by appending format=json to an item URL, and documents parentId filtering for direct child items:

- https://www.usgs.gov/sciencebase-instructions-and-documentation/api-and-web-services
- https://www.usgs.gov/sciencebase-instructions-and-documentation/search-queries

Official Data Catalog records:

- https://data.usgs.gov/datacatalog/data/USGS%3A662bccfad34ea70bd5f11f88
- https://data.usgs.gov/datacatalog/data/USGS%3A67bf94acd34e8876fcbfc91b
- https://data.usgs.gov/datacatalog/data/USGS%3A67b78df2d34e1a2e835b13b7
- https://data.usgs.gov/datacatalog/data/USGS%3A68c05cbbd4be025f1dac0cd4
- https://data.usgs.gov/datacatalog/data/USGS%3A662ac4a0d34ea70bd5f0bc9c

## Claim boundary

A successful item JSON or child listing is metadata access only. It does not establish that a DEM is georeferenced correctly, that raster CRS/resolution/nodata/vertical datum are suitable, that meteorological sensors are calibrated, or that any Earth descriptor is comparable to a Mars descriptor. No E001 score, analogue label, or cross-body similarity claim follows from metadata access.

## Next gate

If file listings are available, select one small DEM/orthomosaic plus its processing report and one matched weather/imagery interval. Before any analysis, preserve original URLs, item/file IDs, byte sizes and SHA-256; then inspect CRS, pixel size, nodata, vertical units/datum, acquisition timestamps and processing metadata. If the API does not expose files, preserve the access failure and use the official USGS catalog's data links rather than scraping or guessing filenames.
