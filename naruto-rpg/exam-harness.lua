-- Run real generated chapter functions; these mocks do not prove engine rendering/pathfinding.
function TriggerRegisterPlayerChatEvent(t,p,text,exact)t.chat=true end
function GetTriggerPlayer()return ChatPlayer end
function GetEventPlayerChatString()return ChatText end
function SubString(s,a,b)return string.sub(s,a+1,b)end
function StringLength(s)return #s end
function S2I(s)return tonumber(s) or 0 end
function I2S(n)return tostring(n)end
function StopMusic()end
function PlayMusic(path)assert(path)end
MusicOn=false
local forcedRolls={}
function GetRandomInt(a,b)local n=table.remove(forcedRolls,1) or b;assert(n>=a and n<=b);return n end
function GetItemTypeId(it)return it and it.type or 0 end
function GetWidgetLife(w)return w and (w.hp or 1) or 0 end
function UnitItemInSlot(u,k)return u and u.items and u.items[k] or nil end
function SetItemPosition(it,x,y)it.x=x;it.y=y;it.owned=false end
function UnitRemoveItem(u,it)for k=0,5 do if u.items[k]==it then u.items[k]=nil end end;it.owned=false end
function UnitAddItem(u,it)for k=0,5 do if not u.items[k] then u.items[k]=it;it.owned=true;return true end end;return false end
function RemoveItem(it)it.removed=true;for p=0,11 do if Hero[p] then UnitRemoveItem(Hero[p],it)end end;it.type=0 end
function Rect(a,b,c,d)return {a,b,c,d}end
function RemoveRect(r)r.removed=true end
function DestroyTrigger(t)t.destroyed=true end
function EnumDestructablesInRect(r,filter,action)GatesOpened=(GatesOpened or 0)+1 end
local function raw(s)local n=0;for i=1,4 do n=n*256+string.byte(s,i)end;return n end
-- Fresh occupied/non-red teams plus one open team. Real first-answer path for humans/bots.
ExamPhase=0;ExamReadyAt=0;ExamUsed={};ExamAnswered={};ExamScore={};ExamAnswerAt={};ExamEnemy={};ExamScroll={};ExamDropped={};ExamEnemyCastAt={};ExamScrollCount=89;ExamRepopulateAt=0
setmetatable(ExamScore,{__index=function()return 0 end});setmetatable(ExamEnemyCastAt,{__index=function()return 0 end})
StoryMembers={[0]=3,[1]=3,[2]=0,[3]=3};StoryStage={[0]=5,[1]=4,[2]=0,[3]=5}
Hero={};Companion={};Dummy={};StoryMentor={};StoryEnemy={};EnemyMark={};BurstArt={};StoryShop={}
for t=0,3 do StoryShop[t]=CreateUnit(15,raw('rqsh'),0,0,0)end
for p=0,11 do
 if math.floor(p/3)~=2 then Hero[p]=CreateUnit(p,p,0,0,0);HeroRole[p]=p;HeroType[p]=p;Controllers[p]=(p==0 or p==3) and 'human' or 'computer';Hero[p].level=5;Hero[p].xp=0 end
end
TimeNow=100;NextChapterTick();assert(ExamPhase==0,'Wait for every occupied team')
StoryStage[1]=5;NextChapterTick();assert(ExamPhase==1 and ExamReadyAt==420)
TimeNow=419.5;NextChapterTick();assert(ExamPhase==1)
TimeNow=420;NextChapterTick();assert(ExamPhase==2 and Hero[0].paused and not Hero[6] and MusicCursor==1)
ExamAnswer(0,1);assert(not ExamAnswered[0],'No answer before first question')
for round=1,5 do
 TimeNow=ExamNextAt;NextChapterTick();assert(ExamAsked==round)
 local answer=ExamCorrect[ExamQuestion];local xp=Hero[0].xp
 ExamAnswer(0,9);assert(not ExamAnswered[0],'Invalid choices do not consume attempt')
 ChatPlayer=0;ChatText='-answer '+tostring(answer);ExamChat();assert(Hero[0].xp==xp+120 and ExamAnswered[0])
 ExamAnswer(0,answer);assert(Hero[0].xp==xp+120,'No duplicate XP')
 ExamAnswer(3,answer%4+1);local wrongXP=Hero[3].xp
 ExamAnswer(3,answer);assert(Hero[3].xp==wrongXP,'First answer is final')
 TimeNow=ExamNextAt-1;NextChapterTick();assert(ExamAnswered[1],'Computer answers independently before deadline')
