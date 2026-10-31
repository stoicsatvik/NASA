"""E452: test whether real MOLA 16ppd rescues E446's Earth-window support gate.

Metadata-only comparison; not analogue retrieval or a terrain similarity score.
"""
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parent / "results"


def evaluate(mola16, coarse, earth):
    if mola16.get("pixels_per_degree") != 16 or mola16.get("shape") != [2880, 5760]:
        raise ValueError("E210 must be the 16ppd global MOLA product")
    if coarse.get("grid_shape") != [720, 1440]:
        raise ValueError("E212 must be the 4ppd global products")
    px = coarse["equatorial_pixel_north_south_km"]
    if set(px) != {"moon", "mars"} or not all(math.isfinite(v) and v > 0 for v in px.values()):
        raise ValueError("invalid planetary pixel spacing")
    if len(earth.get("sites", [])) != 6:
        raise ValueError("expected six real E214 windows")
    if not 0 < mola16.get("observed_fraction", 0) <= 1:
        raise ValueError("invalid MOLA measured-cell fraction")
    mars16_km = px["mars"] / 4  # same planet; 16ppd vs 4ppd
    records = []
    for row in earth["sites"]:
        width = row["physical_window_km"]
        if not isinstance(width, (int, float)) or not math.isfinite(width) or width <= 0:
            raise ValueError("invalid Earth window width")
        samples = {"moon_4ppd": width / px["moon"],
                   "mars_4ppd": width / px["mars"],
                   "mars_16ppd": width / mars16_km}
        records.append({"site": row["site"], "window_km": width,
                        "pixel_spans": samples,
                        "mars_16ppd_at_least_one": samples["mars_16ppd"] >= 1,
                        "mars_16ppd_at_least_four": samples["mars_16ppd"] >= 4,
                        "moon_4ppd_at_least_four": samples["moon_4ppd"] >= 4})
    return {"experiment": "E452", "inputs": ["E210", "E212", "E214"],
            "equatorial_pixel_km": {"moon_4ppd": px["moon"],
                                    "mars_4ppd": px["mars"],
                                    "mars_16ppd": mars16_km},
            "four_pixel_minimum_km": {"moon_4ppd": 4 * px["moon"],
                                       "mars_16ppd": 4 * mars16_km},
            "mars16_one_pixel_windows": sum(r["mars_16ppd_at_least_one"] for r in records),
            "mars16_four_pixel_windows": sum(r["mars_16ppd_at_least_four"] for r in records),
            "moon4_four_pixel_windows": sum(r["moon_4ppd_at_least_four"] for r in records),
            "mola16_global_measured_fraction": mola16["observed_fraction"],
            "mola16_site_specific_measured_fraction": None,
            "records": records,
            "claim": "4km Earth windows cross one MOLA16 pixel but none meet 4-pixel diagnostic; E001 NOT YET MEASURED"}


def run():
    def load(name):
        return json.loads((ROOT / name).read_text())
    return evaluate(load("e210_mola_16ppd_real_data_20261024.json"),
                    load("e212_lola_mola_real_data_20261024.json"),
                    load("e214_earth_skadi_real_data_20261024.json"))


if __name__ == "__main__":
    print(json.dumps(run(), indent=2, sort_keys=True))
