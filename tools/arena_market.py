"""Two shared central stores. Classic native item effects; no periodic handles."""
import json
from pathlib import Path

def rows(root):return json.loads((Path(root)/'map/arena-items.json').read_text())
def abilities(root):
    common=[('alev',0,1),('aher',0,0),('aite',0,1),('amcs',0,0,1,0)]
    soldier='ground,air,friend,nonhero,nonstructure,vuln,invu'
    return [
      ('ANss','Frss',common+[('acdn',2,25.,1,0)]),
      ('AOae','Frsp',common+[('Oae1',2,0.,1,1),('Oae2',2,.15,1,2),('aare',2,900.,1,0),('atar',3,soldier,1,0),('abuf',3,'BOae',1,0)]),
      ('AIrr','Frat',common+[('Roa1',2,.60,1,1),('aare',2,750.,1,0),('adur',2,15.,1,0),('ahdu',2,15.,1,0),('acdn',2,45.,1,0),('atar',3,soldier,1,0)]),
      ('AIda','Frdf',common+[('Idef',0,16,1,1),('aare',2,750.,1,0),('adur',2,20.,1,0),('ahdu',2,20.,1,0),('acdn',2,45.,1,0),('atar',3,soldier,1,0)]),
      ('AIra','Frrs',common+[('Ihps',0,4000,1,1),('Imps',0,1800,1,2),('aare',2,650.,1,0),('acdn',2,45.,1,0),('atar',3,'ground,air,friend,self,nonstructure,vuln,invu',1,0)]),
      ('AIvu','Friv',common+[('adur',2,3.,1,0),('ahdu',2,3.,1,0),('acdn',2,75.,1,0)])]
