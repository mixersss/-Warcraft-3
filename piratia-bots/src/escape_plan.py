"""One minute without an exit: owned ticket first, bounded native-position resync."""
import threading,math

class RecoveryResync(ConnectionError):pass

class RescueDirectory:
    def __init__(self):self.lock=threading.Lock();self.rows={}
    def claim(self,name,map_name,point,now):
        with self.lock:
            old=self.rows.get(name)
            if old and old[0]==map_name and math.dist(old[1],point)<1000 and now-old[2]<600:return False
            self.rows[name]=(map_name,tuple(point),now)
            if len(self.rows)>1024:
                oldest=min(self.rows,key=lambda n:self.rows[n][2]);self.rows.pop(oldest,None)
            return True

class EscapePlan:
    def __init__(self,name,directory):
        self.name,self.directory=name,directory;self.resyncs=0;self.reason='';self.trigger_seconds=60
    def tick(self,now,policy):
        since=policy.offmesh_since
        if since is None or now-since<self.trigger_seconds:return False
        if policy.stuck_return.tick(now,policy):self.reason=policy.stuck_return.reason;return True
        if policy.stuck_return.reason=='билет требует полные HP и SP':
            policy.sitting.tick(now,policy,True);self.reason='запасной план: восстанавливает HP/SP для билета'
            if now-since<120:return True
        if policy.stuck_return.reason=='нет собственного билета для возврата' or now-since>=120:
            w=policy.world
            if self.directory.claim(self.name,w.map,w.own.position,now):
                self.resyncs+=1;self.reason='выход или возврат не подтверждён: повторный вход для свежих координат сервера'
                raise RecoveryResync(self.reason)
            self.reason='билет отсутствует; повторный вход здесь уже проверен, ищет физический выход; нужен доступный проход'
        else:self.reason=policy.stuck_return.reason or 'ожидает подтверждение запасного возврата'
        return False
    def summary(self):return {'trigger_after_seconds':60,'native_position_resyncs':self.resyncs,'same_area_resync_cooldown_seconds':600,'state':self.reason,'uses_only_owned_tickets':True,'local_position_not_changed':True}
