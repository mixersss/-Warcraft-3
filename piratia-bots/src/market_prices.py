"""Bounded price guides from confirmed exchanges; never changes inventory or gold."""
import json,threading,time
from pathlib import Path

class MarketPrices:
    def __init__(self,path):
        self.path=Path(path);self.lock=threading.Lock();self.rows={};self.dirty=False;self.last_save=0;self.save_errors=0
        self.write_lock=threading.Lock();self.saving=False;self.revision=0;self.saved_revision=-1
        try:
            data=json.loads(self.path.read_text())
            if data.get('version')==1:
                self.rows={k:v for k,v in data.get('items',{}).items() if k.isdigit() and isinstance(v,dict)
                    and type(v.get('guide')) is int and 0<v['guide']<=2000000000
                    and type(v.get('observations')) is int and 0<v['observations']<=1000000000}
        except (OSError,ValueError,TypeError,AttributeError):pass

    def guide(self,identity,base):
        with self.lock:
            price=self.rows.get(str(identity),{}).get('guide',base)
            return max(1,min(base*2,max(base//2,price))) if base else 0

    def confirmed(self,identity,unit_price,base):
        if not base or not 0<unit_price<=2000000000:return
        with self.lock:
            row=self.rows.get(str(identity),{'guide':base,'observations':0})
            observed=max(base//2,min(base*2,unit_price))
            row={'guide':max(1,round(row['guide']*.8+observed*.2)),
                 'observations':row['observations']+1}
            self.rows[str(identity)]=row;self.dirty=True;self.revision+=1
        self.save()

    def save(self,force=False):
        now=time.monotonic()
        with self.lock:
            if not self.dirty or (not force and (self.saving or now-self.last_save<60)):return
            rows={key:dict(value) for key,value in self.rows.items()};revision=self.revision
            self.last_save=now;self.saving=True
        def write():
            try:
                # Neither disk writes nor filesystem/antivirus delays hold the
                # shared guide lock or block another bot's decision thread.
                with self.write_lock:
                    if revision>=self.saved_revision:
                        self.path.parent.mkdir(parents=True,exist_ok=True);temp=self.path.with_suffix('.tmp')
                        temp.write_text(json.dumps({'version':1,'items':rows},separators=(',',':')))
                        temp.replace(self.path);self.saved_revision=revision
                with self.lock:
                    if self.revision==revision:self.dirty=False
            except OSError:
                with self.lock:self.save_errors+=1
            finally:
                with self.lock:self.saving=False
        if force:write()
        else:
            try:threading.Thread(target=write,name='piratia-price-save',daemon=True).start()
            except RuntimeError:
                with self.lock:self.saving=False;self.save_errors+=1
