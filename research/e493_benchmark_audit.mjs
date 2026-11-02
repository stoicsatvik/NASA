/** E493: audit benchmark design, not model quality or AUC. No upstream data redistribution. */
import {readFile} from "node:fs/promises";
import {createHash} from "node:crypto";
import assert from "node:assert/strict";
export function audit(catalog, targets) {
const sites = catalog.sites || [];
const negatives = catalog.negatives || [];
const env = sites.filter(s => s.kind === "environment");
const geology = sites.filter(s => s.kind === "geology");
const moon = env.filter(s => s.bodies?.includes("moon"));
const mars = env.filter(s => s.bodies?.includes("mars"));
const profiles = targets.targets || [];
const proxyCounts = profiles.map(t => Object.values(t.criteria || {}).filter(c => Object.hasOwn(c, "earth_percentile")).length);
return {
  sites: sites.length, environmental: env.length, geology: geology.length,
  negatives: negatives.length,
  humid_or_vegetated_negatives: negatives.filter(n => n.reason === "dense vegetation or humid climate").length,
  negative_reason_categories: [...new Set(negatives.map(n => n.reason))],
  moon_positives: moon.length, mars_positives: mars.length,
  moon_pairwise_comparisons: moon.length * negatives.length,
  mars_pairwise_comparisons: mars.length * negatives.length,
  target_profiles: profiles.length,
  targets_with_editorial_proxy: proxyCounts.filter(n => n > 0).length,
  total_editorial_proxy_criteria: proxyCounts.reduce((a,b)=>a+b,0)
};
}
function gitBlobSha(raw) { return createHash("sha1").update(Buffer.from("blob "+raw.length+"\\0")).update(raw).digest("hex"); }
const [catalogPath, targetPath] = process.argv.slice(2);
if (catalogPath && targetPath) {
 const [c,t] = await Promise.all([readFile(catalogPath),readFile(targetPath)]);
 assert.equal(gitBlobSha(c),"d75240ce203ddb00b2d9186e7981ab90720ff9a3");
 assert.equal(gitBlobSha(t),"ed326364e2ba4bad3e05a0bb48d06c23d7c87d4c");
 const result=audit(JSON.parse(c.toString("utf8")),JSON.parse(t.toString("utf8")));
 const expected={"sites":12,"environmental":8,"geology":4,"negatives":8,"humid_or_vegetated_negatives":8,"moon_positives":3,"mars_positives":5,"moon_pairwise_comparisons":24,"mars_pairwise_comparisons":40,"target_profiles":5,"targets_with_editorial_proxy":5,"total_editorial_proxy_criteria":10};
 for (const [key,value] of Object.entries(expected)) assert.equal(result[key],value,key);
 console.log(JSON.stringify(result,null,2));
} else if (process.argv[1]?.endsWith("e493_benchmark_audit.mjs")) {
 throw new Error("usage: node research/e493_benchmark_audit.mjs known_analogs.json targets.json");
}
