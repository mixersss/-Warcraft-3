"""Native helper records for the user-supplied3.5 techniques; independent safe scheduling."""
def abilities():
 common=[('aher',0,0),('aite',0,0),('alev',0,1),('abpy',0,-11),('amcs',0,0,1,0),('acdn',2,0.,1,0),('acas',2,0.,1,0),('aran',2,2000.,1,0),('areq',3,''),('aani',3,'')]
 out=[('AHtb','R35k',common+[('anam',3,'Кунай с печатью3.5'),('Htb1',2,100.,1,1),('adur',2,2.,1,0),('ahdu',2,2.,1,0),('amat',3,'Kunai.MDX'),('amsp',0,1400),('atar',3,'air,ground,organic,enemy,neutral',1,0)])]
 image=[('anam',3,'Копирование теневого клона3.5'),('aher',0,0),('aite',0,0),('alev',0,4),('abpy',0,-11),('areq',3,'')]
 for n in range(1,5):image += [('Iild',2,[.15,.18,.21,.24][n-1],n,1),('Iilw',2,15.,n,2),('adur',2,30.,n,0),('ahdu',2,30.,n,0),('amcs',0,0,n,0),('acdn',2,0.,n,0),('acas',2,0.,n,0),('aran',2,700.,n,0),('atar',3,'ground,air,friend,self',n,0)]
 out.append(('AIil','R35i',image))
 out.append(('Amls','R35s',common+[('anam',3,'Групповое теневое подражание'),('mls1',2,45.,1,1),('aran',2,600.,1,0),('adur',2,9.,1,0),('ahdu',2,7.,1,0),('atar',3,'enemies,organic',1,0),('alig',3,''),('abuf',3,'Bmlc,Bmlt',1,0)]))
 choke=[('anam',3,'Поддерживаемое удушение3.5'),('aher',0,0),('alev',0,3),('abpy',0,-11),('alig',3,''),('aefs',3,''),('aefl',3,'')]
 for n in range(1,4):choke.extend([('mls1',2,30.,n,1),('adur',2,3.+2*n,n,0),('ahdu',2,3.+n,n,0),('amcs',0,0,n,0),('acdn',2,0.,n,0),('acas',2,0.,n,0),('aran',2,550.,n,0),('atar',3,'enemies,organic',n,0),('abuf',3,'Bmlc,Bmlt',n,0)])
 out.append(('Amls','R35c',choke))
 for _,_,mods in out:mods.extend([('aefs',3,''),('aefl',3,'')])
 return out
