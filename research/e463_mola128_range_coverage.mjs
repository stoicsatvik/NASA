/** E463: bounded, read-only 128-ppd MOLA count/topography sample.
 * Actual coverage is determined by count>0, not by nominal pixel spacing.
 * No analog labels or Earth/Moon matching. No complete source file downloaded.
 */
import { createHash } from 'node:crypto';
import { pathToFileURL } from 'node:url';
import { resolve } from 'node:path';

const BASE = 'https://pds-geosciences.wustl.edu/mgs/urn-nasa-pds-mgs_mola_topography_derived/meg128/';
const STEM = '00n000hb';
const LINES = 5632;
const COLS = 11520;
const PPD = 128;
const WIDTH = 9;
const CENTERS = [-0.5, -20, -40];
const LON = 45;

export function parseLabel(source, kind) {
  const get = (name) => {
    const match = source.match(new RegExp('^\\s*' + name + '\\s*=\\s*([^\\r\\n]+)', 'm'));
    if (!match) throw new Error('Missing label key ' + name);
    return match[1].trim();
  };
  const record = Number(get('RECORD_BYTES'));
  const lines = Number(get('LINES'));
  const cols = Number(get('LINE_SAMPLES'));
  const bits = Number(get('SAMPLE_BITS'));
  const sampleType = get('SAMPLE_TYPE');
  const ppd = Number(get('MAP_RESOLUTION').split(/\s+/)[0]);
  const expected = kind === 'megc' ? [11520, 8, 'UNSIGNED_INTEGER'] : [23040, 16, 'MSB_INTEGER'];
  if (lines !== LINES || cols !== COLS || ppd !== PPD ||
      record !== expected[0] || bits !== expected[1] || sampleType !== expected[2] ||
      get('PRODUCT_VERSION_ID').replace(/"/g, '') !== '2.0') {
    throw new Error('MOLA PDS label geometry/type/version mismatch');
  }
  return { lines, cols, ppd, record_bytes: record, sample_bits: bits, sample_type: sampleType };
}

export function parseContentRange(header, start, length, total) {
  const m = /^bytes (\d+)-(\d+)\/(\d+)$/.exec(header || '');
  if (!m || Number(m[1]) !== start || Number(m[2]) !== start + length - 1 ||
      Number(m[3]) !== total) throw new Error('HTTP Content-Range mismatch');
  return true;
}

export function windowSamples(countRows, topoRows, centerColumn, width = WIDTH) {
  if (width < 1 || width % 2 !== 1 || !Number.isInteger(width) ||
      countRows.length !== width * COLS || topoRows.length !== width * COLS * 2) {
    throw new Error('Window byte geometry mismatch');
  }
  const startColumn = centerColumn - Math.floor(width / 2);
  if (!Number.isInteger(centerColumn) || startColumn < 0 || startColumn + width > COLS) {
    throw new Error('Window outside tile');
  }
  const counts = [], elevations = [];
  for (let r = 0; r < width; r++) for (let c = 0; c < width; c++) {
    const idx = r * COLS + startColumn + c;
    counts.push(countRows[idx]);
    elevations.push(topoRows.readInt16BE(2 * idx));
  }
  return { counts, elevations };
}

function digest(buffer) { return createHash('sha256').update(buffer).digest('hex'); }
async function textGet(url) {
  const r = await fetch(url, { signal: AbortSignal.timeout(30000) });
  if (r.status !== 200) throw new Error('Label HTTP status ' + r.status);
  const body = await r.text();
  if (body.length > 20000) throw new Error('Oversized label');
  return body;
}
async function rangeGet(url, start, length, total) {
  const r = await fetch(url, {
    headers: { Range: 'bytes=' + start + '-' + (start + length - 1), 'Accept-Encoding': 'identity' },
    signal: AbortSignal.timeout(60000),
  });
  if (r.status !== 206) throw new Error('HTTP range request refused, status ' + r.status);
  parseContentRange(r.headers.get('content-range'), start, length, total);
  const bytes = Buffer.from(await r.arrayBuffer());
  if (bytes.length !== length) throw new Error('Truncated range response');
  return bytes;
}

export async function main() {
  const meta = {};
  const labelHashes = {};
  for (const kind of ['megc', 'megt']) {
    const label = await textGet(BASE + kind + STEM + '.lbl');
    meta[kind] = parseLabel(label, kind);
    labelHashes[kind] = digest(Buffer.from(label, 'utf8'));
  }
  const windows = [];
  for (const latitude of CENTERS) {
    const centerRow = Math.floor(-latitude * PPD);
    const startRow = centerRow - Math.floor(WIDTH / 2);
    const centerColumn = Math.floor(LON * PPD);
    if (startRow < 0 || startRow + WIDTH > LINES) throw new Error('Invalid latitude window');
    const cStart = startRow * meta.megc.record_bytes;
    const tStart = startRow * meta.megt.record_bytes;
    const cLength = WIDTH * meta.megc.record_bytes;
    const tLength = WIDTH * meta.megt.record_bytes;
    const [cRows, tRows] = await Promise.all([
      rangeGet(BASE + 'megc' + STEM + '.img', cStart, cLength, LINES * COLS),
      rangeGet(BASE + 'megt' + STEM + '.img', tStart, tLength, LINES * COLS * 2),
    ]);
    const { counts, elevations } = windowSamples(cRows, tRows, centerColumn);
    const measured = counts.map((x) => x > 0);
    const measuredElevation = elevations.filter((_, i) => measured[i]);
    windows.push({
      latitude_deg_requested: latitude, longitude_deg_requested: LON,
      center_row_zero_based: centerRow, center_column_zero_based: centerColumn,
      sampled_cells: counts.length,
      measured_cells: measured.filter(Boolean).length,
      interpolated_cells: measured.filter((x) => !x).length,
      measured_fraction: measured.filter(Boolean).length / counts.length,
      count_min: Math.min(...counts), count_max: Math.max(...counts),
      measured_elevation_min_m: measuredElevation.length ? Math.min(...measuredElevation) : null,
      measured_elevation_max_m: measuredElevation.length ? Math.max(...measuredElevation) : null,
      sampled_count_range_sha256: digest(cRows), sampled_topo_range_sha256: digest(tRows),
      sampled_count_byte_range: [cStart, cStart + cLength - 1],
      sampled_topo_byte_range: [tStart, tStart + tLength - 1],
    });
  }
  const receipt = {
    schema: 'nasa/e463/mola128-bounded-real-data-coverage/v1',
    source_base: BASE, tile: STEM,
    pds_product_version: '2.0', sampling: 'three preregistered 9x9 windows, not a random global sample',
    pds3_labels_sha256: labelHashes, metadata: meta,
    topography_units: 'metres above MOLA areoid',
    counts_units: 'number of MOLA observations per grid cell; zero implies interpolated topography',
    full_file_sha256: null, full_file_downloaded: false,
    windows,
    claim: 'ONLY site-specific MOLA 128ppd observation coverage at three selected windows; no independent effective resolution',
    known_site_recovery: 'NOT YET MEASURED',
    cross_body_similarity: 'NOT YET PROVEN',
    limitations: [
      'Samples are not geological analogues and were chosen before observing the raster bytes.',
      'Counts>0 establishes an observed bin, not independent sample geometry, measurement uncertainty or optical resolution.',
      'The sampled byte-range hashes are not full-file hashes; full product checksums were not verified.',
      'No LOLA high-resolution sample, Earth matched descriptor, independent label, or E001 retrieval.',
      'No raw data are committed to GitHub.'
    ],
  };
  console.log(JSON.stringify(receipt, null, 2));
}
if (process.argv[1] && import.meta.url === pathToFileURL(resolve(process.argv[1])).href) {
  main().catch((err) => { console.error(err.stack || String(err)); process.exitCode = 1; });
}
