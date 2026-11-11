"""E542: metadata-only coverage and reference audit for a Jezero Mars data stack."""
from __future__ import annotations

import json
import math

DATASETS = {
    "mola_128ppd": {
        "name": "MGS MOLA MEGT44N000HB",
        "bbox": [0.0, 0.0, 90.0, 44.0],
        "resolution_m": 463.0,
        "radius_m": 3396000.0,
        "projection": "simple_cylindrical",
        "reference_system": "IAU2000",
        "latitude_type": "planetocentric",
        "longitude_direction": "positive_east",
        "control_net": "MOLA",
        "source": "https://pds-geosciences.wustl.edu/mgs/urn-nasa-pds-mgs_mola_topography_derived/meg128/megt44n000hb.lbl",
        "notes": [
            "128 pixels/degree; 0.463 km/pixel at the equator.",
            "Bins without observations receive interpolated topography.",
            "The PDS label reports about 55% of equatorial bins contain a shot and gaps can reach 12 km.",
            "That is a global equatorial statistic, not a Jezero-local support measurement; acquire the local counts raster."
        ],
    },
    "ctx_trn_2020": {
        "name": "Mars 2020 TRN CTX DTM Mosaic",
        "bbox": [77.1605, 18.211, 77.6990, 18.7212],
        "resolution_m": 20.0,
        "radius_m": 3396190.0,
        "projection": "equirectangular",
        "reference_system": "Mars_2015",
        "latitude_type": "planetocentric",
        "longitude_direction": "positive_east",
        "control_net": "MOLA",
        "horizontal_displacement_m": 9.6,
        "vertical_registration_m": 3.8,
        "source": "https://astrogeology.usgs.gov/search/map/mars_2020_terrain_relative_navigation_ctx_dtm_mosaic",
        "doi": "10.5066/P906QQT8",
    },
    "hirise_msr_2025": {
        "name": "Mars Sample Return TRN HiRISE DTM and Orthoimage Mosaics",
        "bbox": [77.0570, 18.1350, 77.3800, 18.5880],
        "resolution_m": 1.0,
        "radius_m": 3396190.0,
        "projection": "equirectangular",
        "reference_system": "Mars_2015",
        "latitude_type": "planetocentric",
        "longitude_direction": "positive_east",
        "control_net": "MOLA",
        "alignment_p93_m": 6.0,
        "alignment_p99_m": 10.2,
        "stereo_pairs_completed": 8,
        "stereo_pairs_planned": 10,
        "source": "https://astrogeology.usgs.gov/search/map/mars-sample-return-terrain-relative-navigation-hirise-dtm-mosaic",
        "doi": "10.5066/P13CPYYU",
    },
    "ctx_science_investigation_2021": {
        "name": "Mars 2020 Science Investigation CTX DEM Mosaic",
        "bbox": [76.99, 17.58, 78.58, 19.29],
        "resolution_m": 20.0,
        "radius_m": 3396160.0,
        "projection": "equirectangular",
        "reference_system": "Mars_2015",
        "latitude_type": "planetocentric",
        "longitude_direction": "positive_east",
        "control_net": "MOLA",
        "source": "https://astrogeology.usgs.gov/search/map/mars_2020_science_investigation_ctx_dem_mosaic",
        "doi": "USGS data release, 2021-10-14",
        "notes": [
            "This extends the original TRN CTX DEM with additional CTX orbits.",
            "The added DEMs were localized to MOLA; the published Jezero comparison reports significant pixel offsets from HRSC.",
            "Do not substitute this larger-extent extension for the TRN reference without independent registration."
        ],
    },
}


def validate_bbox(bbox):
    if not isinstance(bbox, (list, tuple)) or len(bbox) != 4:
        raise ValueError("bbox must be [west, south, east, north]")
    if any(
        isinstance(value, bool)
        or not isinstance(value, (int, float))
        or not math.isfinite(value)
        for value in bbox
    ):
        raise ValueError("bbox coordinates must be finite numbers")
    west, south, east, north = (float(value) for value in bbox)
    if not (-180 <= west < east <= 360 and -90 <= south < north <= 90):
        raise ValueError("bbox bounds are invalid")
    return west, south, east, north


def contains_bbox(outer, inner):
    ow, os, oe, on = validate_bbox(outer)
    iw, ins, ie, inn = validate_bbox(inner)
    return ow <= iw and os <= ins and oe >= ie and on >= inn


def intersection_bbox(a, b):
    aw, ass, ae, an = validate_bbox(a)
    bw, bs, be, bn = validate_bbox(b)
    result = [max(aw, bw), max(ass, bs), min(ae, be), min(an, bn)]
    return result if result[0] < result[2] and result[1] < result[3] else None


def spherical_bbox_area_km2(bbox, radius_m=3396190.0):
    west, south, east, north = map(math.radians, validate_bbox(bbox))
    return (
        radius_m**2
        * abs(east - west)
        * abs(math.sin(north) - math.sin(south))
        / 1_000_000
    )


def mola_local_pixel_spacing_m(latitude_deg, equatorial_spacing_m=463.0):
    """Return local ground spacing for a simple-cylindrical MOLA grid."""
    for value, name in (
        (latitude_deg, "latitude_deg"),
        (equatorial_spacing_m, "equatorial_spacing_m"),
    ):
        if (
            isinstance(value, bool)
            or not isinstance(value, (int, float))
            or not math.isfinite(value)
        ):
            raise ValueError(f"{name} must be a finite number")
    latitude = float(latitude_deg)
    equatorial_spacing = float(equatorial_spacing_m)
    if not -90.0 <= latitude <= 90.0:
        raise ValueError("latitude_deg must be within [-90, 90]")
    if equatorial_spacing <= 0.0:
        raise ValueError("equatorial_spacing_m must be positive")
    return {
        "east_west_m": equatorial_spacing * math.cos(math.radians(latitude)),
        "north_south_m": equatorial_spacing,
    }


