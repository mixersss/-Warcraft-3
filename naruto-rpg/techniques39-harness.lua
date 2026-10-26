-- Source-based presentation, bounded cleanup and level60 learning through real JASS.
for p=0,11 do RosterReset(p)end
local savedTerrain,savedCliff=IsTerrainPathable,GetTerrainCliffLevel
function IsTerrainPathable()return false end
function GetTerrainCliffLevel()return 0 end
CampaignStage=0;CampaignTransition=false;CampaignFinished=false;TimeNow=9900000;World={}
for p=0,1 do
 Hero[p]=CreateUnit(p,raw('R000')+p,0,0,0);HeroRole[p]=p;HeroType[p]=Hero[p].type
 Hero[p].level=59;Hero[p].points=60;Hero[p].hp=10000;Hero[p].mana=10000
 SkillsLearnBot(p);local skill=PlayableSkill[p*5+4]
 assert(SkillRanks[p*5+4]==1 and SkillRequired[p*5+4]==60 and GetUnitAbilityLevel(Hero[p],skill)==0,'No inaccessible65/70-rank or early form')
 Hero[p].level=60;Hero[p].points=1;SkillsLearnBot(p)
 assert(GetUnitAbilityLevel(Hero[p],skill)==1 and Hero[p].points==0,'One real skill point at60 gives maximum form')
 Hero[p].points=10;SkillsLearnBot(p);assert(GetUnitAbilityLevel(Hero[p],skill)==1,'Never learn a phantom second form rank')
end
local enemy=CreateUnit(12,123,400,0,0);enemy.hp=100000;enemy.maxLife=100000;World={enemy};local sasuke=Hero[1]
local function step(count)
 for i=1,count do TimeNow=TimeNow+.05;VisualTick()end
end
VisualApply(1,8,1,enemy);assert(sasuke.x==0 and not sasuke.paused and not sasuke.hidden)
step(3);assert(sasuke.x>0 and sasuke.x<100 and sasuke.animationIndex==10,'600/s source rush, never instant blink or charge loop')
step(15);assert(VisualApproachCaster[1]==nil and VisualApproachSkill[1]==0 and sasuke.animationIndex==11,'Separate normal strike sequence '..tostring(sasuke.x)..' state'..tostring(VisualApproachSkill[1])..' pose'..tostring(sasuke.animationIndex))
local bolts,flare=0,0
for i=0,255 do if VisualUnit[i]then if VisualUnit[i].type==raw('vchi')then bolts=bolts+1 elseif VisualUnit[i].type==raw('vcmf')then flare=flare+1 end end end
assert(bolts==3 and flare==2 and not VisualHand[4] and not VisualHand[5],'Exact source impact actor multiplicities and hand cleanup')
VisualClearHero(1);sasuke.x=0;sasuke.type=raw('Rsfm');VisualApply(1,8,1,enemy);step(3);assert(sasuke.animationIndex==5,'Cursed model uses its actual source spell sequence')
step(15);assert(sasuke.animationIndex==2,'Cursed form finishes with attack, not an absent normal sequence')
VisualClearHero(1);sasuke.type=HeroType[1];sasuke.x=0;VisualApply(1,8,1,enemy);enemy.dead=true;step(3)
assert(not VisualApproachCaster[1] and sasuke.x==0 and not VisualHand[4],'Engine-dead victim cancels movement and effects')
enemy.dead=false;VisualApply(1,8,1,enemy);VisualClearHero(1);assert(VisualApproachSkill[1]==0 and VisualChidoriUntil[1]==0,'Scene reset cancels all cast state')
local naruto=Hero[0];naruto.x=0;naruto.y=0;enemy.x=400;enemy.y=0
VisualRasenganStart(0,enemy);assert(naruto.timeScale==2 and VisualRasenganTarget[0]==enemy)
for i=0,5 do assert(VisualRasenganArt[i]and VisualRasenganArt[i].alive,'All six source target layers are retained')end
for i=0,2 do assert(VisualHand[i]and VisualHand[i].alive,'Three source hand chakra layers')end
step(11);assert(naruto.timeScale==1,'Source half-second speed reset')
step(52);assert(not VisualRasenganTarget[0] and VisualRasenganUntil[0]==0)
local impact=false;for i=0,255 do if VisualUnit[i]and VisualUnit[i].type==raw('vras')then impact=true;assert(VisualHeight[i]==-100 and VisualLife[i]==2)end end
assert(impact,'Original blue Naga impact actor appears after the three-second target effect')
for i=0,5 do assert(not VisualRasenganArt[i],'Target layer cleanup')end
VisualRasenganStart(0,enemy);VisualClearHero(0)
for i=0,5 do assert(not VisualRasenganArt[i])end
assert(not VisualRasenganCaster[0] and VisualRasenganPoseUntil[0]==0 and naruto.timeScale==1,'Transition cleanup restores animation speed')
IsTerrainPathable,GetTerrainCliffLevel=savedTerrain,savedCliff
print('PASS: source Chidori600/s/normal+cursed rush/strike and3+2impact actors; Rasengan3hand+6targetlayers/sourcepose speed/3sec blue impact; death/reset bounded cleanup and one-point maximum form learning at60 (mock natives).')
