"""Build derived item facts and native-shop catalogs; never copy original tables."""
import argparse,csv,hashlib,json,sqlite3,struct,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parent
BOT_ROOT=ROOT.parents[1]/'piratia-bots'
if not BOT_ROOT.is_dir():BOT_ROOT=ROOT.parents[1]
sys.path.insert(0,str(BOT_ROOT/'tools'))
from build_mechanics import table_rows

def records(raw):
 stride=struct.unpack_from('<I',raw)[0]
 if stride!=868 or (len(raw)-4)%stride:raise ValueError('Unknown item record format')
 result={}
 for pos in range(4,len(raw),stride):
  identity=struct.unpack_from('<I',raw,pos+4)[0]
  if identity!=struct.unpack_from('<I',raw,pos+108)[0] or identity in result:raise ValueError('Invalid item record identity')
  result[identity]={'name':raw[pos+112:pos+192].split(b'\0')[0].decode('cp1251',errors='replace').strip(),
                    'kind':struct.unpack_from('<h',raw,pos+308)[0],'price':struct.unpack_from('<i',raw,pos+320)[0]}
 return result

def build(resource,client_bin):
 rows={int(r[0]):r for r in table_rows(resource/'ItemInfo.txt')};client=records(client_bin.read_bytes())
 knowledge=json.loads((BOT_ROOT/'assets/mechanics.json').read_text());meta=knowledge['item_bases']
 original=json.loads((ROOT.parent/'catalog.json').read_text());shops=original['shops']
 apparel=[i for i in rows if 5000<=i<6000 or int(rows[i][10])==44]
 shops[0]['items']=[{'id':i,'name':rows[i][1].strip(),'price':50000,'kind':int(rows[i][10]),'hooks':meta[str(i)]['hooks']} for i in sorted(apparel)]
 forge=sorted(set([i for i,r in rows.items() if int(r[10]) in (47,49,50)]+[448,453,454,455,456,890,891,1018,1020,1022,1023,1024,2403,2404,2562,2563,2564,2565,2566,2567,3074,3075,3883,3884,3907]))
 shops[2]['items']=[{'id':i,'name':rows[i][1].strip(),'price':5000,'kind':int(rows[i][10]),'hooks':meta[str(i)]['hooks']} for i in forge]
 shops[1]['items'].append({'id':609,'name':rows[609][1].strip(),'price':300000,'kind':int(rows[609][10]),'hooks':meta['609']['hooks']})
 for item in shops[3]['items']:
  if item['id'] in (4602,4603,4604):item['price']=int(rows[item['id']][22])
 for shop in shops:
  for item in shop['items']:
   i=item['id']
   if i not in client or client[i]['kind']!=int(rows[i][10]):raise ValueError('Client/server mismatch '+str(i))
   item.update(name=rows[i][1].strip(),name_ru=client[i]['name'],stack=int(rows[i][20]),kind=int(rows[i][10]))
 catalog={'version':2,'shops':shops,'apparel_rule':'exact server can_fusion_item_main permits appearance IDs5000..5999; all existing records in range plus wings type44',
  'native_shop':True,'prices_scope':'global selected item prices on server and client; all other fields preserved',
  'source_hashes':{'server_iteminfo':hashlib.sha256((resource/'ItemInfo.txt').read_bytes()).hexdigest(),'client_iteminfo':hashlib.sha256(client_bin.read_bytes()).hexdigest()},
  'native_windows_verified':False,'price_overrides':[{'id':1000,'kind':31,'price':1000,'npc_buyback':500,'name_ru':'Чертеж Пачкули','name_en':'Blurry Blueprint','name':'Blurry Blueprint','stack':99}]}
 (ROOT/'catalog.json').write_text(json.dumps(catalog,ensure_ascii=False,indent=2)+'\n')
 assignments={i['id']:(s['key'],i['price']) for s in shops for i in s['items']};assignments[1000]=('',1000);allfacts=[]
 for i in sorted(set(rows)|set(client)):
  r=rows.get(i);c=client.get(i);assignment=assignments.get(i)
  allfacts.append({'id':i,'name_ru':c['name'] if c else '', 'name_en':r[1].strip() if r else '',
   'kind':int(r[10]) if r else c['kind'],'level':int(r[24]) if r else None,
   'bodies':r[23] if r else '', 'jobs':r[25] if r else '', 'server_price':int(r[22]) if r else None,
   'client_price':c['price'] if c else None,'owner_price':assignment[1] if assignment else None,
   'shop':assignment[0] if assignment else '', 'in_server':bool(r),'in_client':bool(c),
   'effect_hooks':','.join(meta.get(str(i),{}).get('hooks',[])),
   'apparel_id_range':5000<=i<6000,'wings':int(r[10])==44 if r else c['kind']==44})
 (ROOT/'item-database.json').write_text(json.dumps(allfacts,ensure_ascii=False,indent=2)+'\n')
 with (ROOT/'item-database.csv').open('w',encoding='utf-8-sig',newline='') as f:
  writer=csv.DictWriter(f,fieldnames=list(allfacts[0]),lineterminator='\n');writer.writeheader();writer.writerows(allfacts)
 db=ROOT/'item-database.sqlite3';db.unlink(missing_ok=True)
 with sqlite3.connect(db) as connection:
  fields=list(allfacts[0]);integer={'id','kind','level','server_price','client_price','owner_price','in_server','in_client','apparel_id_range','wings'}
  connection.execute('CREATE TABLE items ('+','.join(f+' '+('INTEGER' if f in integer else 'TEXT')+(' PRIMARY KEY' if f=='id' else '') for f in fields)+')')
  connection.executemany('INSERT INTO items VALUES ('+','.join('?' for _ in fields)+')',[[r[f] for f in fields] for r in allfacts])
  connection.execute('CREATE INDEX item_shop ON items(shop)')
  connection.execute('CREATE VIEW available_shop_items AS SELECT * FROM items WHERE shop<>\'\' AND in_server=1 AND in_client=1')
 stats={'all_items':len(allfacts),'server_items':len(rows),'client_items':len(client),'client_only':sum(not r['in_server'] for r in allfacts),
        'shops':{s['key']:len(s['items']) for s in shops},'banana_name_matches':[r['id'] for r in allfacts if 'банан' in r['name_ru'].lower() or 'banana' in r['name_en'].lower()]}
 (ROOT/'database-summary.json').write_text(json.dumps(stats,ensure_ascii=False,indent=2)+'\n');print(stats)
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('resource',type=Path);p.add_argument('client_bin',type=Path);a=p.parse_args();build(a.resource,a.client_bin)
