"""One authorised, resumable 200 -> 300 expansion; never replace the saved prefix."""
import hashlib
import json
import os
import shutil
import threading
from collections import Counter
from pathlib import Path
from population import ALLOWED
from roles import RoleStore, LOCK as ROLE_LOCK


def atomic_json(path,value):
    temporary=path.with_suffix('.tmp')
    temporary.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    os.replace(temporary,path)


def prefix_digest(state,count):
    # Ignore only secondary-password migration, never login identity/secret/SID.
    prefix=[{k:r.get(k) for k in ('account','character','password_dpapi')}
            for r in state['bots'][:count]]
    return hashlib.sha256(json.dumps([state.get('windows_sid'),prefix],sort_keys=True).encode()).hexdigest()


def balanced_additions(records,count):
    """Fill the least represented compatible classes, then balance possible bodies.

    Existing records are never changed. Carsise only supports champion, so equal
    body increments would entrench an unequal class distribution.
    """
    jobs=Counter(r['target_job'] for r in records.values())
    bodies=Counter(r['body'] for r in records.values());plans=[]
    choices=sorted({j for allowed in ALLOWED.values() for j in allowed})
    for _ in range(count):
        job=min(choices,key=lambda j:(jobs[j],j))
        body=min((b for b,allowed in ALLOWED.items() if job in allowed),key=lambda b:(bodies[b],b))
        plans.append({'body':body,'target_job':job});jobs[job]+=1;bodies[body]+=1
    return plans


class PopulationGrowth:
    BASE=200
    TARGET=300

    def __init__(self,data):
        self.data=Path(data);self.path=self.data/'population-growth.json';self.lock=threading.Lock()
        self.state=json.loads((self.data/'bot-local.json').read_text(encoding='utf-8-sig'))
        if self.state.get('version')!=1 or not isinstance(self.state.get('bots'),list):
            raise RuntimeError('Неверный формат сохранённой популяции; расширение остановлено.')
        count=len(self.state['bots'])
        if not self.BASE<=count<=self.TARGET:
            raise RuntimeError('Расширение рассчитано на сохранённых 200 ботов до фиксированных 300. Верни полную data.')
        if self.path.exists():
            self.ledger=json.loads(self.path.read_text(encoding='utf-8'))
            self.validate()
        elif count==self.TARGET:
            # A complete legacy population is protected, not treated as unfinished.
            self.ledger=None
        elif count==self.BASE:
            roles=RoleStore(self.data/'bot-roles.json').read_records()
            names=[r['character'] for r in self.state['bots']]
            if len(set(names))!=self.BASE or any(name not in roles for name in names):
                raise RuntimeError('Для расширения нужен реестр классов всех нынешних 200 ботов. Запусти их прежним Start-Bot.cmd и сохрани полную data.')
            backup=self.data/'backups'/'before-growth-300'
            # Never overwrite the pre-expansion snapshot, including after a crash.
            backup.mkdir(parents=True,exist_ok=True)
            for source in self.data.glob('*.json'):
                dest=backup/source.name
                if not dest.exists():shutil.copy2(source,dest)
            plans=balanced_additions({n:roles[n] for n in names},self.TARGET-self.BASE)
            self.ledger={'version':1,'base_count':self.BASE,'target_count':self.TARGET,
                         'prefix_digest':prefix_digest(self.state,self.BASE),
                         'plans':plans,'confirmed_indices':[]}
            atomic_json(self.path,self.ledger)
        else:
            raise RuntimeError('Неполное расширение без журнала. Верни population-growth.json из той же data; новые боты не созданы.')

    def validate(self):
        d=self.ledger
        if (d.get('version')!=1 or d.get('base_count')!=self.BASE or d.get('target_count')!=self.TARGET
                or d.get('prefix_digest')!=prefix_digest(self.state,self.BASE)):
            raise RuntimeError('Журнал расширения не совпадает с нынешними 200 ботами; замена запрещена.')
        plans=d.get('plans',[]);confirmed=d.get('confirmed_indices',[])
        if (len(plans)!=100 or any(not isinstance(p,dict) or set(p)!={'body','target_job'}
                or p['target_job'] not in ALLOWED.get(p['body'],()) for p in plans)
                or not isinstance(confirmed,list) or len(set(confirmed))!=len(confirmed)
                or any(type(i) is not int or not 201<=i<=len(self.state['bots']) for i in confirmed)):
            raise RuntimeError('Некорректный журнал расширения; новые боты не созданы.')

    @property
    def existing_count(self):return self.BASE if self.ledger else self.TARGET

    def permits_creation(self,index):
        return bool(self.ledger and self.BASE<index<=self.TARGET
                    and index not in self.ledger['confirmed_indices'])

    def assign(self,bots):
        current=json.loads((self.data/'bot-local.json').read_text(encoding='utf-8-sig'))
        if len(bots)!=self.TARGET or prefix_digest(current,self.BASE)!=prefix_digest(self.state,self.BASE):
            raise RuntimeError('Сохранённые аккаунты изменились во время расширения. Подключение остановлено.')
        for before,after in zip(current['bots'],bots):
            if before['account']!=after['account'] or before['character']!=after['character']:
                raise RuntimeError('Порядок сохранённых аккаунтов изменился; создание остановлено.')
        if self.ledger:
            store=RoleStore(self.data/'bot-roles.json')
            with ROLE_LOCK:
                records=store.read_records()
                for index,plan in enumerate(self.ledger['plans'],self.BASE):
                    name=bots[index]['character'];saved=records.get(name)
                    if saved is not None and saved['body']!=plan['body']:
                        raise RuntimeError('Новый профиль не совпадает с журналом расширения; автоматическая замена запрещена.')
                    if saved is None:records[name]=plan.copy() # Keep legitimate novice rebalancing/earned intent.
                store.save_records(records)
        for index,bot in enumerate(bots,1):
            bot['preserve_existing']=not self.permits_creation(index)
            if self.ledger and index>self.BASE:
                bot['creation_body']=self.ledger['plans'][index-self.BASE-1]['body']
            if self.permits_creation(index):bot['_growth_confirmation']=(self,index)

    def confirm(self,index):
        # Called only after native enter-world succeeded. No fake character grant.
        with self.lock:
            if self.permits_creation(index):
                updated=dict(self.ledger,confirmed_indices=sorted(self.ledger['confirmed_indices']+[index]))
                atomic_json(self.path,updated)
                self.ledger=updated
