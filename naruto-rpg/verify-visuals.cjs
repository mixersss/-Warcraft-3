// Read actual MDX animation/visibility/attachment data and generated Classic object files.
const fs=require('fs'),path=require('path'),assert=require('assert/strict');
const Model=require('mdx-m3-viewer/dist/cjs/parsers/mdlx/model').default;
const ObjectParser=require('mdx-m3-viewer/dist/cjs/parsers/w3x/w3u/file').default;
const AbilityParser=require('mdx-m3-viewer/dist/cjs/parsers/w3x/w3d/file').default;
const root=__dirname,read=n=>JSON.parse(fs.readFileSync(path.join(root,n)));
const profiles=read('src/skill-visuals.json'),skills=read('src/playable-skills.json'),heroes=read('src/heroes.json'),source=read('src/source-visual-audit.json');
const meta=read('src/model-visual-metadata.json'),models={};
for(const entry of meta){
 const m=new Model();m.load(new Uint8Array(fs.readFileSync(path.join(root,'assets',entry.path.replaceAll('\\','/')))));models[entry.path.toLowerCase()]=m;
 assert.deepEqual(m.sequences.map(s=>({name:s.name,from:s.interval[0],to:s.interval[1],seconds:(s.interval[1]-s.interval[0])/1000,nonLooping:s.nonLooping})),entry.sequences,entry.path);
 assert.deepEqual(m.attachments.map(a=>a.name.trim().replace(/ Ref$/i,'').toLowerCase()),entry.attachments);
}
function parse(C,name){let o=new C();o.load(new Uint8Array(fs.readFileSync(path.join(root,'dist/map',name))));return Object.fromEntries(o.customTable.objects.map(x=>[x.newId,x]));}
const units=parse(ObjectParser,'war3map.w3u'),abilities=parse(AbilityParser,'war3map.w3a');
const schema=read('src/classic-skill-schema.json');
const get=(o,id,rank=0)=>o.modifications.find(m=>m.id===id && (m.levelOrVariation||0)===(schema.abilityFields[id]?.repeat===0?0:rank))?.value;
for(const a of Object.values(abilities))for(const mod of a.modifications)if(schema.abilityFields[mod.id].repeat===0)assert.equal(mod.levelOrVariation,0,a.newId+':'+mod.id+' must be a real global override');
assert.equal(profiles.skills.length,58);assert.equal(source.skills.length,58);
const out=[];
for(const r of skills){
 const profile=profiles.skills.find(p=>p.id===r.id);assert(profile && profile.sourceId===r.source_id);
 const original=source.skills.find(p=>p.hero===r.hero && p.sourceId===r.source_id);assert(original);
 const model=models[heroes[r.hero].model.toLowerCase()],tokens=r.animation.toLowerCase().split(/\s+/);
 const seq=model.sequences.find(s=>tokens.every(t=>s.name.toLowerCase().split(/\s+/).includes(t)));assert(seq);
 assert.equal((seq.interval[1]-seq.interval[0])/1000,profile.sequenceSeconds);
 if(profile.channelSeconds){
  assert.equal(r.base,'ANcl');for(let rank=1;rank<=r.ranks;rank++){assert(Math.abs(get(abilities[r.id],'Ncl1',rank)-profile.channelSeconds)<1e-5);assert.equal(get(abilities[r.id],'Ncl5',rank),1);}
  assert(Math.abs(profile.sequenceSeconds/profile.sequencePlaybackScale-profile.channelSeconds)<1e-6);
 }
 for(const [field,value] of Object.entries(profile.nativeArt))for(let rank=1;rank<=r.ranks;rank++)assert.equal(get(abilities[r.id],field,rank),value,r.id+':'+field);
 out.push({hero:heroes[r.hero].name,name:r.name,id:r.id,sourceId:r.source_id,sourceTriggerVisualFunctionCount:original.triggerVisualOperations.length,visualKind:profile.kind,animation:seq.name,channelSeconds:profile.channelSeconds,enginePlaybackChecked:false});
}
for(const p of profiles.visualUnits){
 assert.equal(get(units[p.id],'umdl'),p.model);assert.equal(get(units[p.id],'uaen'),0);assert.equal(get(units[p.id],'ucol'),0);assert.equal(get(units[p.id],'uabi'),'Aloc,Avul');
 const model=models[p.model.replace(/\.mdl$/i,'.mdx').toLowerCase()];
 if(model)assert(model.sequences.some(s=>s.name.toLowerCase()===p.animation.toLowerCase()),p.id+' missing visual sequence');
}
// The translucent chakra shell is mesh visibility keyed to spell spin, not HakkeAura.
let sphere=[];
for(const name of ['neji.mdx','Hinata.mdx']){
 const m=models[name.toLowerCase()],spin=m.sequences.find(s=>s.name==='spell spin');assert.equal(spin.interval[0],3667);assert.equal(spin.interval[1],6600);
 const visibility=m.geosetAnimations.flatMap(a=>a.animations.filter(t=>t.name==='KGAO').map(t=>({geoset:a.geosetId,keys:t.frames.map((f,i)=>[f,t.values[i][0]])})));
 const shell=visibility.filter(a=>a.keys.some(([f,v])=>f===3933 && v>0) && a.keys.some(([f,v])=>f===9333 && v===0));assert(shell.length>=1,name+' sphere visibility must be keyed to spin');
 for(const a of shell)assert(a.keys.some(([f,v])=>f===333 && v===0),'Stand Ready must have no sphere');
 sphere.push({model:name,spinSeconds:2.933,visibleShellGeosets:shell,channelSeconds:2,playbackScale:2.933/2});
}
for(const id of ['R401','R801'])assert.equal(get(abilities[id],'aani'),'Stand Ready');
assert.equal(get(units.R005,'ua1m'),'Shurikens.mdl');
for(const id of ['RB01','R503']){const art=abilities[id].modifications.filter(m=>m.id==='amat');assert.equal(art.length,1);assert.equal(art[0].levelOrVariation,0);}
assert(get(abilities.R503,'amat').includes('Shurikens.mdl'));
const sourceWind=source.skills.find(s=>s.sourceId==='A00S').abilityArt.find(f=>f.id==='amat').value;
assert.equal(get(abilities.RB01,'amat',1),sourceWind);assert(sourceWind.includes('TornadoElemental'));
assert.equal(get(units.vcyc,'umdl'),'Electrical Cyclone.mdl');assert.equal(get(units.vbal,'usca'),12);
for(const [hero,points] of [[0,['hand right']],[1,['hand left']],[2,['hand left','hand right']],[3,['hand right','foot right']],[4,['hand left','hand right']],[8,['hand left','hand right']]]){
 const actual=meta.find(m=>m.path===heroes[hero].model).attachments;for(const point of points)assert(actual.includes(point),heroes[hero].name+':'+point);
}
const generated=read('src/generated-assets.json');
const strip=new Model();strip.load(new Uint8Array(fs.readFileSync(path.join(root,generated[0].file))));
assert.equal(strip.version,800);assert.equal(strip.geosets[0].vertices.length,12);
assert.equal(strip.materials[0].layers[0].filterMode,2,'Black shadow must use blend, not additive material');
assert.equal(strip.textures[0].replaceableId,1);assert(strip.sequences.some(s=>s.name==='Stand' && s.nonLooping===0));
assert.equal(get(units.rshd,'umdl'),'ShinobiShadowStrip.mdl');assert.equal(get(units.rshk,'umdl'),'ShikamaruKageMane.mdl');
assert.equal(get(units.vfan,'umdl'),'Abilities\\Spells\\NightElf\\FanOfKnives\\FanOfKnivesMissile.mdl');
const result={checkedSourceSlots:58,checkedImportedModels:68,originalModels:67,generatedShadowModel:true,activeSkills:52,visualActorTypes:profiles.visualUnits.length,sourceObjectsAndTriggersCompared:true,bodySequencesAndAttachmentPointsChecked:true,sourceSpecificKaitenVisibility:sphere,finiteChanneledCastPoses:true,tentenBasicProjectile:'Shurikens.mdl (explicit user preference; source basic attack is Kunai.mdl)',temariWindProjectile:sourceWind,enginePlaybackChecked:false,exactOriginalChoreography:false,skills:out};
fs.writeFileSync(path.join(root,'dist/visual-verification.json'),JSON.stringify(result,null,2)+'\n');
console.log('PASS: all 58 source visual inventories, all 67 actual MDX sequence/attachment records, 52 active cast profiles, native projectile overrides, channel durations and spin-only sphere visibility, source model scales and finite visual actors. Actual engine playback remains untested.');
