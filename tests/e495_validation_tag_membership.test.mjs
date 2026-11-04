import test from 'node:test';
import assert from 'node:assert/strict';
import {audit, effectiveControls} from '../research/e493_benchmark_audit.mjs';

const catalog = {
  sites: [
    {name:'Moon barren',kind:'environment',bodies:['moon'],tags:[]},
    {name:'Mars polar',kind:'environment',bodies:['mars'],tags:['cold_polar']},
    {name:'Moon polar geology',kind:'geology',bodies:['moon'],tags:['cold_polar']},
    {name:'Moon other',kind:'environment',bodies:['moon'],tags:['other']},
    {name:'Mars ordinary',kind:'environment',bodies:['mars'],tags:[]}
  ],
  negatives: [{reason:'dense vegetation or humid climate'}, {reason:'arid hard negative'}]
};
const targets = {targets:[
  {id:'default_moon',body:'Moon'},
  {id:'tagged_moon',body:'Moon',validation_tag:'cold_polar'},
  {id:'missing_tag',body:'Moon',validation_tag:'nonexistent'},
  {id:'default_mars',body:'Mars'}
]};
const byId = Object.fromEntries(effectiveControls(catalog, targets).map(x => [x.target_id,x]));

test('ordinary Moon target selects same-body environment controls only',()=>{
  assert.deepEqual(byId.default_moon.positive_site_names,['Moon barren','Moon other']);
  assert.equal(byId.default_moon.cross_body_positive_count,0);
  assert.equal(byId.default_moon.possible_pairwise_comparisons,4);
});
test('validation_tag overrides body and selects cross-body positives',()=>{
  assert.deepEqual(byId.tagged_moon.positive_site_names,['Mars polar']);
  assert.deepEqual(byId.tagged_moon.cross_body_positive_names,['Mars polar']);
  assert.equal(byId.tagged_moon.cross_body_positive_count,1);
  assert.equal(byId.tagged_moon.possible_pairwise_comparisons,2);
});
test('tagged geology is not an environmental positive',()=>{
  assert.ok(!byId.tagged_moon.positive_site_names.includes('Moon polar geology'));
});
test('unknown tag does not silently fall back to body controls',()=>{
  assert.equal(byId.missing_tag.positive_count,0);
  assert.equal(byId.missing_tag.possible_pairwise_comparisons,0);
});
test('Mars default membership remains body-scoped',()=>{
  assert.deepEqual(byId.default_mars.positive_site_names,['Mars polar','Mars ordinary']);
});
test('aggregate audit reports cross-body assignments without claiming model AUC',()=>{
  const result=audit(catalog,targets);
  assert.equal(result.targets_with_cross_body_positives,1);
  assert.equal(result.cross_body_positive_assignments,1);
  assert.equal(result.moon_positives,2);
  assert.equal(result.mars_positives,2);
  assert.equal(Object.hasOwn(result,'auc'),false);
});
test('editorial proxy fields do not alter control membership',()=>{
  const changed={targets:targets.targets.map(t=>({...t,criteria:{slope:{earth_percentile:95}}}))};
  assert.deepEqual(effectiveControls(catalog,changed),effectiveControls(catalog,targets));
});
