import test from 'node:test';
import assert from 'node:assert/strict';
import {validateLabel,checkRange,decodeWindow} from './e469_lola128_bounded.mjs';
const COLS=46080;
function label(stem,type='MSB_INTEGER'){
 return ['PRODUCT_ID = "'+stem+'"','LINES = 23040','LINE_SAMPLES = 46080','SAMPLE_BITS = 16','RECORD_BYTES = 92160','MAP_RESOLUTION = 128.0 <PIXEL/DEGREE>','SAMPLE_TYPE = '+type].join('\n');
}
test('valid PDS labels admitted for count and elevation',()=>{assert.equal(validateLabel(label('LDEC_128'),'count').cols,46080);assert.equal(validateLabel(label('LDEM_128'),'elevation').ppd,128);});
test('wrong instrument product is rejected',()=>assert.throws(()=>validateLabel(label('LDEM_128'),'count')));
test('PDS little-endian integer labels are admitted',()=>{assert.equal(validateLabel(label('LDEC_128','LSB_INTEGER'),'count').sample_type,'LSB_INTEGER');});
test('wrong type and geometry are rejected',()=>{assert.throws(()=>validateLabel(label('LDEC_128','PC_REAL'),'count'));assert.throws(()=>validateLabel(label('LDEC_128').replace('23040','23039'),'count'));});
test('HTTP range must match exact byte offsets and total',()=>{const full=23040*46080*2;checkRange('bytes 100-199/'+full,100,100);assert.throws(()=>checkRange('bytes 100-200/'+full,100,100));assert.throws(()=>checkRange('bytes 100-199/99',100,100));});
test('count zero and big-endian elevation decoding',()=>{const c=Buffer.alloc(3*COLS*2),e=Buffer.alloc(3*COLS*2);for(let r=0;r<3;r++)for(let k=0;k<3;k++){let i=r*COLS+100+k;c.writeUInt16BE(r===1&&k===1?0:2,i*2);e.writeInt16BE(-100+r*10+k,i*2);}assert.equal(decodeWindow(c,101,3).filter(x=>x===0).length,1);assert.deepEqual(decodeWindow(e,101,3,true).slice(0,3),[-100,-99,-98]);});
test('little-endian count and signed elevation decoding',()=>{const c=Buffer.alloc(3*COLS*2),e=Buffer.alloc(3*COLS*2);for(let r=0;r<3;r++)for(let k=0;k<3;k++){let i=r*COLS+100+k;c.writeInt16LE(r===1&&k===1?0:513,i*2);e.writeInt16LE(-100+r*10+k,i*2);}assert.equal(decodeWindow(c,101,3,true,true).filter(x=>x===0).length,1);assert.equal(decodeWindow(c,101,3,true,true)[0],513);assert.deepEqual(decodeWindow(e,101,3,true,true).slice(0,3),[-100,-99,-98]);});
test('truncation and edge windows rejected',()=>{assert.throws(()=>decodeWindow(Buffer.alloc(3*COLS*2-1),101,3));assert.throws(()=>decodeWindow(Buffer.alloc(3*COLS*2),0,3));});
