"""Build broad ordinary loot sale policy from checked-in owner table projections."""
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
# Previously audited ordinary trophies and plant ingredients, including type31.
EXPLICIT_COMMON = (1573, 1574, 1575, 1577, 1579, 1585, 1590, 1591, 1592, 1593, 1594, 1595, 1596, 1597, 1598, 1599, 1600, 1601, 1602, 1603, 1604, 1605, 1606, 1607, 1608, 1609, 1610, 1611, 1613, 1614, 1615, 1616, 1617, 1618, 1620, 1622, 1623, 1624, 1625, 1627, 1628, 1629, 1653, 1676, 1678, 1679, 1690, 1691, 1692, 1704, 1725, 1777, 1779, 1838, 1844, 3116, 3117, 3118, 3129, 3130, 3372, 4314, 4315, 4316, 4317, 4318, 4319, 4322, 4325, 4328, 4332, 4396, 4397, 4398, 4399, 4400, 4401, 4402, 4404, 4406, 4408, 4410, 4414, 4483, 4484, 4485, 4486, 4506, 4508)
# Development materials / known valuable drops stay out of ordinary NPC sales.
VALUABLE = {1612,1619,1621,1631,1634,1636,1640,1641,1746,1754,
            3363,3364,3367,3380,3387,3388,3391}
SPECIAL_WORDS = ('blueprint','skill book','hairstyle book','scroll','chest')

def build(assets):
    types=json.loads((assets/'items.json').read_text())['types']
    life=json.loads((assets/'life-items.json').read_text())
    regions=json.loads((assets/'regions.json').read_text())
    market=json.loads((assets/'market-items.json').read_text())['items']
    drops={i for region in regions.values() for farm in region['farms'].values() for i in farm['drops']}
    # Broad common monster materials, rather than a handful of low-level IDs.
    candidates=set(EXPLICIT_COMMON)
    candidates.update(i for i in drops if types.get(str(i))==41)
    # Audited continuous common trophy block, including later mobs not yet routed.
    candidates.update(i for i in range(4319,4543) if types.get(str(i))==41)
    protected=VALUABLE | set(map(int,life['books'])) | set(map(int,life['chests'])) | set(map(int,market))
    items={}
    for identity in sorted(candidates-protected):
        key=str(identity);name=life['names'][key]
        if any(word in name.casefold() for word in SPECIAL_WORDS):continue
        items[key]={'name':name,'table_price':life['prices'][key]}
    return {'source':'Owner table projections: all ordinary type41 monster drops in regions plus audited common trophy block4319..4542 and explicit common type31 plants. Exclude development materials, books, blueprints, chests and market goods. Active quest ingredients and modified instances protected at runtime; server sets sale value.',
            'policy':'broad_ordinary_loot', 'keep_each':0,'items':items}

def main():
    data=build(ROOT/'assets')
    (ROOT/'assets/junk-items.json').write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
    print(len(data['items']),'ordinary loot IDs eligible for NPC sale')

if __name__=='__main__':main()
