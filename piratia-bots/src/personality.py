"""Persistent deterministic traits; civil refusals and choices, no external AI."""
import hashlib,random
KINDS=(('доброжелательный',.95),('общительный',.8),('деловой',.6),('ворчливый',.35),('одиночка',.15),('шутник',.75))
class Personality:
 def __init__(self,seed):
  self.seed=int.from_bytes(hashlib.sha256((str(seed)+':personality').encode()).digest()[:8],'big')
  self.rng=random.Random(self.seed);self.kind,self.help_chance=KINDS[self.seed%len(KINDS)]
 def help(self,busy,hp):
  if hp<.7:return False,'Сам еле держусь. Сначала восстановлюсь.'
  if busy:return False,'Сейчас не могу: своё дело ещё не закончил.'
  if self.rng.random()>self.help_chance:return False,('Разбирайся пока сам, у меня свои планы.' if self.kind in ('ворчливый','одиночка') else 'В этот раз не пойду, хочу закончить своё дело.')
  return True,'Иду, попробую помочь. Только не тащи ещё одну толпу!'
