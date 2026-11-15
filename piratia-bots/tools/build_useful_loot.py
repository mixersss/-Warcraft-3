"""Audit useful tradeable loot against owner item facts, native shops and mob drops."""
import argparse,json,collections
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def build(resource):
    load=lambda p:json.loads((ROOT/p).read_text())
    base=load('assets/market-items.json')['items'];life=load('assets/life-items.json');mobs=load('assets/world-mobs.json')['monsters']
    city=json.loads((ROOT.parent/'piratia-city-shops/native/catalog.json').read_text())
    forge={i['id'] for shop in city['shops'] if shop['key']=='forge' for i in shop['items']}
    drops=collections.defaultdict(list)
    for identity,row in mobs.items():
        for item in row['drops']:drops[item].append(int(identity))
    from build_junk import VALUABLE
    rows={}
    for line in (resource/'ItemInfo.txt').read_bytes().decode('gb18030','replace').splitlines():
        a=line.split('\t')
        if not a[0].isdigit() or len(a)<94 or a[16]!='1':continue
        identity=int(a[0]);category=base.get(str(identity),{}).get('category')
        if identity in forge and not category:category='forge_material'
        if identity in VALUABLE and not category:category='craft_material'
        if identity in drops and str(identity) in life['books']:category='skill_book'
        if identity in drops and identity in (1847,227,2312,276,277,278,279,280):category='care_supply'
        if not category or identity==1000:continue
        meta=dict(base.get(str(identity),{}))
        meta.update(name=a[1],kind=int(a[10]),category=category,level=int(a[24]),stack=int(a[20]),drop_species=sorted(drops[identity]),
                    reference_price=meta.get('reference_price',max(50,int(a[22])*2)),useful_for={'gear':'снаряжение и классовые улучшения','scroll':'карты и поиск сокровищ','blueprint':'рецепты производства','refining':'улучшение снаряжения','kal':'материалы ковки','rune':'родной обмен рун','gem':'вставка самоцветов','sealed':'снаряжение с распечатыванием','forge_material':'материал из проверенного каталога форжа','skill_book':'изучение родного навыка','care_supply':'уход за феей или восстановление персонажа','craft_material':'сохранённый материал развития: кристаллы, жемчуг, камни и компоненты; применение зависит от рецепта или обмена'}[category])
        rows[str(identity)]=meta
    data={'version':1,'scope':'Tradeable known gear/scrolls/blueprints/runes/gems/native forge goods and observed dropped books/care supplies. Not an exhaustive interpretation of every game mechanic.',
          'patchouli_destination':'ordinary NPC500','category_counts':dict(collections.Counter(r['category'] for r in rows.values())),
          'items':rows,'drop_backed_item_count':sum(bool(r['drop_species']) for r in rows.values())}
    (ROOT/'assets/useful-loot.json').write_text(json.dumps(data,ensure_ascii=False,separators=(',',':'))+'\n')
    print('Useful saleable items',len(rows),data['category_counts'],'drop-backed',data['drop_backed_item_count'])
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('resource',type=Path);build(p.parse_args().resource)
