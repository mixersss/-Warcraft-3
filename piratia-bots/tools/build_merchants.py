"""Project actual BuyPage merchant locations, including field shops, from owner files."""
import argparse
import json
import re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]


def discover(npc_file,script_directory,encoding='gb18030'):
    functions={}
    for path in sorted(Path(script_directory).glob('NpcScript*.lua')):
        source=path.read_bytes().decode(encoding,errors='replace')
        starts=list(re.finditer(r'(?m)^function\s+(\w+)\s*\(',source))
        for i,m in enumerate(starts):
            body=source[m.start():starts[i+1].start() if i+1<len(starts) else len(source)]
            functions[m[1]]='\n'.join(line.split('--')[0] for line in body.splitlines())
    shops=[]
    for line in Path(npc_file).read_bytes().decode(encoding,errors='replace').splitlines():
        columns=line.split('\t')
        if not columns[0].isdigit() or len(columns)<13:continue
        body=functions.get(columns[11],'')
        entries=re.findall(r'Text\s*\(\s*1\s*,\s*"[^"]*"\s*,\s*(\w+)',body)
        if 'BuyPage' not in entries:continue
        offers=[int(v) for v in re.findall(r'(?:Weapon|Defence|Other)\s*\(\s*(\d+)\s*\)',body)]
        if not offers:continue
        position=list(map(int,columns[5].split(',')))
        if len(position)!=2 or any(not 0<=v<409600 for v in position):raise ValueError('Invalid merchant position')
        shops.append({'position':position,'menu':entries.index('BuyPage'),'name':columns[1],
                      'offers':offers,'region':columns[8]})
    return shops


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('npc_file',type=Path);parser.add_argument('script_directory',type=Path)
    parser.add_argument('--map',default='garner');parser.add_argument('--encoding',default='gb18030')
    args=parser.parse_args();path=ROOT/'assets/town-services.json'
    data=json.loads(path.read_text());shops=discover(args.npc_file,args.script_directory,args.encoding)
    if not shops:raise ValueError('No verified BuyPage merchants found; keep existing catalog')
    data['shops'][args.map]=shops
    path.write_text(json.dumps(data,ensure_ascii=False,separators=(',',':'))+'\n')
    print(args.map,len(shops),'verified merchants (city and field)')


if __name__=='__main__':main()
