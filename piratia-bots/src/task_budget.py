"""Bound optional town detours by actual position/progress; never cancel a confirmed stall."""
import math

class TaskBudget:
    def __init__(self):self.rows={};self.paused={};self.yields=0
    def allow(self,key,now):return now>=self.paused.get(key,0)
    def track(self,key,feature,used,position,now):
        if not used:self.rows.pop(key,None);return False
        if getattr(feature,'context',None) or getattr(feature,'pending',None):return True
        old=self.rows.get(key)
        if old is None:self.rows[key]=[now,now,position];return True
        if math.dist(position,old[2])>=100:old[1]=now;old[2]=position
        if now-old[1]<35 and now-old[0]<180:return True
        self.rows.pop(key,None);self.paused[key]=now+180;self.yields+=1
        return False
