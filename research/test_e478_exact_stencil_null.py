"""E478 offline contracts; source-dependent checks require the archived E472 artifact."""
import importlib.util
import os
from pathlib import Path
import pytest

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('e478', HERE / 'e478_exact_stencil_null.py')
e478 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(e478)


def test_full_and_empty_stencil_counts():
    full = e478.bitmask(['11111'] * 5)
    empty = e478.bitmask(['00000'] * 5)
    assert e478.count_stencils(full, e478.stencils(5)) == 9
    assert e478.count_stencils(full, e478.stencils(5, True)) == 9
    assert e478.count_stencils(empty, e478.stencils(5)) == 0
    assert e478.count_stencils(empty, e478.stencils(5, True)) == 0


def test_malformed_and_tampered_source(tmp_path):
    with pytest.raises(ValueError):
        e478.bitmask(['100', '10', '111'])
    with pytest.raises(ValueError):
        e478.bitmask(['abc', '101', '111'])
    p = tmp_path / 'source.json'
    p.write_text('{}')
    with pytest.raises(ValueError, match='unpinned'):
        e478.load(p, 'mars')


def test_exact_enumeration_independent_cpp_oracle():
    # Independently enumerated using a C++20 Gosper-bitmask implementation.
    for k, total, zero_cross, zero_full in (
        (3, 2300, 2300, 2300),
        (11, 4457400, 4122758, 4456320),
        (15, 3268760, 1995810, 3200192),
    ):
        got = e478.exact_fixed_count(5, k, 0, 0)
        assert (got['total_masks'], got['cross_le_count'], got['full_le_count']) == (
            total, zero_cross, zero_full)


def test_archived_source_cohort():
    root = Path(os.environ.get('E478_ARTIFACT_DIR', HERE))
    mars, moon = root / 'e472_mars_source.json', root / 'e472_moon_source.json'
    if not mars.exists() or not moon.exists():
        pytest.skip('E472 archived artifact absent; never substitute synthetic source')
    result = e478.evaluate(e478.load(mars, 'mars'), e478.load(moon, 'moon'))
    assert [w['observed'] for w in result['windows'][:3]] == [11, 3, 15]
    assert [w['observed_cross'] for w in result['windows'][:3]] == [0, 0, 0]
    assert [w['cross'] for w in result['windows'][3:]] == [0, 0, 49]


def test_inclusion_exclusion_and_95pct_screen():
    for k, zero, total in ((3,2300,2300),(11,4122758,4457400),(15,1995810,3268760)):
        assert e478.exact_any_stencil_probability(5,k) == pytest.approx(1-zero/total)
    assert next(k for k in range(26) if e478.exact_any_stencil_probability(5,k)>=0.95)==21
    assert e478.exact_any_stencil_probability(5,20) < 0.95
    assert e478.exact_any_stencil_probability(5,21) > 0.95
