"""Audit emitted data, including scripted kits; no engine or win-rate claims."""
import csv,json,math,os
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
BEFORE=json.loads((ROOT/'build/balance-before.json').read_text());NOW=json.loads((ROOT/'build/balance-current.json').read_text())
HEROES=json.loads((ROOT/'map/heroes.json').read_text());SEEDS=json.loads((ROOT/'map/ability-seeds.json').read_text());CFG=json.loads((ROOT/'map/balance-profiles.json').read_text());BAL=json.loads((ROOT/'map/balance.json').read_text());NAMES=json.loads((ROOT/'map/skill-names-ru.json').read_text());BOTS=json.loads((ROOT/'map/bot-profiles.json').read_text());STOCK=json.loads((ROOT/'map/stock-hero-balance.json').read_text())['heroes']
OUT=ROOT/'docs/balance';OUT.mkdir(exist_ok=True)
def value(data,kind,raw,field,rank=0,default=0):
 return data[kind].get(raw,{}).get('fields',{}).get(field,{}).get(str(rank),default)
def ability(raw,field,rank=0,data=NOW,default=0):return value(data,'abilities',raw,field,rank,default)
def field_values(raw,field,data=NOW):return data['abilities'].get(raw,{}).get('fields',{}).get(field,{})
def fmt(v):
 if isinstance(v,str):return v
 return f'{v:.4g}'
COUNTS={'Hwe2','Osf2','Efn1','Esv1','Nba2','Ndo2','Rai1','Uls1'}
SUMMON={'Hwe1','Osf1','Efnu','Esvu','Nbau','Ndou','Nef1','Nsy2','Nsyu','Rai3','Uin4','Ntou','Ulsu'}
EXCLUDE={'amcs','acas','aran','abuf','aeff','atar','alev','arlv','alsk'}

def observed(h,slot,rank,data=NOW):
 raw=h['skills'][slot];original=h.get('skill_sources',h['skills'])[slot]
 if data is BEFORE and raw=='Finc':raw='ANia';original='ANia'
 a=data['abilities'].get(raw,{});fields=a.get('fields',{});metrics={}
 if h.get('simple'):
  kind=h['simple'][slot]['kind']
  if kind in ['crabs','lizards','beast']:
   family={'crabs':0,'lizards':1,'beast':2}[kind];pet='k'+str(family)+f'{rank-1:02x}';count=(1 if family==2 else 2)+rank//10
   metrics['group_hp']=count*value(data,'units',pet,'uhpm');metrics['group_damage']=count*value(data,'units',pet,'ua1b')
  elif kind=='petbuff':metrics['army_ias']=value(data,'abilities','Csum','Oae2',rank)
  elif kind=='army_vamp':metrics['life_steal']=round((.12+(.20 if data is NOW else .18)*(rank-1)/199)*(1000 if data is NOW else 500))/(1000 if data is NOW else 500)
  elif kind=='rain':metrics['damage']=4*(45+6*rank)
  elif kind=='banner':metrics['army_ias']=value(data,'abilities','Cuba','Oae2',rank);metrics['armor']=value(data,'abilities','Cubd','Had1',rank)
  elif kind=='bladestorm':metrics['damage']=6*(30+7*rank);metrics['self_ias']=value(data,'abilities','Crag','Oae2',rank)
  else:
   specific={'bowcrit':['Ocr2'],'bowspeed':['Oae2'],'army_speed':['Oae2'],'army_armor':['Had1'],'cleave':['nca1'],'evasion':['Eev1'],'escape':['adur'],'rogueescape':['adur','Owk3']}.get(kind,[])
   metrics.update({f:ability(raw,f,rank,data)for f in specific})
 else:
  base=original
  for f,s in CFG['curves'].get(base,{}).items():
   if f in EXCLUDE:continue
   v=ability(raw,f,rank,data,default=None)
   if isinstance(v,(int,float)):metrics[f]=v
  for f in BAL['aura_balance'].get(base,{}):metrics[f]=ability(raw,f,rank,data)
  if raw in ['Fhas','Fmrg']:
   for f in ['Oae2','Oar1']:
    if str(rank)in fields.get(f,{}):metrics[f]=ability(raw,f,rank,data)
  if base in CFG['hybrid']:
   kind=['AHhb','AUdc','AEmb'].index(base);metrics['magnitude']=data['hybrid'][str(kind*200+rank-1)]
  if base=='AOmi':metrics['illusion_damage']=ability(raw,'Omi1',rank,data)*ability(raw,'Omi2',rank,data);metrics.pop('Omi2',None)
  if raw=='Finc':metrics.update({f:ability(raw,f,rank,data)for f in ['Nic1','Nic2','Nic4']})
  for f,rows in fields.items():
   if f not in SUMMON or str(rank)not in rows:continue
   ids=rows[str(rank)].split(',');count=max([ability(raw,c,rank,data)for c in COUNTS]+[1])
   prefix='factory'if f=='Nsyu'else'robot'if f=='Nsy2'else'summon'
   metrics[prefix+'_hp']=count*sum(value(data,'units',u,'uhpm')for u in ids)
   metrics[prefix+'_damage']=count*sum(value(data,'units',u,'ua1b')for u in ids)
  # Native copy Fent preserves AEfn counts and uses the same native summon model.
 if ability(raw,'acdn',rank,data)>0:metrics['cooldown']=ability(raw,'acdn',rank,data)
 return metrics

