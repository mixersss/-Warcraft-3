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
for(const [id,hp]of [['Rn05',1000],['Rs05',850]]){const mods=abilities.find(o=>o.newId===id).modifications;const field=(f,l=0)=>mods.find(m=>m.id===f&&m.levelOrVariation===l)?.value;assert.equal(field('alev'),1);assert.equal(field('arlv'),60);assert.equal(field('alsk'),0);assert.equal(field('Eme5',1),hp);assert.equal(field('ahdu',1),0);assert.equal(field('adur',1),1);assert(!mods.some(m=>m.levelOrVariation>1));}
const get=(o,id,rank=0)=>o.modifications.find(m=>m.id===id && (m.levelOrVariation||0)===(schema.abilityFields[id]?.repeat===0?0:rank))?.value;
const unit=Object.fromEntries(units.map(o=>[o.newId,o]));
const ability=Object.fromEntries(abilities.map(o=>[o.newId,o]));
const nativeNPC=JSON.parse(fs.readFileSync(__dirname+'/src/npc-native-source.json'));
const nativeSourceAbilities=Object.fromEntries(nativeNPC.abilities.map(o=>[o.newId,o]));
const nativeModels=new Set(["Doodads\\Cityscape\\Props\\City_Fountain\\City_Fountain.mdl","Abilities\\Weapons\\AvengerMissile\\AvengerMissile.mdl", "Abilities\\Spells\\Other\\Tornado\\TornadoElemental.mdl", "Doodads\\Cinematic\\TownBurningFireEmitter\\TownBurningFireEmitter.mdl", "Objects\\Spawnmodels\\Other\\NeutralBuildingExplosion\\NeutralBuildingExplosion.mdl", "Doodads\\Ashenvale\\Props\\AshenLogAngled\\AshenLogAngled.mdl"].map(x=>x.toLowerCase()));
for(const v of JSON.parse(fs.readFileSync(__dirname+'/src/skill-visuals.json')).visualUnits)if(/^(abilities|objects|doodads)\\/i.test(v.model))nativeModels.add(v.model.toLowerCase());
for(const o of nativeNPC.units){const m=o.modifications.find(m=>m.id==='umdl')?.value;if(m && /^(abilities|objects|doodads|sharedmodels)\\/i.test(m) || m==='none.mdl')nativeModels.add(m.toLowerCase());}
for(const nativeModel of ["Buildings\\Other\\BarrelsUnit0\\BarrelsUnit0.mdl","Doodads\\Terrain\\RockChunks\\RockChunks0.mdl"])nativeModels.add(nativeModel.toLowerCase());
const assets=new Set([...JSON.parse(fs.readFileSync(__dirname+'/src/asset-manifest.json')),...JSON.parse(fs.readFileSync(__dirname+'/src/generated-assets.json')),...JSON.parse(fs.readFileSync(__dirname+'/src/extra35-assets.json'))].map(r=>r.path.toLowerCase()));
for(const o of units){
 assert(['rdum','rdst'].includes(o.newId) || (get(o,'uico')||'replaceabletextures\\').toLowerCase().startsWith('replaceabletextures\\') || assets.has((get(o,'uico')||'').toLowerCase()),'Missing unit portrait '+o.newId);
 if(!['rdum','rdst'].includes(o.newId))assert(((get(o,'umdl')||'units\\').toLowerCase().startsWith('units\\') || nativeModels.has(get(o,'umdl').toLowerCase())) || assets.has(get(o,'umdl').replace(/\.mdl$/i,'.mdx').toLowerCase()),'Missing unit model '+o.newId);
}
for(const row of rows)assert(row.icon.toLowerCase().startsWith('replaceabletextures\\') || assets.has(row.icon.toLowerCase()),'Missing spell icon');
function kind(t){return t==='real'?1:t==='unreal'?2:['int','bool','attackBits','deathType','regenType','channelType','channelFlags','silenceFlags','detectionType','teamColor','spellDetail'].includes(t)?0:3;}
for(const o of abilities){
 assert.equal(get(o,'aefs'),'');assert.equal(get(o,'aefl'),'');
 assert(schema.stockIds.abilities.includes(o.oldId),'Invalid native ability base '+o.oldId);
 for(const mod of o.modifications){const meta=schema.abilityFields[mod.id];if(!meta){const expected=nativeSourceAbilities[o.newId]?.modifications.find(m=>m.id===mod.id&&m.levelOrVariation===mod.levelOrVariation&&m.dataPointer===mod.dataPointer);assert(expected,'Unknown field without original provenance '+o.newId+':'+mod.id);assert.equal(mod.variableType,expected.variableType);assert.equal(mod.value,expected.value);continue;}assert.equal(mod.variableType,kind(meta.type),o.newId+':'+mod.id);if(meta.repeat===0){assert.equal(mod.levelOrVariation,0,o.newId+':'+mod.id+' must be global');assert.equal(mod.dataPointer,0);}else if(mod.levelOrVariation>0)assert.equal(mod.dataPointer,meta.column,o.newId+':'+mod.id+' column');}
}
for(const o of units){
 assert.equal(get(o,'usnd'),'');assert(get(o,'ucs1'),'Weapon impacts must remain audible');assert.equal(get(o,'ucs2'),'');
 assert(schema.stockIds.units.includes(o.oldId),'Invalid native unit base');
 for(const mod of o.modifications){const meta=schema.unitFields[mod.id];assert(meta,'Unknown unit field '+mod.id);assert.equal(mod.variableType,kind(meta.type),o.newId+':'+mod.id);}
 for(const id of (get(o,'uhab')||'').split(',').filter(Boolean))assert(ability[id]);
}
for(let j=0;j<rows.length;j++){const pos=rows[j].slot;assert.equal(get(ability[rows[j].id],'abpy'),pos<4?2:1);assert.equal(get(ability[rows[j].id],'abpx'),pos<4?pos:1);}
const buffs=parse(Parser,'war3map.w3h').customTable.objects;
assert.equal(buffs.length,7+nativeNPC.buffs.length);assert.equal(get(buffs.find(b=>b.newId==='Rsmb'),'ftat'),'');assert(buffs.some(b=>b.newId==='Rksb'&&b.oldId==='BPSE'));
for(const buff of buffs){assert(schema.stockIds.buffs.includes(buff.oldId),'Invalid native buff base '+buff.oldId);for(const mod of buff.modifications){assert(schema.buffFields[mod.id]);assert.equal(mod.variableType,kind(schema.buffFields[mod.id].type));}}
for(let rank=1;rank<=4;rank++){assert.equal(get(ability.R601,'abuf',rank),'Bmlc,Bmlt');assert.equal(get(ability.Rbyg,'aran',rank),200+200*rank);assert.equal(get(ability.Rbyg,'Det1',rank),1);}
assert.equal(rows.length,58);assert.equal(new Set(rows.map(r=>r.id)).size,58);
for(const r of rows){assert.equal(get(ability[r.id],'alev'),r.ranks);for(let rank=1;rank<=r.ranks;rank++){assert.equal(get(ability[r.id],'amcs',rank),r.mana[rank-1]);assert(Math.abs(get(ability[r.id],'acdn',rank)-(r.cooldowns?.[rank-1]??r.cooldown))<.01);}}
assert.equal(get(unit.R000,'uhab'),rows.slice(0,5).map(r=>r.id).join(','));
assert.equal(get(unit.R001,'uhab'),rows.filter(r=>r.hero===1).map(r=>r.id).join(','));
for(const [normal,form,morph] of [['R000','Rnfm','Rn05'],['R001','Rsfm','Rs05'],['R007','Rkfm','R705'],['R009','Rgfm','R904']]){
 assert.equal(get(unit[form],'uhab'),get(unit[normal],'uhab'));
 for(let rank=1;rank<=get(ability[morph],'alev');rank++){assert.equal(get(ability[morph],'Eme1',rank),normal);assert.equal(get(ability[morph],'Emeu',rank),form);}
}
for(let rank=1;rank<=3;rank++){assert(unit[get(ability.Rn03,'Hwe1',rank)]);assert.equal(get(ability.Rn03,'Hwe2',rank),1);assert(get(ability.Rsev,'Eev1',rank)<=.75);}
assert.equal(get(unit.rt03,'uhpm'),2800);assert.equal(get(unit.rt03,'ua1b'),110);
for(let n=1;n<=3;n++){assert.equal(get(ability.R902,'Nms1',n),n,'Native shield stores damage absorbed per mana');assert(Math.abs(get(ability.R902,'Nms2',n)-[.5,.7,.9][n-1])<1e-6);}
for(let rank=1;rank<=4;rank++){assert.equal(get(ability.R201,'ahdu',rank),.75);assert.equal(get(ability.R201,'adur',rank),1.25);assert.equal(get(ability.Rn01,'atar',rank),'self');assert.equal(get(ability.Rn01,'Uau2',rank),[1,2,4,8][rank-1]);}
assert.equal(get(ability.Rpsm,'Ncs2',1),1);assert.equal(get(ability.Rdog,'Eme1',1),'ra03');assert.equal(get(ability.Rdog,'Emeu',1),'rdgf');assert.equal(get(ability.Rktr,'Htb1',1),0);assert.equal(get(ability.Rktr,'ahdu',1),3);
for(const [id,skills] of Object.entries({ra02:['ACct'],ra03:['ACct','Rdog'],rdgf:['ACct','Rdog'],rc03:['AEbl','ACvs','Rpsm'],rk01:['Rktr'],rs03:['Aens','Ansk','A02E']}))for(const a of skills)assert(get(unit[id],'uabi').split(',').includes(a),id+':'+a);
assert.equal(get(ability.Rn02,'Omi1',4),8);assert.equal(get(ability.Rn04,'Htb1',3),650);assert.equal(get(ability.Rs04,'Htb1',3),800);
const audit=JSON.parse(fs.readFileSync(__dirname+'/src/source-skill-audit.json'));
for(const h of audit.heroes)assert.deepEqual(rows.filter(r=>r.hero===h.hero).map(r=>r.source_id),h.sourceSkills);
assert.equal(ability.Rlog.oldId,'AOwk');assert.equal(get(ability.Rlog,'aher'),0);assert.equal(get(ability.Rlog,'amcs',1),150);assert.equal(get(ability.Rlog,'acdn',1),22);assert.equal(get(ability.Rlog,'adur',1),3);assert.equal(get(ability.Rlog,'ahdu',1),3);assert.equal(get(ability.Rlog,'Owk1',1),0);assert(Math.abs(get(ability.Rlog,'Owk2',1)-.2)<.001);assert.equal(get(ability.Rlog,'Owk3',1),50);assert.equal(get(ability.Rlog,'abuf',1),'BOwk');assert.equal(get(ability.Rlog,'aart'),'Icon_Kawarimi.blp');assert.equal(get(ability.Rlog,'ahky'),'D');assert.equal(get(ability.Rlog,'abpx'),2);assert.equal(get(ability.Rlog,'abpy'),1);
for(const o of units)if(['Hpal','Edem','Hblm'].includes(o.oldId) && o.newId.startsWith('R'))assert(get(o,'uabi').split(',').includes('Rlog'),'Every base/morph hero has the common skill');
assert.equal(ability.R604.oldId,'ANcl');assert.equal(ability.R301.oldId,'ANcl');assert.equal(ability.Rjtr.oldId,'Aeat');assert.equal(get(ability.Rjtr,'acas',1),10);
for(const o of units)if(['Hpal','Edem','Hblm'].includes(o.oldId) && o.newId.startsWith('R'))assert(get(o,'uabi').split(',').includes('Rjtr'));
assert.equal(get(ability.Lgar,'Idef',1),10);assert.equal(get(ability.Lcar,'Idef',1),25);
for(const [raw,projectile] of [['R002','Shurikens.mdl'],['R005','Shurikens.mdl'],['R006','Shurikens.mdl'],['R009','gaars sand.mdl'],['R00B','WindAttack.mdl']]){assert.equal(get(unit[raw],'ua1w'),'missile');assert.equal(get(unit[raw],'ua1m'),projectile);assert.equal(get(unit[raw],'ua1r'),700);assert.equal(get(unit[raw],'udp1'),.5);}
assert.equal(get(unit.re01,'ulev'),4);assert.equal(get(unit.re02,'ulev'),4);assert.equal(get(unit.re03,'ulev'),20);assert.equal(get(unit.re04,'ulev'),30);
for(const id of ['Zbwp','Zbce','Zbbl','Ljkn','Ljsh','Ljnt'])assert(ability[id]);
const info=parse(Info,'war3map.w3i');assert.equal(info.players.length,12);assert.equal(info.forces.length,4);assert.deepEqual(info.forces.map(f=>f.playerMasks),[7,56,448,3584]);
const L=lauxlib.luaL_newstate();lualib.luaL_openlibs(L);
function run(s){if(lauxlib.luaL_dostring(L,to_luastring("local ok,err=xpcall(function()\n"+s+"\nend,debug.traceback);if not ok then error(err)end"))!==lua.LUA_OK)throw Error(to_jsstring(lua.lua_tostring(L,-1)));}
run(translate(source).replace(/\bnot(?=[A-Z(])/g,'not '));
for(const m of source.matchAll(/^\s*(integer|real|boolean) array (\w+)\s*$/gm))run(`setmetatable(${m[2]}, {__index=function() return ${m[1]==='boolean'?'false':'0'} end})`);
run("for i=0,11 do _G['SkillsData'..i]() end; SkillDataReady=true");
run(`
debug.setmetatable('',{__add=function(a,b)return tostring(a)..tostring(b)end})
function Player(p) return p end
PLAYER_SLOT_STATE_PLAYING='playing'
function GetPlayerSlotState(p)return PLAYER_SLOT_STATE_PLAYING end
MAP_CONTROL_COMPUTER='computer';UNIT_STATE_MANA='mana';UNIT_STATE_MAX_MANA='maxMana';UNIT_TYPE_STRUCTURE='structure';UNIT_TYPE_MAGIC_IMMUNE='immune';UNIT_TYPE_DEAD='dead'
ATTACK_TYPE_NORMAL='normal';DAMAGE_TYPE_MAGIC='magic';WEAPON_TYPE_WHOKNOWS='unknown'
function ExecuteFunc(name)_G[name]()end
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
function IsUnitType(u,t) return u and (u[t] or false) or false end
function IsUnitHidden(u)return u and u.hidden or false end
function IsUnitPaused(u)return u and u.paused or false end
function IsUnitVisible(u,p)return u and not u.hidden and (not u.invisible or u.detected)end
function IsUnitInvisible(u,p)return u and u.invisible or false end
function IsUnitDetected(u,p)return u and u.detected or false end
function UnitResetCooldown(u)u.cooldownResets=(u.cooldownResets or 0)+1 end
function Condition(f)return f end
function GroupEnumUnitsInRect(g,r,f) for _,u in ipairs(World)do g[#g+1]=u end end
function GetUnitX(u) return u.x end
function GetUnitY(u) return u.y end
function GetUnitState(u,s) return u[s] end
function SetUnitState(u,s,v) u[s]=math.max(0,v) end
function SetWidgetLife(u,hp) u.hp=hp end
function RMaxBJ(a,b) return math.max(a,b) end
function RMinBJ(a,b) return math.min(a,b) end
function IMinBJ(a,b) return math.min(a,b) end
function RAbsBJ(a) return math.abs(a) end
function R2I(x) return math.floor(x) end
function UnitMakeAbilityPermanent(u,flag,id) end
FOG_OF_WAR_VISIBLE=1;UNIT_TYPE_HERO='hero';PATHING_TYPE_WALKABILITY='walk'
function IsTerrainPathable(x,y,t)return false end
FogCreated=0;FogDestroyed=0;Pings={};LocalPlayer=4
function CreateFogModifierRadius(p,state,x,y,r,shared,after) FogCreated=FogCreated+1;return {owner=p,radius=r} end
function FogModifierStart(f)f.active=true end
function FogModifierStop(f)f.active=false end
function DestroyFogModifier(f)assert(not f.destroyed);f.destroyed=true;FogDestroyed=FogDestroyed+1 end
function GetTerrainCliffLevel(x,y)return 0 end
function SetUnitPosition(u,x,y)u.x=x;u.y=y end
function GetLocalPlayer()return LocalPlayer end
function IsPlayerAlly(a,b)return math.floor(a/3)==math.floor(b/3)end
function PingMinimapEx(x,y,d,r,g,b,extra)Pings[#Pings+1]={x=x,y=y}end
function GetUnitFacing(u) return 0 end
function GetUnitCurrentOrder(u)return u.order or 0 end
function Cos(x) return math.cos(x) end
function Sin(x) return math.sin(x) end
function SquareRoot(x) return math.sqrt(x) end
function GetSpellTargetX() return AimX or 100 end
function GetSpellTargetY() return AimY or 0 end
function UnitApplyTimedLife(u,buff,duration) u.expire=TimeNow+duration end
bj_PI=math.pi
bj_DEGTORAD=math.pi/180
UNIT_STATE_LIFE='hp';UNIT_STATE_MAX_LIFE='maxLife'
function GetHeroAgi(u,bonus)return u.agi or 20 end
function SetHeroAgi(u,v,permanent)u.agi=v end
function GetUnitMoveSpeed(u)return u.speed or 300 end
function SetUnitMoveSpeed(u,v)u.speed=v end
function GetRandomInt(a,b)return a end
function GetRandomReal(a,b)return (a+b)/2 end
function AddLightningEx(code,visible,x,y,z,tx,ty,tz)return {alive=true}end
function SetLightningColor()end
function DestroyLightning(l)assert(l.alive);l.alive=false end
function GetHeroLevel(u) return u.level end
function GetHeroSkillPoints(u) return u.points end
function SelectHeroSkill(u,id)
 for j=0,59 do if PlayableSkill[j]==id then
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
function CreateGroup()return {}end
function GroupClear(g)for i=#g,1,-1 do g[i]=nil end end
function GroupAddUnit(g,u)for _,v in ipairs(g)do if u==v then return end end;g[#g+1]=u end
function CreateTrigger()return {actions={}}end
function TriggerAddAction(t,f)t.actions[#t.actions+1]=f end
function InitHashtable()return {}end
function SaveInteger(t,p,c,v)t[p]=t[p]or{};t[p][c]=v;return true end
function LoadInteger(t,p,c)return t[p]and t[p][c]or 0 end
UNIT_TYPE_SUMMONED='summoned'
function Rect(a,b,c,d)return {a,b,c,d}end
function SaveReal(t,p,c,v)t[p]=t[p]or{};t[p][c]=v;return true end
function LoadReal(t,p,c)return t[p]and t[p][c]or 0 end
function FlushChildHashtable(t,p)t[p]=nil end
function GetHandleId(h)return h end
function TriggerRegisterPlayerUnitEvent()end
function GroupAddGroup(src,dst)for _,u in ipairs(src)do GroupAddUnit(dst,u)end end
function SetRect(r,a,b,c,d)r[1]=a;r[2]=b;r[3]=c;r[4]=d end
function GetOrderTargetUnit()return Target end
function GetOrderPointX()return AimX or 0 end
function GetOrderPointY()return AimY or 0 end
function EnumDestructablesInRect()end
Source40Init()
Source35Init()
function FirstOfGroup(g) return g[1] end
function GroupRemoveUnit(g,u)for i,v in ipairs(g)do if v==u then table.remove(g,i);return end end end
function UnitDamageTarget(c,t,amount,attack,ranged,at,dt,wt) assert(c~=t and amount>0);Hits[#Hits+1]={target=t,damage=amount};t.hp=t.hp-amount;return true end
function AddUnitAnimationProperties(u,tag,on)u.alternate=on end
function SetUnitInvulnerable(u,on)u.invul=on;if on then u.abilities[1098282348]=1 else u.abilities[1098282348]=nil end end
function ShowUnit(u,show)u.hidden=not show end
function PauseUnit(u,pause)u.paused=pause end
function SetUnitTimeScale(u,s)if u then u.timeScale=s end end
function QueueUnitAnimation(u,s)u.queuedAnimation=s end
function SetUnitFlyHeight(u,h,s)u.flyHeight=h end
function GetUnitFlyHeight(u)return u.flyHeight or 0 end
function SetUnitFacing(u,a)u.facing=a end
function SetUnitAnimation(u,a) u.animation=a end
function SetUnitAnimationByIndex(u,n) assert(n>=0);u.animationIndex=n end
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
function make(p,x,y) return {type=0,owner=p,x=x,y=y,hp=10000,maxLife=10000,level=10,points=10,mana=1000,maxMana=1000,abilities={}} end
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
cast(1,PlayableSkill[6],2,nil);assert(SharinganUntil[1]==10.5)
local ev=string.byte('R')*16777216+string.byte('s')*65536+string.byte('a')*256+string.byte('g')
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
TimeNow=30;Hero[1].abilities={};Hero[1].points=30;Hero[1].level=60;Controllers[1]='computer'
SkillsLearnBot(1);assert(Hero[1].points<30)
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
RosterHeroType[0]=0;RosterHeroType[1]=1;Hero[7]=old;SpawnX[7]=500;SpawnY[7]=600;HeroRole[7]=-1
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
for p=0,11 do HeroType[p]=p;HeroRole[p]=p;SpawnX[p]=p*10;SpawnY[p]=0 end
for p=0,12 do FoundationSpawn() end
for p=0,11 do assert((Hero[p]~=nil)==(slots[p]=='playing'),'Open slots must remain empty') end
assert(Hero[0].level==1 and Hero[1].level==1 and Hero[4].level==1)
-- All started effect handles have a bounded cleanup path.
TimeNow=100;SkillsTick();for i=1,40 do VisualTick() end;assert(Effects==Destroyed)
`);
run(fs.readFileSync(__dirname+'/roster-harness.lua','utf8'));
const storyLines=source.split('\n').filter(s=>/^\s*set (StoryX|StoryY|StoryItem|StoryPrice|SpawnX|SpawnY|EnemySpawnX|EnemySpawnY|StoryMentorType|StoryMentorName|StoryLootType|StoryShopX|StoryShopY)\[\d+\]/.test(s));
run(translate('function StoryFixtureData takes nothing returns nothing\n'+storyLines.join('\n')+'\nendfunction\n'));run('StoryFixtureData()');
run(fs.readFileSync(__dirname+'/hud-native-mocks.lua','utf8'));
run(fs.readFileSync(__dirname+'/npc-native-mocks.lua','utf8'));
run(fs.readFileSync(__dirname+'/story-harness.lua','utf8'));
run(fs.readFileSync(__dirname+'/tree-jump-harness.lua','utf8'));
run(fs.readFileSync(__dirname+'/presentation-harness.lua','utf8'));
run(fs.readFileSync(__dirname+'/technique-audit-harness.lua','utf8'));
run(fs.readFileSync(__dirname+'/visual-harness.lua','utf8'));
run(fs.readFileSync(__dirname+'/corrective-harness.lua','utf8'));
run(fs.readFileSync(__dirname+'/appearance-harness.lua','utf8'));
for(const m of source.matchAll(/^\s*set (Exam(?:Spawn[XY]|Enemy[XY]|QuestionText|Correct)\[\d+\])=(.+)$/gm))run(m[1]+'='+m[2]);
const examTypeLines=source.split('\n').filter(s=>/^\s*set ExamEnemyType\[\d+\]/.test(s));
run(translate('function ExamTypeFixtureData takes nothing returns nothing\n'+examTypeLines.join('\n')+'\nendfunction\n'));run('ExamTypeFixtureData()');
run(fs.readFileSync(__dirname+'/exam-harness.lua','utf8'));
run(fs.readFileSync(__dirname+'/common-harness.lua','utf8'));
const campaignLines=source.split('\n').filter(s=>/^\s*set Campaign(?:Unit|Animation|Name|Intro|Music|Limit|X|Y|TX|TY|MinX|MinY|MaxX|MaxY|LeafX|LeafY|LeafFacing|AnbuX|AnbuY|AnbuFacing|MedicX|MedicY|SupportX|SupportY|BarrelX|BarrelY|RouteX|RouteY|FiveX|FiveY|FiveType|DefenderX|DefenderY|ReserveX|ReserveY|WaveSpawnX|WaveSpawnY|WaveOrigin|WaveDestination|WaveKind|WaveRole|WavePeriod|WaveDelay)\[\d+\]/.test(s)||/^\s*set ArenaSeat[XY]\[\d+\]/.test(s));
run(translate('function CampaignFixtureData takes nothing returns nothing\n'+campaignLines.join('\n')+'\nendfunction\n'));run('CampaignFixtureData()');
run('CampaignTestStats={}');for(const u of units)if(/^[Cc][0-9A-F]{3}$/.test(u.newId))run(`CampaignTestStats[${Buffer.from(u.newId).readUInt32BE()}]={hp=${get(u,'uhpm')||10000}}`);
const npcLines=source.split('\n').filter(s=>/^\s*set RosterHeroType\[\d+\]/.test(s)||/^\s*set NPC(?:ChannelGuard|SourceTypeDummy|SpellCount|Ability|Order|OrderId|Rank|Target|Range|Radius|Cost|Cooldown|Hold)\[\d+\]/.test(s));
run(translate('function NPCFixtureData takes nothing returns nothing\n'+npcLines.join('\n')+'\nendfunction\n'));run('NPCFixtureData()');
run(fs.readFileSync(__dirname+'/campaign-harness.lua','utf8'));
run(fs.readFileSync(__dirname+'/npc-harness.lua','utf8'));
run(fs.readFileSync(__dirname+'/forest-fixes-harness.lua','utf8'));
run(fs.readFileSync(__dirname+'/village-fixes-harness.lua','utf8'));
run(fs.readFileSync(__dirname+'/arena-items-harness.lua','utf8'));
run(fs.readFileSync(__dirname+'/source18-harness.lua','utf8'));
run(fs.readFileSync(__dirname+'/defense19-harness.lua','utf8'));
run(fs.readFileSync(__dirname+'/invasion20-harness.lua','utf8'));
run(fs.readFileSync(__dirname+'/events21-harness.lua','utf8'));
run(fs.readFileSync(__dirname+'/corrections22-harness.lua','utf8'));
run(fs.readFileSync(__dirname+'/visibility23-harness.lua','utf8'));
run(fs.readFileSync(__dirname+'/village23-harness.lua','utf8'));
run(fs.readFileSync(__dirname+'/balance24-harness.lua','utf8'));
run(fs.readFileSync(__dirname+'/visibility25-harness.lua','utf8'));
run(fs.readFileSync(__dirname+'/source35-harness.lua','utf8'));
run(fs.readFileSync(__dirname+'/cooldown27-harness.lua','utf8'));
run(fs.readFileSync(__dirname+'/late28-harness.lua','utf8'));
run(fs.readFileSync(__dirname+'/gaara31-harness.lua','utf8'));
run(fs.readFileSync(__dirname+'/sasuke31-harness.lua','utf8'));
run(fs.readFileSync(__dirname+'/skills33-harness.lua','utf8'));
run(fs.readFileSync(__dirname+'/death34-harness.lua','utf8'));
run(fs.readFileSync(__dirname+'/test35-harness.lua','utf8'));
run(fs.readFileSync(__dirname+'/techniques39-harness.lua','utf8'));
run(fs.readFileSync(__dirname+'/skills40-harness.lua','utf8'));
run(fs.readFileSync(__dirname+'/rebuild41-harness.lua','utf8'));
run(fs.readFileSync(__dirname+'/lee42-harness.lua','utf8'));
run(fs.readFileSync(__dirname+'/shadow-clones43-harness.lua','utf8'));
run(fs.readFileSync(__dirname+'/invasion44-harness.lua','utf8'));
run(fs.readFileSync(__dirname+'/sarutobi45-harness.lua','utf8'));
console.log('PASS: all 54 active skill animations including native abilities, delayed visual cleanup and source-native XP without synthetic quest bonuses (mock natives).');
console.log('PASS: smart tree orders, animated movement, landing, all four forest bounds, preserved trees, mana/cooldown, invalid/dead/distant trees and death/hero-replacement cleanup (mock natives).');
console.log('PASS: chapter JASS, separate team quests, empty teams, human/bot commands, native shop budget, 56 original ninja spawns, original 330s mentor departure, source forest stats, Haku response and five-second Zabuza blink without invented splash/clones, loot chance/pickup/use, one-time rewards, twenty-second revival, moving sand crest cleanup (mock natives).');
fs.writeFileSync(__dirname+'/dist/behavior-verification.json',JSON.stringify({late28NativeMocks:true,lowLevelSakuraEntrance:true,isolatedLateCampaignProgress:true,lateBossGatesVerified:true,cooldown27NativeMocks:true,statScrollPurchasesForAll12Roles:true,statPurchasesWithFullInventory:true,deferredLeeKick:true,source35NativeMocks:true,source35CloneCounts:[8,16,24,40],source35FullKits:[3,6],source35IndependentChoke:true,invasionCriticalPrefixNativeMocks:true,corrections23NativeMocks:true,corrections22NativeMocks:true,prelimWinnersOnly:true,scrollRewardLevels:2,kawarimiCooldownSeconds:22,sourceShieldDamagePerMana:[1,2,3],sourceShieldAbsorption:[.5,.7,.9],permanentDogAndPuppets:true,isolatedCompanionSpellState:true,sourceTechniqueSlots:58,rosterHeroes:12,activeBotOrders:54,legacyMechanicFamilies:9,source40NativeMechanics:true,rebuild41NativeMocks:true,staggeredDataCallbacks:12,originalNinjasPerTeam:14,mentorDepartureSeconds:330,originalLootItems:7,campaignObjectiveDataEntries:22,parallelCloneRooms:8,jiraiyaSearchBarrels:20,jiraiyaSearchSeconds:150,invasionStreams:8,invasionWavePeriods:[45,45,45,30,30,30,30,30],invasionRoleBasedEnemyCamp:true,visibleInvasionEventTimers:4,invasionEventCountdownSeconds:[400,760,820,1160],invasionEventTimerLifecycleNativeMocks:true,leafCornerFountainSpawns:9,sourceSoundGuardPosts:5,sourceSoundGuardRetreatHP:10000,medicPulseHP:75,medicPulseMana:25,medicPulseSeconds:.25,realMedicHealingNativeMocks:true,independentReinforcementCallbacks:true,invasionNativeBountyLifecycle:true,kibaTsugaHits:5,kibaTsugaDamagePerHit:[180,240,300],kibaTargetedMotionAndInterruptsNativeMocks:true,spacedInvasionSpawns:32,invasionUnitsPerWave:3,invasionWavePattern:[3,3,4],waveStallRecoveryNativeMocks:true,waveRecoveryWithoutTeleport:true,recycledActorMovementStateReset:true,leafWaveInterceptionNativeMocks:true,leafDefenseRallyPoints:[3,5],leafDefenseUpperShare:.3,windWalkNativeBuffCleanup:true,castLocalNPCVisibility:true,defenseCombatOverridesShoppingAndFollow:true,invasionWaypointRedirectsNativeMocks:true,villageShortcutActualChatDispatch:true,sourceLeafDefenders:140,sourceAnbuDefenders:102,sourceVillageMedics:6,sourceNPCSpellObjects:nativeNPC.abilities.length,sourceNPCFunctions:Object.keys(JSON.parse(fs.readFileSync(__dirname+'/src/npc-source-audit.json')).sourceFunctions).length,shopsOnlyDuringInvasion:false,shopsFromJiraiyaSearch:true,sourceVillageFountains:4,globalTeamByakuganNativeMocks:true,tentenKunaiImpactNativeMocks:true,alliedBotsDrawEnemyAggroNativeMocks:true,openingTimerDeferredNativeMocks:true,primaryHeroFamilies:12,arenaCampRegenExcluded:true,sourceUpperTerraceSeats:24,ramenRecoverySurvivesDamage:true,pointTargetNotesNativeMocks:true,villageServiceVisibilityAndNeutralSupply:true,narutoCloneCounts:[8,16,24,40],narutoCloneCount:8,narutoCloneOneAttackRule:true,kaitenDamage:[156,234,312,546],kaitenMultiplierFrom42:1.3,kaitenStunSeconds:1,byakuganAttackBonus:.15,cloneDeathOnlyOnActualDamage:true,sourceShikamaruVoice:true,arenaVictoryLevels:1,arenaBotLogUsesPerFight:1,botStatScrollPickup:true,corrections24NativeMocks:true,visibility25NativeMocks:true,autonomousOrochimaruAttack:true,sasukeStaleHiddenRecoverySeconds:10,finalEliminationDuels:3,threeWayFinal:true,cooldownsResetBeforeEveryFight:true,sourceBarrelModelRestored:true,arenaTestShortcutActualChatDispatch:true,arenaTestEarlyChapterCleanupAndReentry:true,arenaTerrainRevealWithoutDetection:true,arenaSharedVisionDisabled:true,arenaSpectatorCameraAndFilterRecovery:true,forestBotPairPatrolAndStalledGoalRecovery:true,characterBoundSasukeRole:true,campaignThroughEndingNativeMocks:true,treeJumpActualJASS:true,autoStartHumanTeamAtSeconds:30,skillSourceListsAudited:12,commonKawarimiDataAndBotOrders:true,stageHUDDeadlinesAndHandleCleanup:true,nativeMocks:true,enginePlaytest:false},null,2));
console.log('PASS: 58 skills across 12 heroes, stock bases/field types/data columns, native damage/clone/summon/morph references, 12 slots/4 forces; actual JASS splash filters, combo, Sharingan expiration/death, sound queue, all 54 bot cast orders, roster learning/healing/mana, combos/zones/companions, staggered init and bounded effect/timer cleanup (mock natives).');
