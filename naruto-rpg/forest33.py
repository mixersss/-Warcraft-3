"""Missing forest Kabuto ability copied from the supplied 4.2i source."""
import json
from pathlib import Path
ROOT=Path(__file__).parent
def abilities():
 row=next(r for r in json.loads((ROOT/'src/forest33-source.json').read_text())['abilities'] if r['newId']=='A018')
 return [(row['oldId'],row['newId'],[(m['id'],m['variableType'],m['value'],m['levelOrVariation'],m['dataPointer'])for m in row['modifications']]+[('aefs',3,'',0,0),('aefl',3,'',0,0)])]
