/** E469: independent bounded LOLA count/elevation source check.
 * A count>0 is observational support, not a guarantee of effective resolution.
 * No analog identification, physical cross-body descriptor or field observation.
 */
import { createHash } from 'node:crypto';
import { pathToFileURL } from 'node:url';
import { resolve } from 'node:path';
const BASE='https://pds-geosciences.wustl.edu/lro/lro-l-lola-3-rdr-v1/lrolol_1xxx/data/lola_gdr/cylindrical/img/';
const ROWS=23040, COLS=46080, PPD=128, WIDTH=9, LON=45;
const LATS=[-0.5,-20,-40];
const FULL=ROWS*COLS*2;
function sha(b){return createHash('sha256').update(b).digest('hex');}
function field(label,key){const m=label.match(new RegExp('^\\s*'+key+'\\s*=\\s*([^\\r\\n]+)','m'));if(!m)throw Error('Missing '+key);return m[1].trim().replace(/^"|"$/g,'');}
export function validateLabel(label,kind){
 const nums=['LINES','LINE_SAMPLES','SAMPLE_BITS','RECORD_BYTES','MAP_RESOLUTION'];
 const [rows,cols,bits,record,ppd]=nums.map(k=>Number(field(label,k).split(/\s+/)[0]));
 const sample=field(label,'SAMPLE_TYPE');
 if(rows!==ROWS||cols!==COLS||bits!==16||record!==COLS*2||ppd!==PPD||!['MSB_INTEGER','MSB_UNSIGNED_INTEGER','LSB_INTEGER','LSB_UNSIGNED_INTEGER'].includes(sample))throw Error('LOLA '+kind+' label geometry/type mismatch: '+JSON.stringify({rows,cols,bits,record,ppd,sample}));
 if(kind==='count' && !/LDEC_128/i.test(label))throw Error('Wrong count product');
 if(kind==='elevation' && !/LDEM_128/i.test(label))throw Error('Wrong elevation product');
 return {rows,cols,bits,record,ppd,sample_type:sample};
}
export function checkRange(header,start,len){
 const m=/^bytes (\d+)-(\d+)\/(\d+)$/.exec(header||'');
 if(!m||Number(m[1])!==start||Number(m[2])!==start+len-1||Number(m[3])!==FULL)throw Error('Content-Range mismatch');
}
export function decodeWindow(buffer,centerColumn,width=WIDTH,signed=false,littleEndian=false){
 if(!Number.isInteger(width)||width<1||width%2!==1||buffer.length!==width*COLS*2)throw Error('Window geometry mismatch');
 const left=centerColumn-Math.floor(width/2);
 if(!Number.isInteger(centerColumn)||left<0||left+width>COLS)throw Error('Window column out of bounds');
 const values=[];
 for(let row=0;row<width;row++)for(let col=0;col<width;col++){
  const byte=2*(row*COLS+left+col);
  values.push(signed?(littleEndian?buffer.readInt16LE(byte):buffer.readInt16BE(byte)):(littleEndian?buffer.readUInt16LE(byte):buffer.readUInt16BE(byte)));
 }
 return values;
}
async function labelGet(url){const r=await fetch(url,{signal:AbortSignal.timeout(30000)});if(r.status!==200)throw Error('Label HTTP '+r.status);const s=await r.text();if(s.length>16000)throw Error('Label oversized');return s;}
async function boundedGet(url,start,len){const r=await fetch(url,{headers:{Range:'bytes='+start+'-'+(start+len-1),'Accept-Encoding':'identity'},signal:AbortSignal.timeout(60000)});if(r.status!==206){await r.body?.cancel();throw Error('Bounded HTTP 206 required, got '+r.status);}checkRange(r.headers.get('content-range'),start,len);const b=Buffer.from(await r.arrayBuffer());if(b.length!==len)throw Error('Truncated range');return b;}
export async function main(){
 const products=[['count','ldec_128'],['elevation','ldem_128']];
 const labels={}, metadata={};
 for(const [kind,stem] of products){const s=await labelGet(BASE+stem+'.lbl');metadata[kind]=validateLabel(s,kind);labels[kind]=sha(Buffer.from(s));}
 const windows=[];
 for(const lat of LATS){
  const row=Math.floor((90-lat)*PPD),col=Math.floor(LON*PPD),startRow=row-Math.floor(WIDTH/2);
  if(startRow<0||startRow+WIDTH>ROWS)throw Error('Invalid latitude');
  const start=startRow*COLS*2,len=WIDTH*COLS*2;
  const [c,t]=await Promise.all([boundedGet(BASE+'ldec_128.img',start,len),boundedGet(BASE+'ldem_128.img',start,len)]);
  const counts=decodeWindow(c,col,WIDTH,metadata.count.sample_type.endsWith('_INTEGER')&&!metadata.count.sample_type.includes('UNSIGNED'),metadata.count.sample_type.startsWith('LSB'));
  const elevations=decodeWindow(t,col,WIDTH,true,metadata.elevation.sample_type.startsWith('LSB'));
  if(counts.some(v=>v<0))throw Error('Negative observation count');
  const observed=counts.filter(v=>v>0).length;
  const observedMask=counts.map(v=>v>0);
  const observedMaskRows=Array.from({length:WIDTH},(_,r)=>observedMask.slice(r*WIDTH,(r+1)*WIDTH).map(v=>v?'1':'0').join(''));
  windows.push({latitude_deg_requested:lat,longitude_deg_requested:LON,row_zero_based:row,col_zero_based:col,sampled_cells:counts.length,observed_cells:observed,zero_count_cells:counts.length-observed,observed_fraction:observed/counts.length,observed_mask_rows:observedMaskRows,counts_min:Math.min(...counts),counts_max:Math.max(...counts),elevation_dn_min:Math.min(...elevations),elevation_dn_max:Math.max(...elevations),count_range_sha256:sha(c),elevation_range_sha256:sha(t),byte_range:[start,start+len-1]});
 }
 const total=windows.reduce((s,w)=>s+w.sampled_cells,0),obs=windows.reduce((s,w)=>s+w.observed_cells,0);
 console.log(JSON.stringify({schema:'nasa/e469/lola128-bounded-count-coverage/v1',source:BASE,source_labels_sha256:labels,metadata,windows,pooled_nonrandom:{observed:obs,total,observed_fraction:obs/total},full_file_downloaded:false,full_file_sha256:null,claims:{lunar_observed_bin_coverage:'MEASURED FOR THESE WINDOWS ONLY',cross_body_similarity:'NOT YET PROVEN',known_site_recovery:'NOT YET MEASURED'},limitations:['Samples at 45E were fixed before viewing bytes, not representative globally','Counts>0 does not prove independent effective resolution','LDEM DN is not directly comparable to MOLA elevation; scale/offset and reference datums differ','No Earth descriptor or independent analogue labels','Byte-range hashes are not whole-product checksums']},null,2));
}
if(process.argv[1]&&import.meta.url===pathToFileURL(resolve(process.argv[1])).href)main().catch(e=>{console.error(e.stack||String(e));process.exitCode=1;});
