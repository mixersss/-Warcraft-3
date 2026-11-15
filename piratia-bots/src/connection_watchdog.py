"""Recover a silent transport after own actions; idle listening alone is not an error."""
class ConnectionWatchdog:
    def __init__(self):self.received=None;self.action_baseline=0;self.silence=0;self.reason=''
    def expired(self,now,wire,action_count):
        received=getattr(wire,'last_receive_at',None)
        if type(received) not in (int,float):return False
        if received!=self.received:self.received=received;self.action_baseline=action_count
        self.silence=max(0,now-received)
        if self.silence<120 or action_count-self.action_baseline<2 or getattr(wire,'buffer',None):return False
        self.reason='120секунд без входящих байтов после игровых действий; требуется обычное переподключение'
        return True
    def summary(self):return {'seconds_without_received_bytes':round(self.silence,1),'reason':self.reason,'minimum_silence_seconds':120,'minimum_new_actions':2,'position_or_inventory_not_fabricated':True}