LABELS={'group_hp':'HP всех за призыв','group_damage':'суммарный базовый урон','summon_hp':'HP за призыв','summon_damage':'суммарный базовый урон призывов','army_ias':'скорость армии','life_steal':'вампиризм','damage':'урон','self_ias':'скорость героя','cooldown':'КД','magnitude':'эффект','Htb1':'урон','Ocr2':'множитель крита','Eev1':'уклонение','Omi3':'получаемый урон копий','Nms1':'коэффициент щита','Nic1':'урон за заряд','Nic2':'взрыв','illusion_damage':'суммарная доля урона копий','Oae2':'скорость атаки','Had1':'броня','Oar1':'HP/с','Uau2':'HP/с','Hab1':'мана/с','Eim1':'урон/тик'}

LABELS.update({'factory_hp':'HP фабрики','factory_damage':'урон фабрики','robot_hp':'HP одного робота','robot_damage':'базовый урон одного робота','Htc1':'урон по площади','ahdu':'действие на героя, с','adur':'длительность, с','Hbh1':'шанс оглушения, %','Hbh3':'доп.урон','Eer1':'урон/с','Wrs1':'урон','Uim3':'урон','Usl1':'непрерываемое оглушение, с','aare':'радиус','Hbn1':'замедление','Ucs1':'урон','Osh1':'урон','Ucs2':'общий предел урона','Osh2':'общий предел урона','Ocl1':'урон/лечение цели','Ocl3':'потеря эффекта на прыжок','Ufn1':'урон по площади','Ufn2':'доп.урон цели','Efk1':'урон цели','Efk2':'общий предел урона','Esh5':'начальный урон','Esh1':'периодический урон','Eim2':'расход маны/с','Hfa1':'урон стрелы','Hca1':'урон стрелы','Hca2':'замедление','Nba1':'урон стрелы','Nab4':'урон/с основной цели','Nab5':'урон/с остальных','Nab3':'снятая броня','Nso1':'урон/с','Nso3':'ослабление урона','Hbz2':'урон волны','Hbz6':'общий предел волны','Hfs1':'урон за интервал','Hfs3':'последующий урон','Ncs1':'эффект за интервал','Ncs4':'общий предел','Ndr1':'похищение HP/с','Ndr2':'похищение маны/с','Ndr5':'передача маны/с','Ufa2':'броня','Udp2':'коэффициент лечения','Udp1':'коэффициент маны','Roa1':'ослабление урона','Nsi2':'шанс промаха','Nsi3':'замедление','nca1':'доля рассекающего урона','Ocr1':'шанс критического удара, %','Ocr4':'уклонение','Uts1':'возврат урона','Uts2':'получаемый урон','Uts3':'броня','Owk2':'ускорение','Owk3':'урон из невидимости','Ebl1':'дальность','Ebl2':'минимальная дальность','Neg1':'ускорение','Neg2':'доп.урон','Ncr6':'ускорение формы','Hav1':'броня','Hav2':'доп.HP','Hav3':'доп.урон','Eme5':'доп.HP','Oww1':'урон/с','Esf1':'урон звезды','Etq1':'лечение за интервал','Oeq2':'урон зданиям/с','Oeq3':'замедление','Udd1':'доля HP/с','Udd2':'множитель по зданиям','Uin1':'урон падения','Ore1':'задержка возрождения, с','Hmt2':'задержка телепорта, с','Nch1':'предельный уровень цели','Ndo1':'урон/с','Nst3':'урон зверя','Nvc5':'урон камня','Nrg5':'доп.сила','Nrg6':'доп.броня','Uls4':'возврат урона в HP','Uls5':'порог возврата','Uau1':'скорость движения','Ear1':'урон дальних атак','Eah1':'возврат урона','Uav1':'вампиризм'})

