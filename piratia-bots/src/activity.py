"""Earned-progress watchdog: finish fights, avoid optional-task loops and farm feasible targets."""
class Activity:
 def __init__(self):
  self.baseline=None;self.last_progress=None;self.force_until=0;self.fallbacks=0
 def update(self,now,level,xp,kills,quests,protected=False):
  signature=(level,xp,kills,quests)
  if self.baseline is None:self.baseline=signature;self.last_progress=now
  elif signature!=self.baseline:self.baseline=signature;self.last_progress=now
  if protected:
   self.last_progress=now;return
  if now-self.last_progress>=120:
   self.force_until=now+180;self.last_progress=now;self.fallbacks+=1
 def hunting(self,now):return now<self.force_until
 def summary(self):return {'productive_progress_fallbacks':self.fallbacks,'farm_focus_until':self.force_until}
