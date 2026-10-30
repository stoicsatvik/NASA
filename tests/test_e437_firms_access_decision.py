import unittest
from decimal import Decimal as D
from research.e437_firms_access_decision import audit, score


class E437Tests(unittest.TestCase):
    def setUp(self):
        self.w = tuple(map(D, ('.22', '.20', '.18', '.15', '.10', '.10', '.05')))
        self.c = {
            'Planetary analogues': tuple(map(D, ('9','4','7','9','7','6','4','.8','1.5'))),
            'MODIS/VIIRS hotspots': tuple(map(D, ('8','8','4','8','5','8','7','.8','.7'))),
            'Earth trend detective': tuple(map(D, ('8','8','3','7','5','8','8','.8','.6'))),
            'CLPS lunar browser': tuple(map(D, ('8','6','3','8','3','7','6','1.1','1.1'))),
        }

    def test_original_scores_and_tie_thresholds(self):
        result = audit(self.c, self.w)
        self.assertEqual(result['historical_analogue_score'], '4.59')
        self.assertEqual(result['planetary_validation_for_tie']['MODIS/VIIRS hotspots'], '8.2')
        self.assertEqual(result['planetary_validation_for_tie']['Earth trend detective'], '7.3')

    def test_modis_validation_stress_does_not_erase_earth_trend(self):
        result = audit(self.c, self.w)
        self.assertEqual([s['modis_score'] for s in result['modis_validation_stress']], ['5.43','5.03','4.63','3.83'])
        self.assertEqual([s['highest_scoring_old_label'] for s in result['modis_validation_stress']],
                         ['MODIS/VIIRS hotspots','Earth trend detective','Earth trend detective','Earth trend detective'])

    def test_no_silent_navigator_alias(self):
        result = audit(self.c, self.w)
        self.assertIn('NOT Lunar Landing Site Navigator', result['current_challenge_coverage'])

    def test_reject_nonfinite_and_out_of_range(self):
        bad = list(self.c['Planetary analogues']); bad[1] = D('NaN')
        with self.assertRaises(ValueError): score(bad, self.w)
        bad[1] = D('11')
        with self.assertRaises(ValueError): score(bad, self.w)

    def test_reject_missing_historical_identity(self):
        c = dict(self.c); del c['CLPS lunar browser']
        with self.assertRaises(ValueError): audit(c, self.w)


if __name__ == '__main__':
    unittest.main()
