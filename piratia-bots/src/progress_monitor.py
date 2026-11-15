"""Observe native progress, not packet counts or changing console labels."""
import math

class ProgressMonitor:
    def __init__(self):
        self.signature=None;self.anchor=None;self.since=None;self.next_recovery=0
        self.recoveries=0;self.reason='';self.idle_seconds=0
    def tick(self,now,policy):
        w=policy.world;own=w.own
        if not own or not own.alive:self.since=now;return
        target=w.entities.get(policy.target)
        signature=(own.values.get(0),own.values.get(15),own.values.get(1),own.values.get(2),
                   tuple(own.values.get(i) for i in (4,7,8,13)),tuple(sorted((i,s.get('level')) for i,s in w.skills.items())),
                   tuple(sorted(own.equipment.items())),tuple((s,i.identity,i.count,i.energy) for s,i in sorted(w.bag.items())),
                   target.identity if target else None,target.values.get(1) if target else None)
        point=own.position
        moved=self.anchor is None or math.dist(point,self.anchor)>=100
        if self.signature!=signature or moved or self.since is None:
            self.signature=signature;self.since=now
            if moved:self.anchor=point
        self.idle_seconds=max(0,now-self.since)
        if policy.transaction_busy():self.reason='подтверждённая торговля/обмен';return
        if self.idle_seconds<45 or now<self.next_recovery:return
        self.next_recovery=now+45;self.recoveries+=1
        if hasattr(policy.nav,'needs_recovery') and policy.nav.needs_recovery(point):
            policy.offmesh_next=min(policy.offmesh_next,now)
            self.reason='застрял на кромке; проверяет короткий выход и собственный билет';return
        if policy.resting:
            policy.resting=False;policy.mana_resting=False
            self.reason='нет восстановления HP/SP; завершает бесполезный отдых';return
        if target and target.alive:
            self.reason='цель без прогресса; штатный контроль боя сменит её';return
        # Do not discard an in-flight NPC/item/paid operation. Its controller
        # owns the deadline and the inventory confirmation.
        if any(getattr(f,'context',None) or getattr(f,'pending',None) for f in
               (policy.town,policy.vendor,policy.career,policy.story,policy.adventure) if f):
            self.reason='ожидает ограниченный обмен с НПС';return
        if policy.search_goal:policy.goal_blacklist[policy.search_goal]=now+120
        policy.move_goal=None;policy.stuck=5;policy.next_recovery=now;policy.next_action=now
        policy.learning.until=0;policy.learning.next_idle_probe=now
        self.reason='45секунд без результата: меняет маршрут и переоценивает охоту'
    def summary(self):return {'seconds_without_native_progress':round(self.idle_seconds,1),'recovery_decisions':self.recoveries,'reason':self.reason,'chat_never_pauses_play':True}
