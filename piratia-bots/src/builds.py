"""Eight owner builds, persisted separately from identities/classes and earned stats."""
import hashlib,json,os,threading
from pathlib import Path
from classic_wire import ProtocolError

PROFILES={
 'crusader_speed':{'job':9,'label':'воитель: ловкость/сила, цель210скорости','weights':{27:3,25:1},'speed_target':210},
 'sharpshooter_precision':{'job':12,'label':'стрелок: полная точность','weights':{26:1}},
 'sharpshooter_speed':{'job':12,'label':'стрелок: ловкость/точность','weights':{27:1,26:1}},
 'cleric_spirit':{'job':13,'label':'целитель: полный дух','weights':{29:1}},
 'sealmaster_balanced':{'job':14,'label':'колдунья: дух/телосложение','weights':{29:2,28:1}},
 'voyager_spirit':{'job':16,'label':'мореплаватель: дух, немного телосложения','weights':{29:4,28:1}},
 'voyager_tank':{'job':16,'label':'мореплаватель: телосложение, немного духа','weights':{28:4,29:1}},
 'champion_tank':{'job':8,'label':'чемпион: телосложение, немного силы','weights':{28:4,25:1}},
}
DEFAULT={p['job']:key for key,p in reversed(list(PROFILES.items()))}
LOCK=threading.Lock()

def profile(job,identity=None):
    identity=identity or DEFAULT.get(job)
    p=PROFILES.get(identity)
    return p if p and p['job']==job else None

def observed_speed(values):
    # Owner AttrCalculate converts final speed to native attack interval:
    # ATTR_ASPD = floor(100000 / Aspd_final). Includes current gear/states.
    interval=values.get(42)
    return 100000/interval if type(interval) in (int,float) and interval>0 else None

class BuildStore:
    def __init__(self,path):self.path=Path(path)
    def resolve(self,character,job,allow_novice_change=False):
        key=hashlib.sha256(character.encode('utf-8')).hexdigest()
        with LOCK:
            data=json.loads(self.path.read_text()) if self.path.exists() else {'version':1,'profiles':{}}
            records=data.get('profiles')
            if data.get('version')!=1 or not isinstance(records,dict) or len(records)>500:
                raise ProtocolError('Неверный реестр билдов; распределение очков остановлено.')
            if any(not isinstance(v,dict) or set(v)!={'job','build'} or profile(v['job'],v['build']) is None for v in records.values()):
                raise ProtocolError('В реестре неизвестный билд; распределение очков остановлено.')
            saved=records.get(key)
            if saved and saved['job']==job:return saved['build']
            if saved and not allow_novice_change:
                raise ProtocolError('Билд не совпадает с сохранённым классом. Автоматический сброс запрещён.')
            candidates=[k for k,v in PROFILES.items() if v['job']==job]
            if not candidates:raise ProtocolError('Неизвестный класс для билда.')
            counts={c:sum(r['build']==c for k,r in records.items() if k!=key) for c in candidates}
            smallest=min(counts.values());available=sorted(c for c in candidates if counts[c]==smallest)
            chosen=available[int(key[:8],16)%len(available)]
            records[key]={'job':job,'build':chosen}
            self.path.parent.mkdir(parents=True,exist_ok=True)
            temporary=self.path.with_suffix('.tmp');temporary.write_text(json.dumps(data,indent=2)+'\n')
            os.replace(temporary,self.path)
            return chosen