def summary(metrics):
 entries=[(k,v)for k,v in metrics.items()if k!='cooldown'][:2]
 if 'cooldown'in metrics:entries.append(('cooldown',metrics['cooldown']))
 return '; '.join(f'{LABELS.get(k,k)} {fmt(v)}'for k,v in entries)or'нет данных роста основного эффекта'

rows=[];gaps=[];checked=0
for h in HEROES:
 for slot,raw in enumerate(h['skills']):
  cap=50 if slot==3 else 200
  prev=observed(h,slot,1)
  for rank in range(2,cap+1):
   cur=observed(h,slot,rank);checked+=1
   changed=any(abs(cur.get(k,0)-v)>1e-6 for k,v in prev.items())
   if not changed:gaps.append((h['id'],slot,rank))
   prev=cur
  ranks=[1,3,10,25,50]if slot==3 else [1,10,50,100,200]
  name=h.get('ability_names',[None]*4)[slot]if h.get('ability_names')else NAMES.get(raw,raw)
  if h.get('simple'):name=h['simple'][slot]['name']
  rows.append({'hero':h['name'],'hero_id':h['id'],'role':BOTS['roles'][BOTS['heroes'][h['id']]['role']]['name'],'key':'QWER'[slot],'skill':name,'raw':raw,'cap':cap,'ranks':ranks,'before':summary(observed(h,slot,cap,BEFORE)),'values':[summary(observed(h,slot,r))for r in ranks],'samples':{r:observed(h,slot,r)for r in ranks}})
