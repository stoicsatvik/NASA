import test from 'node:test';
import assert from 'node:assert/strict';
import { parseLabel, parseContentRange, windowSamples } from './e463_mola128_range_coverage.mjs';

function label(kind) {
  return [
    'RECORD_BYTES = ' + (kind === 'megc' ? 11520 : 23040),
    'LINES = 5632', 'LINE_SAMPLES = 11520',
    'SAMPLE_TYPE = ' + (kind === 'megc' ? 'UNSIGNED_INTEGER' : 'MSB_INTEGER'),
    'SAMPLE_BITS = ' + (kind === 'megc' ? 8 : 16),
    'MAP_RESOLUTION = 128.0 <PIXEL/DEGREE>',
    'PRODUCT_VERSION_ID = "2.0"',
  ].join('\n');
}
test('count and topography labels match PDS byte geometry', () => {
  assert.equal(parseLabel(label('megc'), 'megc').record_bytes, 11520);
  assert.equal(parseLabel(label('megt'), 'megt').sample_bits, 16);
});
test('wrong instrument sample type fails closed', () => {
  assert.throws(() => parseLabel(label('megc').replace('UNSIGNED_INTEGER', 'MSB_INTEGER'), 'megc'));
});
test('mismatched PDS product version fails closed', () => {
  assert.throws(() => parseLabel(label('megt').replace('"2.0"', '"1.0"'), 'megt'));
});
test('range response must be exact 206 payload location', () => {
  assert.equal(parseContentRange('bytes 100-199/1000', 100, 100, 1000), true);
  assert.throws(() => parseContentRange('bytes 100-200/1000', 100, 100, 1000));
  assert.throws(() => parseContentRange('bytes 100-199/999', 100, 100, 1000));
});
test('count zero is retained and big-endian signed topography is decoded', () => {
  const c = Buffer.alloc(3 * 11520), t = Buffer.alloc(3 * 23040);
  for (let r = 0; r < 3; r++) for (let x = 0; x < 3; x++) {
    const idx = r * 11520 + 100 + x;
    c[idx] = r === 1 && x === 1 ? 0 : 2;
    t.writeInt16BE(-200 + 10 * r + x, 2 * idx);
  }
  const v = windowSamples(c, t, 101, 3);
  assert.equal(v.counts.length, 9);
  assert.equal(v.counts.filter(x => x === 0).length, 1);
  assert.deepEqual(v.elevations.slice(0, 3), [-200, -199, -198]);
});
test('truncated rows and invalid columns fail closed', () => {
  assert.throws(() => windowSamples(Buffer.alloc(3 * 11520 - 1), Buffer.alloc(3 * 23040), 101, 3));
  assert.throws(() => windowSamples(Buffer.alloc(3 * 11520), Buffer.alloc(3 * 23040), 0, 3));
});
