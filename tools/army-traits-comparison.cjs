// Historical checks admit only the explicitly audited 0.20 troop/mode changes.
// verify-020 independently compares every new field against the real 0.19 archive.
const fs=require('node:fs'),path=require('node:path');
const MapFile=require('mdx-m3-viewer/dist/cjs/parsers/w3x/map').default;
const old=new MapFile();old.load(new Uint8Array(fs.readFileSync(path.join(__dirname,'../releases/FourFrontsFrenzy-0.19.0-alpha.w3x'))),true);
const U=require('mdx-m3-viewer/dist/cjs/parsers/w3x/w3u/file').default;
const units=new U();units.load(new Uint8Array(old.get('war3map.w3u').bytes()));
const troops=new Map(units.customTable.objects.filter(o=>/^fm[0-3][1-4]$/.test(o.newId)).map(o=>[o.newId,o]));
function clone(o){if(Array.isArray(o))return o.map(clone);if(o&&typeof o==='object')return Object.assign(Object.create(Object.getPrototypeOf(o)),Object.fromEntries(Object.entries(o).map(([k,v])=>[k,clone(v)])));return o;}
function objects(p){
 require('./army-orders-comparison.cjs').objects(p);
 require('./treant-comparison.cjs').objects(p);
 for(const t of ['originalTable','customTable'])p[t].objects=p[t].objects.filter(o=>!/^Jt[a-z]{2}$/.test(o.newId)).map(o=>troops.has(o.newId)?clone(troops.get(o.newId)):o);
 return p;
}
const functions=['OnChat','ShowModes','SpawnWave','CommandArmy'];
function runtime(s,previous){
 s=require('./army-orders-comparison.cjs').runtime(s,previous);
 s=require('./treant-comparison.cjs').runtime(s);
 for(const name of functions){const re=new RegExp('function '+name+' takes[\\s\\S]*?endfunction');const before=previous.match(re);if(before)s=s.replace(re,()=>before[0]);}
 for(const name of ['RandomBotArmyBranch','ArmyTraitCast'])s=s.replace(new RegExp('function '+name+' takes[\\s\\S]*?endfunction\\s*'),'');
 return s.replaceAll('Waves: six plus','Waves: four plus').replaceAll('Six plus wave-size research troops per wave','Four plus wave-size research troops per wave');
}
module.exports={objects,runtime,functions};
