# Local point-sample ingestion audit (2026-11-04)

**Scope:** pre-ingestion quality gate for issue #3, not a successful LOLA/Diviner/MOLA/THEMIS/Earthdata ingestion. No external samples were downloaded in this change. Do not mark dataset-matrix access-test rows as verified.

Run from repository root:

```sh
python -m unittest discover -s experiments -p 'test_validate_sample.py' -v
python experiments/validate_sample.py /path/to/real_sample.csv /path/to/metadata.json
```

CSV header must be `latitude,longitude,value` (extra columns permitted). Longitude must be in [-180,180], latitude in [-90,90]; convert source coordinates explicitly **before** running, recording that transformation separately. Degrees alone do not identify a planetary coordinate reference frame: the metadata must specify the convention, and the script does not verify it. The script does not parse PDS rasters, IMG labels, NetCDF, GeoTIFF or projected imagery.

Example metadata shape (all values below **fictional**, not source evidence):

```json
{
  "source_url": "https://example.org/fixture",
  "product_id": "SYNTHETIC",
  "body": "Mars",
  "coordinate_frame": "planetocentric-east-positive",
  "latitude_unit": "degree",
  "longitude_unit": "degree",
  "value_unit": "m",
  "native_resolution": "100",
  "native_resolution_unit": "m/pixel",
  "missing_tokens": ["-9999", ""]
}
```

Fail-closed controls reject missing provenance, unsupported coordinate units, out-of-range/nonfinite coordinates, undeclared fill values, nonfinite measurements and zero usable measurements. Output records SHA-256 of source CSV, valid/missing counts, min/max and supplied metadata. It cannot authenticate the stated provenance or infer the true physical units, projection, resolution or instrument calibration. Keep actual downloaded source URL, product ID, processing command, acquisition time, label/metadata file and checksum alongside any eventual real sample audit. No cross-body scientific comparability is established.

**Validation:** seven synthetic `unittest` controls passed locally on a closely matching pre-commit implementation. GitHub exact-head CI has **not** been established; rerun tests on this branch. The negative result remains: no real planetary source ingestion has yet been reproduced here.

**Next falsifiable gate:** obtain one publicly accessible small MOLA/LOLA sample and its authoritative product label, explicitly convert coordinate frame and missing-value sentinel, run the audit, compare reported units/resolution with the label, and archive the checksum plus a reproducible acquisition command. If any field cannot be independently verified, report failure instead of silently treating the dataset as usable.
