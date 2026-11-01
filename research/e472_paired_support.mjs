/** E472: compare measured-bin support at approximately matched 2 km physical footprints.
 * Reanalyses E463/E469 real PDS bounded source receipts. No analogue retrieval.
 */
import { readFileSync } from 'node:fs';
import { pathToFileURL } from 'node:url';
import { resolve } from 'node:path';

const MOON4_KM = 7.58083760603737; // E212 source-fingerprinted receipt, 4 pixels/degree
const MARS4_KM = 14.78948374908695; // E212 source-fingerprinted receipt, 4 pixels/degree
const PPD_RATIO = 128 / 4;

export function validateMask(rows, claimed, width = 9) {
  if (!Array.isArray(rows) || rows.length !== width ||
      rows.some(row => typeof row !== 'string' || !new RegExp('^[01]{' + width + '}$').test(row))) {
    throw Error('Missing or malformed observation mask');
  }
  const count = rows.join('').split('').filter(x => x === '1').length;
  if (!Number.isInteger(claimed) || claimed !== count) throw Error('Observed count inconsistent with mask');
  return count;
}
export function centerCount(rows, width = 5) {
  if (!Array.isArray(rows) || rows.length !== 9 || width !== 5) throw Error('Invalid center support');
  validateMask(rows, rows.join('').split('').filter(x => x === '1').length);
  return rows.slice(2, 7).reduce((n, row) =>
    n + row.slice(2, 7).split('').filter(x => x === '1').length, 0);
}
export function evaluate(mars, moon) {
  if (mars?.schema !== 'nasa/e463/mola128-bounded-real-data-coverage/v1' ||
      moon?.schema !== 'nasa/e469/lola128-bounded-count-coverage/v1') throw Error('Unexpected real-source receipts');
  if (mars.metadata?.megc?.ppd !== 128 || moon.metadata?.count?.ppd !== 128 ||
      mars.metadata.megc.sample_bits !== 8 || moon.metadata.count.bits !== 16) throw Error('Incompatible PDS geometry');
  if (!mars.pds3_labels_sha256?.megc || !moon.source_labels_sha256?.count) throw Error('Missing source fingerprints');
  if (mars.windows?.length !== 3 || moon.windows?.length !== 3) throw Error('Expected three frozen windows');
  const moonPixelKm = MOON4_KM / PPD_RATIO, marsPixelKm = MARS4_KM / PPD_RATIO;
  const moonSpanKm = 8 * moonPixelKm, marsSpanKm = 4 * marsPixelKm;
  const windows = mars.windows.map((m, i) => {
    const l = moon.windows[i];
    if (!l || m.latitude_deg_requested !== l.latitude_deg_requested ||
        m.longitude_deg_requested !== l.longitude_deg_requested ||
        m.sampled_cells !== 81 || l.sampled_cells !== 81 ||
        !m.sampled_count_range_sha256 || !l.count_range_sha256) throw Error('Source-window mismatch');
    validateMask(m.observed_mask_rows, m.measured_cells);
    validateMask(l.observed_mask_rows, l.observed_cells);
    const observedMars = centerCount(m.observed_mask_rows);
    if (m.center_5x5_observed_cells !== observedMars) throw Error('Mars center count inconsistent');
    return {
      latitude_deg_requested: m.latitude_deg_requested,
      longitude_deg_requested: m.longitude_deg_requested,
      moon_9x9_observed: l.observed_cells,
      moon_9x9_total: 81,
      mars_5x5_observed: observedMars,
      mars_5x5_total: 25,
      moon_observed_fraction: l.observed_cells / 81,
      mars_observed_fraction: observedMars / 25,
      mars_full_9x9_observed: m.measured_cells,
      moon_count_range_sha256: l.count_range_sha256,
      mars_count_range_sha256: m.sampled_count_range_sha256,
    };
  });
  return {
    schema: 'nasa/e472/physical-support-count-mask-comparison/v1',
    source_experiments: ['E212', 'E463', 'E469'],
    physical_support: {
      moon_9x9_span_north_south_km: moonSpanKm,
      mars_5x5_span_north_south_km: marsSpanKm,
      relative_span_difference: Math.abs(moonSpanKm - marsSpanKm) / ((moonSpanKm + marsSpanKm) / 2),
      latitude_east_west_shrinkage: 'both scale with cos(latitude); longitudinal footprint remains approximate',
      independent_effective_resolution: 'NOT MEASURED',
    },
    windows,
    claim: 'Observed-bin support for three nonrandom approximately matched physical footprints only',
    known_site_recovery: 'NOT YET MEASURED',
    cross_body_similarity: 'NOT YET PROVEN',
    limitations: [
      'No known analogue labels or Earth-matched 2 km descriptor extraction',
      'A positive observation count is not an independent effective-resolution guarantee',
      'Approximate spherical footprint, not point-spread/track-spacing matched',
      'Source 9x9 byte-range hashes are not full-product hashes',
      'The three selected positions are not representative of either planetary surface',
    ],
  };
}
if (process.argv[1] && import.meta.url === pathToFileURL(resolve(process.argv[1])).href) {
  if (process.argv.length !== 4) throw Error('Usage: node e472_paired_support.mjs <E463.json> <E469.json>');
  const result = evaluate(JSON.parse(readFileSync(process.argv[2], 'utf8')),
                          JSON.parse(readFileSync(process.argv[3], 'utf8')));
  console.log(JSON.stringify(result, null, 2));
}
