const fs=require('node:fs'),path=require('node:path'),assert=require('node:assert/strict');
const root=path.resolve(__dirname,'..'),b=require('../map/balance.json');
const M=require('mdx-m3-viewer/dist/cjs/parsers/w3x/map').default,A=require('mdx-m3-viewer/dist/cjs/parsers/w3x/w3d/file').default;
const old=new M();old.load(new Uint8Array(fs.readFileSync(path.join(root,'releases/FourFrontsFrenzy-0.20.1-alpha.w3x'))),true);
const now=n=>fs.readFileSync(path.join(root,'build/map',n)),before=n=>Buffer.from(old.get(n).bytes()),a=new A(),prior=new A();a.load(new Uint8Array(now('war3map.w3a')));prior.load(new Uint8Array(before('war3map.w3a')));
const get=(o,id,r=0)=>o.modifications.find(m=>m.id===id&&(m.levelOrVariation||0)===r)?.value;
for(let team=0;team<4;team++)for(const prefix of ['Fao','Fac']){
 const s=a.customTable.objects.find(o=>o.newId===prefix+team);assert(s);assert.equal(s.oldId,'ANcl');assert.equal(get(s,'aher'),0);assert.equal(get(s,'alev'),1);assert.equal(get(s,'ahky'),'ZXCV'[team]);
 assert.deepEqual([get(s,'abpx'),get(s,'abpy')],[[1,1],[2,1],[0,2],[1,2]][team]);assert.equal(get(s,'amcs',1),0);assert.equal(get(s,'acdn',1),0);assert.equal(get(s,'Ncl2',1),0);assert.equal(get(s,'Ncl3',1),1);assert.equal(get(s,'Ncl4',1),0);assert.equal(get(s,'Ncl5',1),0);assert.equal(get(s,'Ncl6',1),['berserk','roar','taunt','howlofterror'][team]);
 assert(get(s,'aub1',1).includes('центр'));assert(get(s,'aub1',1).includes('только на вашу армию'));
}
require('./army-orders-comparison.cjs').objects(a);assert.deepEqual(a,prior,'Only eight native order cards added');
for(const n of ['war3map.w3u','war3map.w3q','war3map.w3t','war3map.w3h','war3map.w3b','war3map.wpm','war3map.w3e','war3mapMisc.txt','war3map.doo','war3mapUnits.doo','war3map.imp','war3mapMap.tga','war3mapPreview.tga'])assert.deepEqual(now(n),before(n),n+' unchanged');
const canonical=s=>s.split('\n').map(l=>l.trim()).filter(Boolean).join('\n');
const source=now('war3map.j').toString(),previous=before('war3map.j').toString();
const fn=(s,n)=>s.match(new RegExp('function '+n+' takes[\\s\\S]*?endfunction'))[0];
assert.equal(fn(source,'CommitArmyBranch').replace('    call InstallArmyOrderButtons(p)\n',''),fn(previous,'CommitArmyBranch'));
assert.equal(fn(source,'InitSlot').replace(/^.*set Army(?:Destination|PlanAt|Redirect|WasDefending)\[p\].*\n/gm,''),fn(previous,'InitSlot'));
assert.equal(fn(source,'InitGame').replace(/^.*TriggerAddAction\((?:PickerSpellTrigger, function OnArmyOrderSpell|ShopTrigger,function OnArmyOrderDialog)\).*\n/gm,''),fn(previous,'InitGame'));
assert.equal(fn(source,'OnChat').replace('    elseif command == "-orders" then\n        call ShowArmyOrders(p)\n','').replace('-orders: направление солдат | ',''),fn(previous,'OnChat'));
assert.equal(canonical(require('./army-orders-comparison.cjs').runtime(source,previous).replaceAll(b.version,'0.20.1-alpha')),canonical(previous),'Only explicit army command functions/state change');
assert(source.includes('TriggerAddAction(PickerSpellTrigger, function OnArmyOrderSpell)'));assert(source.includes('TriggerAddAction(ShopTrigger,function OnArmyOrderDialog)'));
for(const name of ['InstallArmyOrderButtons','PlanBotArmyDestination','SetArmyDestination','OnArmyOrderSpell','OnArmyOrderDialog'])assert(!/(?:CreateGroup|CreateTimer|CreateTrigger)\(/.test(source.match(new RegExp('function '+name+' takes[\\s\\S]*?endfunction'))[0]),'No new per-order handles');
fs.writeFileSync(path.join(root,'build/verification-021.json'),JSON.stringify({version:b.version,orderCards:8,visiblePerBarracks:4,perPlayerDestinations:['southwest','southeast','northeast','northwest','center'],ownBaseButton:'hold center',centerWaypointRadius:900,botsPlanSeconds:20,emergencyDefensePreserved:true,everyOther0201ObjectWorldFieldPreserved:true,enginePlaytest:false},null,2)+'\n');
console.log('PASS:eight native direction/center cards,free instant cast/cell safety,existing triggers only; exact0.20.1 scope preserves all prior world/hero/economy/troop data.');
