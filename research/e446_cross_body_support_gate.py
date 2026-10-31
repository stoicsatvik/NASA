"""E446 pre-event audit: are existing real-data receipts on comparable supports?

This checks source resolutions and footprints only. It does NOT identify
planetary analogues or develop a Space Apps competition solution.
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
E212 = ROOT / "results/e212_lola_mola_real_data_20261024.json"
E214 = ROOT / "results/e214_earth_skadi_real_data_20261024.json"
MIN_SAMPLES_PER_AXIS = 4  # transparent conservative diagnostic, not scientific law


def evaluate(lunar_mars, earth):
    if lunar_mars.get("grid_shape") != [720, 1440]:
        raise ValueError("E212 expected 4-pixel/degree global raster geometry")
    if len(earth.get("sites", [])) != 6:
        raise ValueError("E214 expected six Earth site-window records")
    pixels = lunar_mars["equatorial_pixel_north_south_km"]
    if set(pixels) != {"moon", "mars"} or any(x <= 0 for x in pixels.values()):
        raise ValueError("missing/invalid planetary pixel support")
    records = []
    for row in earth["sites"]:
        width = row["physical_window_km"]
        earth_pixel_km = row["metrics"]["pixel_m"]["north_south"] / 1000
        if width <= 0 or earth_pixel_km <= 0:
            raise ValueError("nonpositive Earth footprint/resolution")
        moon_samples = width / pixels["moon"]
        mars_samples = width / pixels["mars"]
        records.append({"site": row["site"], "earth_window_km": width,
                        "earth_pixels_north_south": row["metrics"]["shape"][0],
                        "moon_equatorial_pixel_count": moon_samples,
                        "mars_equatorial_pixel_count": mars_samples,
                        "moon_meets_one_pixel_gate": moon_samples >= 1,
                        "mars_meets_one_pixel_gate": mars_samples >= 1,
                        "moon_meets_four_sample_gate": moon_samples >= MIN_SAMPLES_PER_AXIS,
                        "mars_meets_four_sample_gate": mars_samples >= MIN_SAMPLES_PER_AXIS,
                        "moon_to_earth_pixel_size_ratio": pixels["moon"] / earth_pixel_km,
                        "mars_to_earth_pixel_size_ratio": pixels["mars"] / earth_pixel_km})
    return {"experiment": "E446", "source_experiments": ["E212", "E214"],
            "source_grid": lunar_mars["grid_shape"],
            "minimum_samples_per_axis": MIN_SAMPLES_PER_AXIS,
            "minimum_4pixel_support_km": {body: px * MIN_SAMPLES_PER_AXIS
                                         for body, px in pixels.items()},
            "all_six_earth_windows_fail_even_one_pixel_per_body": all(
                not r["moon_meets_one_pixel_gate"] and
                not r["mars_meets_one_pixel_gate"] for r in records),
            "all_six_earth_windows_fail_both_planetary_support_gates": all(
                not r["moon_meets_four_sample_gate"] and
                not r["mars_meets_four_sample_gate"] for r in records),
            "records": records,
            "claim": "support incompatibility for these real-data products only; E001 NOT YET MEASURED"}


def run():
    return evaluate(json.loads(E212.read_text()), json.loads(E214.read_text()))


if __name__ == "__main__":
    result = run()
    assert result["all_six_earth_windows_fail_even_one_pixel_per_body"]
    print(json.dumps(result, indent=2, sort_keys=True))
