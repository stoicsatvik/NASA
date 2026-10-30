"""Offline deterministic E436 tests; no network or new analogue labels."""
from __future__ import annotations
import json
import tempfile
import unittest
from pathlib import Path
from research.e436_e430_permutation_null import (
    FEATURES, SITES, audit, exact_label_null, load, predicted_indices,
)

class E436LabelNullTests(unittest.TestCase):
    def setUp(self):
        self.rows = [
            {'site': site, 'physical_window_km': km,
             'metrics': {name: float((i+1)*(j+2) + (0.5 if km == 2 else 0))
                         for j,name in enumerate(FEATURES)}}
            for i,site in enumerate(SITES) for km in (2,4)
        ]

    def test_exact_joint_permutation_distribution(self):
        x = exact_label_null((0,1,1))
        self.assertEqual(x['observed'], 2)
        self.assertEqual(sorted(x['null_counts']), [0,0,1,1,2,2])
        self.assertEqual(x['tail_ge_observed'], 1/3)

    def test_frozen_real_source_and_three_scalers(self):
        # The six real-source rows are already tracked in E214, not fetched live.
        x = load()
        for mode in ('pooled_z','catalog_z','other_sites_z','log_ratio'):
            self.assertEqual(predicted_indices(x,mode), (0,1,1))
        report = audit(x)
        self.assertEqual(len(report['configurations']), 20)
        self.assertEqual(report['best_of_20']['observed'], 2)
        self.assertEqual(report['best_of_20']['null_counts'], [2,2,1,1,2,2])
        self.assertEqual(report['best_of_20']['tail_ge_observed'], 2/3)

    def test_invalid_source_or_incomplete_rows_fail_closed(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'fixture.json'
            path.write_text(json.dumps({'experiment':'wrong','sites':self.rows}))
            with self.assertRaisesRegex(ValueError,'E214'): load(path)
            path.write_text(json.dumps({'experiment':'E214 real Earth fixture','sites':self.rows[:-1]}))
            with self.assertRaisesRegex(ValueError,'six'): load(path)

    def test_nonfinite_input_and_invalid_modes_fail_closed(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'fixture.json'
            self.rows[0]['metrics'][FEATURES[0]] = float('nan')
            path.write_text(json.dumps({'experiment':'E214 real Earth fixture','sites':self.rows}))
            with self.assertRaisesRegex(ValueError,'Nonpositive'): load(path)
        with self.assertRaisesRegex(ValueError,'Invalid distance'): predicted_indices({},'invalid')
        with self.assertRaisesRegex(ValueError,'Three candidate'): exact_label_null((0,1))

    def test_label_permutation_cannot_masquerade_as_site_count(self):
        with self.assertRaises(ValueError): exact_label_null((0,0,3))
        with self.assertRaises(ValueError): exact_label_null((0,True,1))

if __name__ == '__main__': unittest.main()
