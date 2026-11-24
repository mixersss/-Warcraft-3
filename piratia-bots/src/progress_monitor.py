"""Observe native progress, not packet counts or changing console labels."""
import math

class ProgressMonitor:
    def __init__(self):
        self.signature=None;self.anchor=None;self.since=None;self.next_recovery=0
        self.recoveries=0;self.reason='';self.idle_seconds=0
        self.work_signature=None;self.work_since=None;self.last_target=None;self.last_target_hp=None
        self.farm_search=None;self.farm_search_advanced_at=None
    def fast_tick(self,now,policy):
        w=policy.world;own=w.own;target=w.entities.get(policy.target)
        signature=(tuple(own.values.get(i) for i in (0,15,4,7,8,13)),
                   tuple(sorted((i,s.get('level')) for i,s in w.skills.items())),
                   tuple(sorted(own.equipment.items())),
                   tuple((s,i.identity,i.count) for s,i in sorted(w.bag.items())))
        key=(target.identity,target.handle) if target else None
        hp=target.values.get(1) if target else None
        damage=(key is not None and key==self.last_target and hp is not None
                and self.last_target_hp is not None and hp<self.last_target_hp)
        self.last_target,self.last_target_hp=key,hp
        if signature!=self.work_signature or damage or self.work_since is None:
            self.work_signature=signature;self.work_since=now;self.since=now
        point=own.position
        if self.anchor is None or math.dist(point,self.anchor)>=100:
            self.anchor=point;self.since=now
        self.idle_seconds=max(0,now-(self.since if self.since is not None else now))
        if policy.transaction_busy():self.reason='ждёт штатное подтверждение операции';return
        goal=policy.search_goal
        started=policy.search_started
        deadline=policy.search_deadline
        travel=getattr(policy,'hunt_travel',None)
        if travel and getattr(travel,'mine_approach',lambda:False)() and travel.approach_clock:
            goal=policy.nav.nearest(travel.plan['position'],3)
            started=travel.target_started
            deadline=travel.approach_clock[1]
        pending=policy.nav.pending_farm_search(goal) if goal and hasattr(policy.nav,'pending_farm_search') else None
        if pending!=self.farm_search:
            self.farm_search=pending;self.farm_search_advanced_at=now
        if (self.idle_seconds<60 and now-self.work_since<180) or now<self.next_recovery:return
        if goal and now<deadline:
            if pending and now-started<300 and now-self.farm_search_advanced_at<15:
                self.reason='поиск пути к лагерю продолжает продвигаться';return
            if policy.move_goal==goal and self.idle_seconds<15:
                self.reason='движется к лагерю по подтверждённому пути';return
        if any(getattr(f,'context',None) or getattr(f,'pending',None) for f in
               (policy.town,policy.vendor,policy.career,policy.story,policy.adventure) if f):
            self.reason='ожидает ограниченную операцию НПС';return
        if policy.resting and now-self.work_since<120:
            self.reason='восстанавливает HP/SP перед аварийной охотой';return
        self.recoveries+=1;self.next_recovery=now+60
        if hasattr(policy.nav,'needs_recovery') and policy.nav.needs_recovery(point):
            policy.offmesh_next=min(policy.offmesh_next,now)
            self.reason='аварийный план: выход на сушу, затем охота';return
        if policy.action_open and policy.last_sent_kind in (1,2):policy.stop_action()
        if policy.search_goal:policy.goal_blacklist[policy.search_goal]=now+60
        policy.pending_action=None;policy.move_goal=None
        policy.drop_target(now,avoid=True);policy.clear_zone()
        if hasattr(policy.nav,'cancel_pending'):policy.nav.cancel_pending()
        policy.stuck=5;policy.next_recovery=now;policy.next_action=now
        policy.learning.until=0;policy.learning.next_idle_probe=now
        policy.resting=False;policy.mana_resting=False
        if policy.economy:policy.economy.emergency_until=now+120
        for key in ('market','career','story','adventure'):policy.task_budget.paused[key]=now+60
        self.since=self.work_since=now
        self.reason='аварийная охота: прерывает бесполезный маршрут и заново выбирает доступную цель'
    def tick(self,now,policy):
        w=policy.world;own=w.own
        if not own or not own.alive:self.since=now;return
        if getattr(policy,'fast_progression',False):self.fast_tick(now,policy);return
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
