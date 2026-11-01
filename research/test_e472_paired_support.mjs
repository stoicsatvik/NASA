import test from 'node:test';
import assert from 'node:assert/strict';
import { validateMask, centerCount, evaluate } from './e472_paired_support.mjs';
const LAT = [-0.5, -20, -40];
const zeros = Array.from({length: 9}, () => '000000000');
const ones = Array.from({length: 9}, () => '111111111');
const middle = Array.from({length: 9}, (_, i) => i >= 2 && i <= 6 ? '001111100' : '000000000');
function fixture() {
  const mars = {
    schema: 'nasa/e463/mola128-bounded-real-data-coverage/v1',
    metadata: {megc: {ppd: 128, sample_bits: 8}},
    pds3_labels_sha256: {megc: 'source-fingerprint'},
    windows: LAT.map(lat => ({
      latitude_deg_requested: lat, longitude_deg_requested: 45, sampled_cells: 81,
      measured_cells: 25, center_5x5_observed_cells: 25,
      observed_mask_rows: middle, sampled_count_range_sha256: 'mars-range',
    })),
  };
  const moon = {
    schema: 'nasa/e469/lola128-bounded-count-coverage/v1',
    metadata: {count: {ppd: 128, bits: 16}},
    source_labels_sha256: {count: 'source-fingerprint'},
    windows: LAT.map(lat => ({
      latitude_deg_requested: lat, longitude_deg_requested: 45, sampled_cells: 81,
      observed_cells: 81, observed_mask_rows: ones, count_range_sha256: 'moon-range',
    })),
  };
  return {mars, moon};
}
test('mask decoding preserves count and 5x5 central registration', () => {
  assert.equal(validateMask(middle, 25), 25);
  assert.equal(centerCount(middle), 25);
  assert.equal(centerCount(zeros), 0);
  assert.equal(validateMask(ones, 81), 81);
});
test('paired footprints are physically close, not equal-angle pixels', () => {
  const {mars, moon} = fixture();
  const r = evaluate(mars, moon);
  assert.equal(r.windows.length, 3);
  assert.ok(r.physical_support.moon_9x9_span_north_south_km > 1.8);
  assert.ok(r.physical_support.mars_5x5_span_north_south_km > 1.8);
  assert.ok(r.physical_support.relative_span_difference < 0.03);
  assert.equal(r.windows[0].mars_5x5_observed, 25);
  assert.equal(r.known_site_recovery, 'NOT YET MEASURED');
});
test('zero-count Mars window is preserved rather than invented', () => {
  const {mars, moon} = fixture();
  for (const m of mars.windows) {
    m.measured_cells = 0;
    m.center_5x5_observed_cells = 0;
    m.observed_mask_rows = zeros;
  }
  const r = evaluate(mars, moon);
  assert.ok(r.windows.every(x => x.mars_5x5_observed === 0));
});
test('aggregate count cannot silently replace a spatial mask', () => {
  const {mars, moon} = fixture();
  delete mars.windows[0].observed_mask_rows;
  assert.throws(() => evaluate(mars, moon), /mask/);
});
test('count-mask contradiction fails closed', () => {
  const {mars, moon} = fixture();
  mars.windows[1].measured_cells = 24;
  assert.throws(() => evaluate(mars, moon), /inconsistent/);
});
test('source latitude and longitude registration must agree', () => {
  const {mars, moon} = fixture();
  moon.windows[0].latitude_deg_requested = -1;
  assert.throws(() => evaluate(mars, moon), /mismatch/);
});
test('source PDS geometry and fingerprints are mandatory', () => {
  const {mars, moon} = fixture();
  mars.metadata.megc.ppd = 16;
  assert.throws(() => evaluate(mars, moon), /geometry/);
  mars.metadata.megc.ppd = 128;
  delete moon.source_labels_sha256.count;
  assert.throws(() => evaluate(mars, moon), /fingerprint/);
});
test('invalid mask character and wrong central count fail closed', () => {
  const {mars, moon} = fixture();
  moon.windows[2].observed_mask_rows = [...ones.slice(0, 8), '11111X111'];
  assert.throws(() => evaluate(mars, moon), /mask/);
  moon.windows[2].observed_mask_rows = ones;
  mars.windows[2].center_5x5_observed_cells = 24;
  assert.throws(() => evaluate(mars, moon), /center count/);
});
