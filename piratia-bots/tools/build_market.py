"""Project owner table facts; prices are configurable pilot references, not market quotations."""
import argparse,json,re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def main():
 p=argparse.ArgumentParser();p.add_argument('resource',type=Path);r=p.parse_args().resource
 rows={}
 for line in (r/'ItemInfo.txt').read_text(encoding='gb18030').splitlines():
  a=line.split('\t')
  if not a[0].isdigit() or len(a)<94:continue
  identity=int(a[0]);kind=int(a[10]);name=a[1]
  category=('refining' if identity==885 else 'kal' if identity==3457 else 'rune' if identity in range(3425,3434) or identity in (3455,3456) else 'gem' if kind in (49,50) else 'sealed' if 'sealed' in name.lower() and kind<30 else 'gear' if kind in range(1,30) else None)
  if not category or a[16]!='1':continue
  price=max(1,int(a[22]));premium=category in ('kal','rune','gem','refining')
  reference=({'kal':250000,'rune':50000,'refining':25000,'gem':50000}.get(category,max(50,price//2)))
  rows[identity]={'name':name,'kind':kind,'category':category,'level':int(a[24]),'reference_price':reference,'stack':int(a[20])}
 script=(r/'script/MisScript/NpcScript01.lua').read_text(encoding='gb18030')
 body=script.split('function r_talk47',1)[1].split('\nfunction ',1)[0]
 rune_goals=[]
 for level,ids in ((30,(3425,3426)),(40,(3428,3429)),(50,(3427,3430)),(60,(3455,3456))):
  for identity in ids:
   assert re.search(r'HasItem,\s*'+str(identity)+r',\s*10',body)
  rune_goals.append({'level':level,'items':{str(i):10 for i in ids},'source':'NpcScript01.lua:r_talk47; Gannon rune exchange'})
 data={'rune_exchange_goals':rune_goals,'source':'Owner ItemInfo.txt: type[10], trade[16], price[22], level[24]; skillinfo241 and Sk_Script_Btjn3296',
       'prices_are_pilot_policy_not_live_quotes':True,'stall_skill':241,'stall_book':3296,'session_seconds':2400,
       'city_limit':10,'reserve_gold':1000,'purchase_fraction':.20,'items':rows,
       'goals':{'refining':{'identity':885,'keep':2,'min_level':30},'kal':{'identity':3457,'keep':5,'min_level':50}},
       'black_market':'Recognize sealed gear and save runes; NPC barter and dungeon rune farming not automated in this release.'}
 (ROOT/'assets/market-items.json').write_text(json.dumps(data,ensure_ascii=False,separators=(',',':'))+'\n')
 print(len(rows),'tradeable item facts')
if __name__=='__main__':main()
