"""Refresh only owner-shop labels/prices in the already-derived item database."""
import csv
import json
import sqlite3
from pathlib import Path

ROOT=Path(__file__).resolve().parent

def main():
    catalog=json.loads((ROOT/'catalog.json').read_text())
    facts=json.loads((ROOT/'item-database.json').read_text())
    owners={item['id']:(shop['key'],item['price']) for shop in catalog['shops'] for item in shop['items']}
    overrides={i['id']:i['price'] for i in catalog['price_overrides']}
    for row in facts:
        shop,price=owners.get(row['id'],('',None))
        row['shop']=shop;row['owner_price']=overrides.get(row['id'],price)
    (ROOT/'item-database.json').write_text(json.dumps(facts,ensure_ascii=False,indent=2)+'\n')
    fields=list(facts[0])
    with (ROOT/'item-database.csv').open('w',encoding='utf-8-sig',newline='') as stream:
        writer=csv.DictWriter(stream,fieldnames=fields,lineterminator='\n');writer.writeheader();writer.writerows(facts)
    with sqlite3.connect(ROOT/'item-database.sqlite3') as connection:
        connection.executemany('UPDATE items SET shop=?,owner_price=? WHERE id=?',[(r['shop'],r['owner_price'],r['id']) for r in facts])
    stats=json.loads((ROOT/'database-summary.json').read_text())
    stats['shops']={s['key']:len(s['items']) for s in catalog['shops']}
    stats['catalog_revision']=catalog['catalog_revision']
    (ROOT/'database-summary.json').write_text(json.dumps(stats,ensure_ascii=False,indent=2)+'\n')

if __name__=='__main__':main()
