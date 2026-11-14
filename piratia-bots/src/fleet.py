"""Bounded, credential-free live population status shared by the worker threads."""
from collections import Counter
import json
import os
import threading
import time
from pathlib import Path


class Fleet:
    def __init__(self, requested, path):
        self.requested,self.path=requested,Path(path)
        self.rows={}
        self.lock=threading.Lock()
        self.peak=0

    def update(self,index,**values):
        allowed={'position','phase','tactic','connected','map','level','job','body','state','hp','max_hp','moves','attacks','equips','quests','target_job','experience','start_experience','start_level','hunt_style','farm_models'}
        if values.keys()-allowed:raise ValueError('Unsupported population field')
        with self.lock:
            self.rows.setdefault(index,{}).update(values)
            self.peak=max(self.peak,sum(bool(r.get('connected')) for r in self.rows.values()))

    def snapshot(self):
        with self.lock:
            rows={str(i):dict(r) for i,r in self.rows.items()}
            peak=self.peak
        active=[r for r in rows.values() if r.get('connected')]
        return {'updated_unix':int(time.time()),'requested':self.requested,
                'connected':len(active),'peak_connected':peak,
                'cities':dict(Counter(r.get('map','unknown') for r in active)),
                'phases':dict(Counter(r.get('phase','unknown') for r in active)),
                'tactics':dict(Counter(r.get('tactic','unknown') for r in active)),
                'bodies':dict(Counter(r.get('body',0) for r in active)),
                'levels':dict(Counter(r.get('level',0) for r in active)),
                'actual_professions':dict(Counter(r.get('job') for r in active)),
                'with_profession':sum(type(r.get('job')) is int and r['job']!=0 for r in active),
                'with_progress_this_session':sum((r.get('level') or 0)>(r.get('start_level') or 9999)
                    or (r.get('level')==r.get('start_level') and (r.get('experience') or 0)>(r.get('start_experience') or 0)) for r in active),
                'target_jobs':dict(Counter(r.get('target_job',0) for r in active)), 'bots':rows}

    def write(self):
        data=self.snapshot()
        temporary=self.path.with_suffix('.tmp')
        temporary.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
        os.replace(temporary,self.path)
        return data
