"""Extract numeric item types/equipment constraints; no descriptions/models copied."""
import argparse
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]


def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('item_info',type=Path);args=p.parse_args()
 types,gear={},{}
 for line in args.item_info.read_bytes().decode('gb18030',errors='replace').splitlines():
  a=line.split('\t')
  if not a[0].isdigit() or len(a)<65:continue
  identity,kind=int(a[0]),int(a[10]);types[identity]=kind
  weapon=1<=kind<=10
  if not weapon and kind not in (11,22,23,24):continue
  links=[int(v) for v in a[28].split(',')]
  if weapon:links=[9] if 9 in links else [6] if 6 in links else []
  if not links or any(v not in (2,3,4,6,9) for v in links):continue
  displaces=[int(v) for v in a[29].split(',') if v.isdigit() and int(v) in (2,3,4,6,9)]
  def value(text):
   try:return max(0,float(text.split(',')[0]))
   except ValueError:return 0
  score=value(a[60])+value(a[61]) if weapon else value(a[62])*4+value(a[63])*.05
  gear[identity]={'level':int(a[24]),'jobs':[int(v) for v in a[25].split(',')],
                  'links':links,'bodies':[b for b in (1,2,3,4) if a[3+b].strip('0')],
                  'displaces':displaces or [links[0]],
                  'score':score}
 (ROOT/'assets/items.json').write_text(json.dumps({'types':types,'gear':gear},separators=(',',':'))+'\n')
 print('Extracted numeric item types:',len(types),'gear:',len(gear))


if __name__=='__main__':main()