assert len(rows)==200
(OUT/'All-skills.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2)+'\n')
report={'version':BAL['version'],'heroes':50,'mainSkills':200,'adjacentRankTransitionsChecked':checked,'ranksWithoutNumericOrScriptedProgress':gaps,'enginePlaytest':False,'winRatesMeasured':False,'preserved':{'waveSize':6,'waveSeconds':18,'armyCap':85,'heroLevel':500,'skillLevels':[200,50],'autosaveSeconds':120,'respawnSeconds':35},'modelLimits':['No combat engine, pathfinding or native projectile simulation.','Equal skill rank is not equal hero level or equal purchased build.','Damage/healing/group HP metrics do not represent wins or 1v1 tier lists.']}
(ROOT/'build/balance-audit.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
with (OUT/'All-skills.csv').open('w',newline='',encoding='utf-8-sig')as f:
 w=csv.writer(f,lineterminator='\n');w.writerow(['Герой','Роль','Клавиша','Навык','ID','Макс.ранг','Ранги','До на максимуме','Новая прогрессия'])
 for r in rows:w.writerow([r['hero'],r['role'],r['key'],r['skill'],r['raw'],r['cap'],'/'.join(map(str,r['ranks'])),r['before'],' | '.join(r['values'])])
text=['# Полная проверка 50 героев и 200 навыков', '',f'Версия **{BAL["version"]}**. Проверены **{checked:,}** переходов между соседними рангами. Ранг навыка и уровень героя — разные величины; максимум ульты открывается на уровне героя 496.','',
'В таблице указаны фактические поля собранной карты и отдельные эффекты авторских триггеров. У призывов считается сумма HP/базового урона за один вызов; это не DPS, число одновременно живущих призывов или рейтинг силы. Броня, иммунитеты, длительность боя, доступность целей и действия игрока меняют результат.','',
'У обычных навыков столбцы: **1 / 10 / 50 / 100 / 200**. У ульт: **1 / 3 / 10 / 25 / 50**. КД — секунды. Проценты в машинных полях показаны долями: 0,5 = 50%.','',
'[CSV для Excel](All-skills.csv) · [Основной отчёт](../Balance-0.22.0.md)','']
for h in HEROES:
 text += ['## '+h['name'],'', 'Роль ИИ: '+BOTS['roles'][BOTS['heroes'][h['id']]['role']]['name']+'.','', '| Кнопка / навык | 1 | 10 / 3 | 50 / 10 | 100 / 25 | 200 / 50 |','|---|---|---|---|---|---|']
 for r in rows:
  if r['hero_id']==h['id']:text.append('| '+' | '.join([r['key']+' — '+r['skill']]+r['values'])+' |')
 text.append('')
(OUT/'All-skills.md').write_text('\n'.join(text)+'\n')
# Transparent before/after numerical diagnostics, with no inferred win rates.
findings=[]
for label,raw,field,rank in [('Магический щит','ANms','Nms1',200),('Крит: шанс','AOcr','Ocr1',200),('Крит: множитель','AOcr','Ocr2',200),('Уклонение','AEev','Eev1',200),('Смертельный союз: коэффициент лечения','AUdp','Udp2',200),('Порча: доля HP/с','AUdd','Udd1',50),('Щит: длительность','AHds','adur',200),('Щит: откат','AHds','acdn',200),('Скачок: дальность','AEbl','Ebl1',200),('Скачок: откат','AEbl','acdn',200)]:findings.append([label,ability(raw,field,rank,BEFORE),ability(raw,field,rank)])
(OUT/'Findings.json').write_text(json.dumps({'findings':findings,'rankProgressGaps':gaps},ensure_ascii=False,indent=2)+'\n')
# Reproducible, exportable diagnostics.
os.environ.setdefault('XDG_CACHE_HOME','/tmp/warcraft-balance-cache')
os.environ.setdefault('MPLCONFIGDIR','/tmp/warcraft-balance-matplotlib')
import matplotlib;matplotlib.use('Agg')
import matplotlib.pyplot as plt
fig,axes=plt.subplots(2,2,figsize=(11,7));samples=range(1,201)
for ax,(title,raw,field)in zip(axes.flat,[('Mana shield coefficient','ANms','Nms1'),('Critical multiplier','AOcr','Ocr2'),('Blink cooldown, seconds','AEbl','acdn'),('Divine Shield duration, seconds','AHds','adur')]):
 ax.plot(samples,[ability(raw,field,r,BEFORE)for r in samples],label='0.21',color='#c34c4c');ax.plot(samples,[ability(raw,field,r)for r in samples],label='0.22',color='#287fa8');ax.set_title(title);ax.set_xlabel('Skill rank');ax.grid(alpha=.25);ax.legend()
fig.tight_layout();fig.savefig(OUT/'Balance-curves.png',dpi=140);fig.savefig(OUT/'Balance-curves.svg');plt.close(fig)
print('AUDIT:',len(rows),'skills;',checked,'adjacent rank transitions;',len(gaps),'without an observable change')
if gaps:print(gaps[:30]);raise SystemExit(1)
