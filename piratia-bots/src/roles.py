"""Persistent per-character class intent, constrained by native race/job compatibility."""
import json
import os
import threading
from pathlib import Path
from population import ALLOWED
from classic_wire import ProtocolError

LOCK = threading.Lock()
FIRST_JOB = {8:1,9:1,12:2,13:5,14:5,16:4}
PROMOTION = {1:'Swordsman Promotion',2:'Hunter Promotion',5:'Herbalist Promotion',4:'Explorer Promotion'}
LABELS = {8:'чемпион',9:'крестоносец',12:'стрелок',13:'целитель',14:'колдун',16:'покоритель морей'}


class RoleStore:
    def __init__(self, path):
        self.path = Path(path)

    def resolve(self, character, body, actual_job):
        if body not in ALLOWED or actual_job is None:
            raise ProtocolError('Неизвестная раса/профессия; выбор классов остановлен.')
        with LOCK:
            records = {}
            if self.path.exists():
                records = json.loads(self.path.read_text(encoding='utf-8'))
                if not isinstance(records,dict) or len(records)>400:
                    raise ProtocolError('Некорректный реестр классов ботов.')
                if any(not isinstance(v,dict) or set(v)!={'body','target_job'}
                       or type(v['body']) is not int or type(v['target_job']) is not int
                       or v['target_job'] not in ALLOWED.get(v['body'],()) for v in records.values()):
                    raise ProtocolError('В реестре обнаружена несовместимая раса и класс.')
            saved = records.get(character)
            if saved:
                target = saved['target_job']
                if saved['body']!=body or actual_job not in (0,FIRST_JOB[target],target):
                    raise ProtocolError('Сохранённый класс не совпадает с персонажем; автоматическая смена запрещена.')
            else:
                if len(records)>=400:
                    raise ProtocolError('Реестр уже содержит 400 персонажей.')
                allowed = [job for job in ALLOWED[body] if actual_job in (0,FIRST_JOB[job],job)]
                if not allowed:
                    raise ProtocolError('Для существующей профессии нет настроенного пути развития.')
                counts = {job:sum(p['target_job']==job for p in records.values()) for job in allowed}
                target = min(allowed,key=lambda job:(counts[job]/(100 if job==8 else 60),job))
                records[character] = {'body':body,'target_job':target}
                self.path.parent.mkdir(parents=True,exist_ok=True)
                temporary = self.path.with_suffix('.tmp')
                temporary.write_text(json.dumps(records,indent=2)+'\n',encoding='utf-8')
                os.replace(temporary,self.path)
            return {'body':body,'target_job':target,'first_job':FIRST_JOB[target],
                    'promotion':PROMOTION[FIRST_JOB[target]],'label':LABELS[target]}