end
assert(ExamScore[0]==5 and Hero[0].xp==600 and ExamScore[3]==0)
TimeNow=ExamNextAt;NextChapterTick();assert(ExamPhase==3 and MusicCursor==2 and StoryStage[0]==7 and StoryStage[2]==0)
assert(not Hero[0].paused and Hero[0].abilities[raw('Avul')]==nil,'Restore normal combat after quiz')
assert(ExamScroll[85] and ExamScroll[86] and not ExamScroll[87] and ExamScroll[88])
assert(not TreeJumpInside(0,1000,1000) and TreeJumpInside(0,-7000,-7000),'Exam tree jump bounds')
for j=0,84 do ExamForestTick()end
assert(ExamPopulateCursor==85 and ExamEnemy[84] and not ExamEnemy[85])
for j=0,84 do assert(ExamEnemy[j].type==ExamEnemyType[j],'Original melee/ranged composition must match')end
forcedRolls={40,1};ExamEnemy[0].hp=0;ExamForestTick();local dropped=ExamScroll[89];assert(dropped and dropped.type==raw('Eshe'))
ExamForestTick();assert(ExamScroll[89]==dropped,'One scroll drop per enemy')
-- Inventory is authoritative, not a global acquired flag. Bots free a slot without deleting gear.
Hero[1].items={};Hero[1].x=dropped.x;Hero[1].y=dropped.y
for k=0,5 do Hero[1].items[k]={type=raw('Nlga'),owned=true}end
local old=Hero[1].items[5];StoryRetreat[0]=false;StoryMarch[0]=true
ExamBot(1,nil);assert(not old.removed and not old.owned and Hero[1].last.target==dropped)
UnitAddItem(Hero[1],dropped);assert(ExamHas(0,raw('Eshe')))
Hero[1].hp=0;assert(not ExamHas(0,raw('Eshe')),'Dead carriers cannot turn in scrolls');Hero[1].hp=10000
local earth=CreateItem(raw('Esea'),0,0);Hero[0].items={};UnitAddItem(Hero[0],earth)
Hero[0].x=ExamTowerX;Hero[0].y=ExamTowerY;Hero[1].x=ExamTowerX;Hero[1].y=ExamTowerY
ExamForestTick();assert(StoryStage[0]==7 and not ExamTowerOpen,'Tower is closed for first 20 minutes')
TimeNow=ExamOpenAt;Hero[1].x=ExamTowerX+1000;ExamForestTick();assert(ExamTowerOpen and GatesOpened==1 and StoryStage[0]==7,'Both carriers must reach tower')
ExamBot(1,nil);assert(Hero[1].last.o=='move' and Hero[1].last.x==ExamTowerX)
Hero[1].x=ExamTowerX;ExamForestTick();assert(StoryStage[0]==8 and dropped.removed and earth.removed,'Consume real pair exactly once')
local reward=GetPlayerState(0,PLAYER_STATE_RESOURCE_GOLD);ExamForestTick();assert(GetPlayerState(0,PLAYER_STATE_RESOURCE_GOLD)==reward,'No repeat reward')
TimeNow=ExamEndAt;ExamForestTick();assert(StoryStage[1]==8 and StoryStage[3]==8,'Timeout still advances without awarding a pair')
ExamForestTick();assert(ExamPhase==4 and ExamClock==nil and ExamDialog==nil and ExamRect==nil,'Shared clock/dialog/rect cleanup')
print('PASS: five unique timed questions, first answers, human XP/bot answers, occupied-team barrier, preserved heroes, 85 staggered genin, one-time real scroll drops, full inventory pickup, tower timing, both carriers, one-time reward, timeout and cleanup (mock natives).')
