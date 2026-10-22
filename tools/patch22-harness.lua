-- Exercise the new native passive through actual roster and bot-learning paths.
reset();local fire=-1
for kind=0,HERO_COUNT-1 do if HeroType[kind]==FourCC('Nfir')then fire=kind end end
assert(fire>=0);CreateHero(0,fire);Bot[0]=true;SetHeroLevel(Hero[0],500)
for i=1,600 do LearnHero(0)end
assert(GetUnitAbilityLevel(Hero[0],FourCC('Finc'))==200,'Firelord learns the real passive through normal bot progression')
assert(GetUnitAbilityLevel(Hero[0],FourCC('ANia'))==0,'No obsolete unconfigured arrow variant')
-- Every aura rank reaches an actual finer-grained native helper level, not just text.
reset();CreateHero(0,48);local h=Hero[0];h.x=0;h.y=0
for p=1,11 do Hero[p].x=5000;Hero[p].y=5000 end
local ally=CreateUnit(1,FourCC('fm00'),100,0,0);local prior=0
for rank=1,200 do
 h.abilities[HeroSkill[48*4]]=rank;CreativeTick()
 local actual=GetUnitAbilityLevel(ally,FourCC('Clif'))
 assert(actual>prior,'Every blood aura rank must increase actual attack lifesteal');prior=actual
end
assert(prior==380)
h.hp=0;CreativeTick();assert(GetUnitAbilityLevel(ally,FourCC('Clif'))==0,'No permanent helper after source death')
print('PASS:0.22 Firelord native passive/bot learning and200 actual lifesteal helper increments with cleanup (mock natives).')