def build_result():
    mola = DATASETS["mola_128ppd"]
    ctx = DATASETS["ctx_trn_2020"]
    hirise = DATASETS["hirise_msr_2025"]
    science = DATASETS["ctx_science_investigation_2021"]
    overlap = intersection_bbox(ctx["bbox"], hirise["bbox"])
    overlap_centroid_latitude_deg = (
        (overlap[1] + overlap[3]) / 2 if overlap is not None else None
    )
    local_mola_spacing = (
        mola_local_pixel_spacing_m(overlap_centroid_latitude_deg, mola["resolution_m"])
        if overlap_centroid_latitude_deg is not None
        else None
    )
    return {
        "experiment": "E542_JEZERO_MULTI_RESOLUTION_COVERAGE_AND_REFERENCE_AUDIT",
        "status": "METADATA_COVERAGE_COMPATIBLE_RAW_RASTER_VALIDATION_PENDING",
        "area": "Jezero crater, Mars",
        "datasets": DATASETS,
        "coverage": {
            "mola_tile_contains_ctx_envelope": contains_bbox(mola["bbox"], ctx["bbox"]),
            "mola_tile_contains_hirise_envelope": contains_bbox(mola["bbox"], hirise["bbox"]),
            "ctx_hirise_overlap_bbox": overlap,
            "ctx_hirise_overlap_bbox_area_km2": spherical_bbox_area_km2(overlap) if overlap else 0.0,
            "ctx_contains_entire_hirise_envelope": contains_bbox(ctx["bbox"], hirise["bbox"]),
            "interpretation": "Bounding-box envelope intersection only; nodata holes and valid-pixel footprints are not measured.",
        },
        "scale": {
            "mola_equatorial_resolution_m": mola["resolution_m"],
            "mola_to_ctx_linear_resolution_ratio": mola["resolution_m"] / ctx["resolution_m"],
            "ctx_to_hirise_linear_resolution_ratio": ctx["resolution_m"] / hirise["resolution_m"],
            "mola_to_hirise_linear_resolution_ratio": mola["resolution_m"] / hirise["resolution_m"],
            "mola_local_spacing_at_ctx_hirise_overlap_centroid": (
                {
                    "planetocentric_latitude_deg": overlap_centroid_latitude_deg,
                    **local_mola_spacing,
                }
                if local_mola_spacing is not None
                else None
            ),
            "mola_local_to_ctx_resolution_ratio_at_overlap_centroid": (
                {
                    "east_west": local_mola_spacing["east_west_m"] / ctx["resolution_m"],
                    "north_south": local_mola_spacing["north_south_m"] / ctx["resolution_m"],
                }
                if local_mola_spacing is not None
                else None
            ),
            "mola_local_to_hirise_resolution_ratio_at_overlap_centroid": (
                {
                    "east_west": local_mola_spacing["east_west_m"] / hirise["resolution_m"],
                    "north_south": local_mola_spacing["north_south_m"] / hirise["resolution_m"],
                }
                if local_mola_spacing is not None
                else None
            ),
            "nominal_ratio_interpretation": (
                "The 463 m MOLA spacing is equatorial. In the simple-cylindrical grid, "
                "east-west ground spacing contracts by cos(latitude); report local "
                "east-west and north-south ratios separately."
            ),
        },
        "reference_differences": {
            "mola_iau2000_to_mars2015_radius_delta_m": ctx["radius_m"] - mola["radius_m"],
            "science_investigation_ctx_to_trn_ctx_radius_delta_m": science["radius_m"] - ctx["radius_m"],
            "mola_reference_system": mola["reference_system"],
            "ctx_hirise_reference_system": ctx["reference_system"],
            "common_latitude_type": "planetocentric",
            "common_longitude_direction": "positive_east",
            "same_reference_system": False,
            "warning": "Sphere-radius differences are metadata reference differences, not measured elevation biases or a vertical correction.",
        },
        "product_selection": {
            "candidate_registered_pair": ["ctx_trn_2020", "hirise_msr_2025"],
            "mola_role": "coarse context only until local observation-count support is measured",
            "science_investigation_ctx": "larger-extent alternative; not the default registration reference",
            "hirise_2025": "extension candidate; its exact CTX reference identity must be pinned before raster overlay",
        },
        "evidence_ceiling": {
            "raw_raster_bytes_ingested": False,
            "pixel_values_inspected": False,
            "mola_local_counts_sampled": False,
            "metadata_coverage": "SUPPORTED_AS_PUBLISHED_METADATA_ONLY",
            "cross_body_similarity": "NOT YET PROVEN",
            "known_site_recovery": "NOT YET MEASURED",
            "novel_analogue_discovery": "NOT YET PROVEN",
            "challenge_selection_superiority": "NOT YET PROVEN",
        },
        "next": [
            "Acquire the 9.3 MB official TRN CTX DTM and a matching bounded HiRISE raster subset; inspect actual GeoTIFF labels, nodata, pixel values and footprints.",
            "Acquire the MOLA 128ppd topography and counts tile; distinguish observed from interpolated cells over the Jezero overlap.",
            "Pin the exact CTX reference used by the 2025 HiRISE mosaic and transform all rasters into one explicit Mars body-fixed reference system.",
            "Compare registered elevation profiles and horizontal control residuals on the shared valid-pixel footprint.",
            "Use local MOLA east-west and north-south ground spacing separately; do not treat the equatorial 463 m value as an isotropic Jezero pixel size.",
        ],
    }


if __name__ == "__main__":
    print(json.dumps(build_result(), indent=2, sort_keys=True))
