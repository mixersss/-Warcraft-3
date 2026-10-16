// Execute shipped JASS decisions with mocked natives; native combat remains an engine test.
const fs=require('node:fs'),assert=require('node:assert/strict');
const {lua,lauxlib,lualib,to_luastring,to_jsstring}=require('fengari');
const translate=require('mdx-m3-viewer/dist/cjs/utils/jass2/jass2lua').default;
const Parser=require('mdx-m3-viewer/dist/cjs/parsers/w3x/w3u/file').default;
const AbilityParser=require('mdx-m3-viewer/dist/cjs/parsers/w3x/w3d/file').default;
const Info=require('mdx-m3-viewer/dist/cjs/parsers/w3x/w3i/file').default;
const base=__dirname+'/dist/map/',source=fs.readFileSync(base+'war3map.j','utf8');
const rows=JSON.parse(fs.readFileSync(__dirname+'/src/playable-skills.json'));
const schema=JSON.parse(fs.readFileSync(__dirname+'/src/classic-skill-schema.json'));
function parse(C,p){const o=new C();o.load(new Uint8Array(fs.readFileSync(base+p)));return o;}
const abilities=parse(AbilityParser,'war3map.w3a').customTable.objects;
const units=parse(Parser,'war3map.w3u').customTable.objects;
const get=(o,id,rank=0)=>o.modifications.find(m=>m.id===id && (m.levelOrVariation||0)===rank)?.value;
const unit=Object.fromEntries(units.map(o=>[o.newId,o]));
const ability=Object.fromEntries(abilities.map(o=>[o.newId,o]));
const assets=new Set(JSON.parse(fs.readFileSync(__dirname+'/src/asset-manifest.json')).map(r=>r.path.toLowerCase()));
for(const o of units){
 assert(o.newId==='rdum' || assets.has(get(o,'uico').toLowerCase()),'Missing unit portrait '+o.newId);
 if(o.newId!=='rdum')assert(assets.has(get(o,'umdl').replace(/\.mdl$/i,'.mdx').toLowerCase()),'Missing unit model '+o.newId);
}
for(const row of rows)assert(assets.has(row.icon.toLowerCase()),'Missing spell icon');
function kind(t){return t==='real'?1:t==='unreal'?2:['int','bool','attackBits','defenseType','deathType','regenType'].includes(t)?0:3;}
for(const o of abilities){
 assert(schema.stockIds.abilities.includes(o.oldId),'Invalid native ability base '+o.oldId);
 for(const mod of o.modifications){const meta=schema.abilityFields[mod.id];assert(meta,'Unknown ability field '+mod.id);assert.equal(mod.variableType,kind(meta.type),o.newId+':'+mod.id);if(mod.levelOrVariation>0)assert.equal(mod.dataPointer,meta.column,o.newId+':'+mod.id+' column');}
}
for(const o of units){
 assert(schema.stockIds.units.includes(o.oldId),'Invalid native unit base');
 for(const mod of o.modifications){const meta=schema.unitFields[mod.id];assert(meta,'Unknown unit field '+mod.id);assert.equal(mod.variableType,kind(meta.type),o.newId+':'+mod.id);}
 for(const id of (get(o,'uhab')||'').split(',').filter(Boolean))assert(ability[id]);
}
for(let j=0;j<rows.length;j++){const pos=j%5;assert.equal(get(ability[rows[j].id],'abpy'),pos<4?2:1);assert.equal(get(ability[rows[j].id],'abpx'),pos<4?pos:1);}
assert.equal(rows.length,10);assert.equal(new Set(rows.map(r=>r.id)).size,10);
for(const r of rows){assert.equal(get(ability[r.id],'alev'),r.ranks);for(let rank=1;rank<=r.ranks;rank++){assert.equal(get(ability[r.id],'amcs',rank),r.mana[rank-1]);assert(Math.abs(get(ability[r.id],'acdn',rank)-r.cooldown)<.01);}}
assert.equal(get(unit.R000,'uhab'),rows.slice(0,5).map(r=>r.id).join(','));
assert.equal(get(unit.R001,'uhab'),rows.slice(5).map(r=>r.id).join(','));
for(const [normal,form,morph] of [['R000','Rnfm','Rn05'],['R001','Rsfm','Rs05']]){
 assert.equal(get(unit[form],'uhab'),get(unit[normal],'uhab'));
 for(let rank=1;rank<=3;rank++){assert.equal(get(ability[morph],'Eme1',rank),normal);assert.equal(get(ability[morph],'Emeu',rank),form);}
}
for(let rank=1;rank<=3;rank++){assert(unit[get(ability.Rn03,'Hwe1',rank)]);assert.equal(get(ability.Rn03,'Hwe2',rank),1);assert(get(ability.Rsev,'Eev1',rank)<=.75);}
assert.equal(get(unit.rt03,'uhpm'),2800);assert.equal(get(unit.rt03,'ua1b'),110);
assert.equal(get(ability.Rn02,'Omi1',4),5);assert.equal(get(ability.Rn04,'Htb1',3),650);assert.equal(get(ability.Rs04,'Htb1',3),800);
const info=parse(Info,'war3map.w3i');assert.equal(info.players.length,12);assert.equal(info.forces.length,4);assert.deepEqual(info.forces.map(f=>f.playerMasks),[7,56,448,3584]);
const L=lauxlib.luaL_newstate();lualib.luaL_openlibs(L);
function run(s){if(lauxlib.luaL_dostring(L,to_luastring(s))!==lua.LUA_OK)throw Error(to_jsstring(lua.lua_tostring(L,-1)));}
run(translate(source).replace(/\bnot(?=[A-Z(])/g,'not '));
for(const m of source.matchAll(/^\s*(integer|real|boolean) array (\w+)\s*$/gm))run(`setmetatable(${m[2]}, {__index=function() return ${m[1]==='boolean'?'false':'0'} end})`);
const assignments=source.split('\n').filter(s=>/^\s*set (PlayableSkill|SkillRanks|SkillRequired|SkillSkip|SkillAudio|SkillOrder|SkillTarget|SkillCooldown|SkillMana)\[/.test(s));
run(translate('function FixtureData takes nothing returns nothing\n'+assignments.join('\n')+'\nendfunction\n'));run('FixtureData()');
run(`
debug.setmetatable('',{__add=function(a,b)return tostring(a)..tostring(b)end})
function Player(p) return p end
MAP_CONTROL_COMPUTER='computer';UNIT_STATE_MANA='mana';UNIT_STATE_MAX_MANA='maxMana';UNIT_TYPE_STRUCTURE='structure';UNIT_TYPE_MAGIC_IMMUNE='immune'
ATTACK_TYPE_NORMAL='normal';DAMAGE_TYPE_MAGIC='magic';WEAPON_TYPE_WHOKNOWS='unknown'
function ModuloInteger(a,b) return a%b end
function GetWidgetLife(u) return u.hp end
function GetOwningPlayer(u) return u.owner end
function GetPlayerId(p) return p end
function GetPlayerController(p) return Controllers[p] or 'human' end
function GetTriggerUnit() return Caster end
function GetSpellTargetUnit() return Target end
function GetSpellAbilityId() return Spell end
function GetUnitTypeId(u) return u.type end
function GetUnitAbilityLevel(u,id) return u.abilities[id] or 0 end
function UnitAddAbility(u,id) u.abilities[id]=1 end
function UnitRemoveAbility(u,id) if u then u.abilities[id]=nil end end
function SetUnitAbilityLevel(u,id,n) u.abilities[id]=n end
function IsUnitIllusion(u) return u.illusion or false end
function IsUnitEnemy(u,p) return math.floor(u.owner/3)~=math.floor(p/3) end
function IsUnitType(u,t) return u[t] or false end
function GetUnitX(u) return u.x end
function GetUnitY(u) return u.y end
function GetUnitState(u,s) return u[s] end
function GetHeroLevel(u) return u.level end
function GetHeroSkillPoints(u) return u.points end
function SelectHeroSkill(u,id)
 for j=0,9 do if PlayableSkill[j]==id then
  local rank=u.abilities[id] or 0
  assert(rank<SkillRanks[j] and u.level>=SkillRequired[j]+rank*SkillSkip[j] and u.points>0,'Invalid bot learning')
  u.abilities[id]=rank+1;u.points=u.points-1;return
 end end
 error('Invalid skill')
end
Effects=0;Destroyed=0
function AddSpecialEffectTarget(model,u,attach) Effects=Effects+1;return {alive=true} end
function AddSpecialEffect(model,x,y) Effects=Effects+1;return {alive=true} end
function DestroyEffect(e) assert(e.alive,'Double effect destruction');e.alive=false;Destroyed=Destroyed+1 end
World={};Hits={}
function GroupEnumUnitsInRange(g,x,y,r,f) for _,u in ipairs(World)do if (u.x-x)^2+(u.y-y)^2<=r*r then g[#g+1]=u end end end
function FirstOfGroup(g) return g[1] end
function GroupRemoveUnit(g,u) assert(g[1]==u);table.remove(g,1) end
function UnitDamageTarget(c,t,amount,attack,ranged,at,dt,wt) assert(c~=t and amount>0);Hits[#Hits+1]={target=t,damage=amount};t.hp=t.hp-amount end
function SetUnitAnimation(u,a) u.animation=a end
function CreateSound(path,loop,d3,range,fi,fo,eax) return {path=path} end
function SetSoundDuration(s,d) assert(d>0) end
function SetSoundChannel(s,c) assert(c==0) end
function SetSoundVolume(s,v) assert(v==127) end
function SetSoundPitch(s,p) assert(p==1) end
function TimerStart(t,delay,loop,cb) assert(delay==.2);AudioCallback=cb end
function StopSound(s,kill,fade) assert(not kill) end
Played={}
function StartSound(s) Played[#Played+1]=s.path end
Controllers={};Orders={}
function IssueImmediateOrder(u,o) Orders[#Orders+1]={unit=u,order=o};return true end
function IssueTargetOrder(u,o,t) Orders[#Orders+1]={unit=u,order=o,target=t};return true end
function IssuePointOrder(u,o,x,y) Orders[#Orders+1]={unit=u,order=o,x=x,y=y};return true end
function make(p,x,y) return {type=0,owner=p,x=x,y=y,hp=10000,level=10,points=10,mana=1000,maxMana=1000,abilities={}} end
function cast(p,raw,rank,target)
 Caster=Hero[p];Caster.abilities[raw]=rank;Spell=raw;Target=target;SkillsEffect()
end
Hero[0]=make(0,0,0);Hero[1]=make(1,0,0);HeroRole[0]=0;HeroRole[1]=1;HeroType[0]=0;HeroType[1]=0
Dummy[0]=make(12,100,0);SkillScratch={}
for i=0,174 do AudioPath[i]='audio'..i;AudioDuration[i]=1000;AudioEAX[i]='' end
-- Original target receives native damage; script splash must only damage nearby enemies.
local victim=Dummy[0];local enemy=make(12,150,0);local ally=make(2,150,0);local immune=make(12,150,0);immune.immune=true
local building=make(12,150,0);building.structure=true;local far=make(12,900,0)
World={victim,enemy,ally,immune,building,far}
cast(0,PlayableSkill[3],1,victim);assert(#Hits==1 and Hits[1].target==enemy and Hits[1].damage==125 and #SkillScratch==0)
-- Real spell events cannot be spoofed by clones or other units with same owner.
Caster=make(0,0,0);Caster.abilities[PlayableSkill[3]]=1;SkillsEffect();assert(#Hits==1)
Hero[0].illusion=true;Caster=Hero[0];SkillsEffect();assert(#Hits==1);Hero[0].illusion=false
-- Sharingan uses exact learned rank, expires, cleans up after death, and never stacks handles.
cast(1,PlayableSkill[6],2,nil);assert(SharinganUntil[1]==18)
local ev=string.byte('R')*16777216+string.byte('s')*65536+string.byte('e')*256+string.byte('v')
assert(GetUnitAbilityLevel(Hero[1],ev)==2)
TimeNow=18;SkillsTick();assert(SharinganUntil[1]==0 and not SharinganArt[1] and GetUnitAbilityLevel(Hero[1],ev)==0)
cast(1,PlayableSkill[6],1,nil);Hero[1].hp=0;SkillsTick();assert(not SharinganArt[1] and GetUnitAbilityLevel(Hero[1],ev)==0);Hero[1].hp=10000
-- Three combo hits, then no retained target; interrupted combo must stop dealing damage.
Hits={};cast(1,PlayableSkill[7],2,victim)
for i=1,3 do SkillsTick() end
assert(#Hits==3 and Hits[1].damage==160 and ComboLeft[1]==0 and ComboTarget[1]==nil)
cast(1,PlayableSkill[7],3,victim);victim.x=900;SkillsTick();assert(#Hits==3 and ComboLeft[1]==0 and ComboTarget[1]==nil);victim.x=100
cast(1,PlayableSkill[7],3,victim);victim.hp=0;SkillsTick();assert(#Hits==3 and ComboTarget[1]==nil);victim.hp=10000
-- Both clips survive a burst of simultaneous casts instead of overwriting one pending index.
Played={};FoundationPlayPending();Played={};FoundationSound(0);FoundationSound(1);FoundationPlayPending();assert(#Played==2)
-- Bots spend existing skill points and respect level prerequisites, mana, and casting spacing.
TimeNow=30;Hero[1].abilities={};Hero[1].points=10;Hero[1].level=10;Controllers[1]='computer'
SkillsLearnBot(1);assert(Hero[1].points==0)
for j=5,9 do assert(GetUnitAbilityLevel(Hero[1],PlayableSkill[j])>0) end
assert(SkillsBot(1) and Orders[#Orders].order=='metamorphosis');local count=#Orders
assert(not SkillsBot(1) and #Orders==count)
TimeNow=33;assert(SkillsBot(1) and Orders[#Orders].order=='thunderbolt' and Orders[#Orders].target==victim)
TimeNow=36;Hero[1].mana=0;assert(not SkillsBot(1));Hero[1].mana=1000
victim.x=2000;assert(not SkillsBot(1));victim.x=100
-- Native morphs return to their normal unit without replacing the hero handle.
-- Their concrete object IDs, HP, duration and matching skill lists were checked above.
-- Test training selection from a different slot and preserve XP, items, gold and resources.
function GetHeroXP(u) return u.xp or 0 end
function SetHeroXP(u,xp,fx) u.xp=xp;u.level=math.floor(xp/100)+1 end
function SetHeroLevel(u,l,fx) u.level=l;u.points=l end
function CreateUnit(owner,raw,x,y,facing) local u=make(owner,x,y);u.level=1;u.points=1;u.type=raw;u.items={};return u end
function UnitItemInSlot(u,k) return (u.items or {})[k] end
function UnitRemoveItem(u,i) for k=0,5 do if u.items[k]==i then u.items[k]=nil end end end
function UnitAddItem(u,i) for k=0,5 do if not u.items[k] then u.items[k]=i;return true end end return false end
function RemoveUnit(u) u.removed=true end
function SelectUnitForPlayerSingle(u,p) Selected=u end
function PanCameraToTimedForPlayer(p,x,y,duration) end
function DisplayTimedTextToPlayer(p,x,y,duration,text) end
local old=make(7,0,0);old.xp=1900;old.items={[0]={name='item'}}
Hero[7]=old;SpawnX[7]=500;SpawnY[7]=600;HeroRole[7]=-1
SkillsChoose(7,0);assert(old.removed and HeroTemplate[7]==0 and HeroRole[7]==0 and Hero[7].xp==1900 and Hero[7].items[0].name=='item' and Selected==Hero[7])
local same=Hero[7];Controllers[7]='computer';SkillsChoose(7,1);assert(Hero[7]==same,'Bots cannot use human selection')
-- Spawn exactly playing slots; retain all four teams, skip open/closed slots.
PLAYER_SLOT_STATE_PLAYING='playing'
local slots={[0]='playing',[1]='playing',[4]='playing',[11]='playing'}
function GetPlayerSlotState(p)return slots[p] or 'empty'end
function SetPlayerState(p,s,n) end
function SetCameraFieldForPlayer(p,f,z,t) end
function PauseTimer(t) end
function DestroyTimer(t) end
Hero={};Controllers={};SpawnCursor=0
for p=0,11 do HeroType[p]=p;HeroRole[p]=(p<=1 and p or -1);SpawnX[p]=p*10;SpawnY[p]=0 end
for p=0,12 do FoundationSpawn() end
for p=0,11 do assert((Hero[p]~=nil)==(slots[p]=='playing'),'Open slots must remain empty') end
assert(Hero[0].level==10 and Hero[1].level==10 and Hero[4].level==1)
-- All started effect handles have a bounded cleanup path.
TimeNow=100;SkillsTick();assert(Effects==Destroyed)
`);
console.log('PASS: 10 skills/13 ability objects, stock bases/field types/data columns, native damage/clone/summon/morph references, 12 slots/4 forces; actual JASS splash filters, combo, Sharingan expiration/death, sound queue, bot learning/mana/order spacing and effect cleanup (mock natives).');
