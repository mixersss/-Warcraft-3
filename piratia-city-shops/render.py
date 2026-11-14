"""Generate original paged NPC dialogs with per-NPC prices; no copied server Lua."""
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parent

def render(catalog):
    if catalog.get('version')!=1 or len(catalog.get('shops',[]))!=5:raise ValueError('Invalid shop catalog')
    for shop in catalog['shops']:
        ids=set()
        for item in shop['items']:
            if (type(item['id']) is not int or not 1<=item['id']<=65535 or item['id'] in ids
                or type(item['price']) is not int or item['price'] not in (1000,2000,5000,10000,20000,50000)):
                raise ValueError('Invalid product or owner price')
            ids.add(item['id']);item['name'].encode('ascii')
    lines=['-- OWNER_CITY_SHOPS_V1_BEGIN','OwnerMarketCatalog = {}']
    for shop in catalog['shops']:
        key=json.dumps(shop['key']);lines.append('OwnerMarketCatalog['+key+'] = {')
        for i in shop['items']:
            lines.append(' [%d] = {price=%d, name=%s},'%(i['id'],i['price'],json.dumps(i['name'],ensure_ascii=True)))
        lines.append('}')
    lines.append((ROOT/'purchase.lua').read_text())
    for shop in catalog['shops']:
        lines.append('function '+shop['function']+'()')
        chunks=[shop['items'][i:i+9] for i in range(0,len(shop['items']),9)]
        if len(chunks)>250:raise ValueError('Too many dialog pages')
        lines.append(' for p=1,%d do Page[p]={count=0}; for k=1,12 do Page[p][k]={} end end'%len(chunks))
        for page,chunk in enumerate(chunks,1):
            lines.append(' Talk(%d,%s)'%(page,json.dumps(shop['name']+' - '+str(page)+'/'+str(len(chunks))+'; buy one item per click.')))
            for item in chunk:
                label=item['name'][:58]+' - '+str(item['price'])+'G'
                lines.append(' Text(%d,%s,OwnerMarketBuy,%s,%d)'%(page,json.dumps(label),json.dumps(shop['key']),item['id']))
            if page>1:lines.append(' Text(%d,"Previous",JumpPage,%d)'%(page,page-1))
            if page<len(chunks):lines.append(' Text(%d,"Next",JumpPage,%d)'%(page,page+1))
            lines.append(' Text(%d,"Close",CloseTalk)'%page)
        lines.append('end')
    lines.append('-- OWNER_CITY_SHOPS_V1_END')
    return ('\n'.join(lines)+'\n').encode('ascii')

if __name__=='__main__':print(render(json.loads((ROOT/'catalog.json').read_text())).decode('ascii'))
