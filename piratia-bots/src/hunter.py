"""First bounded PvE policy: passive weak mobs, normal attack, retreat and rest."""
import math
import struct
import time
import random
import json
from pathlib import Path
NORMAL_ATTACKS={int(k):v["range_cm"] for k,v in json.loads((Path(__file__).resolve().parents[1]/"assets/normal-attacks.json").read_text())["skills"].items()}
from classic_wire import sequence
from classic_wire import ProtocolError, Reader
from progression import Progression
from social import Social, ChatBudget
from world import World, HP, MAX_HP, LV, ATTACK_DISTANCE


def distance(a, b):
    return math.hypot(a[0]-b[0], a[1]-b[1])


def action_header(actor, number, kind):
    return struct.pack('>IIB', actor, number, kind)


def movement(actor, number, points):
    if not 2 <= len(points) <= 32:
        raise ValueError('Expected 2..32 movement points')
    return action_header(actor, number, 1) + sequence(b''.join(struct.pack('<ii', *p) for p in points))


def normal_attack(actor, number, fight, skill, target, handle, position):
    # Native BeginAction 0x5198b0: chMove=2, fight ID, path, skill, world ID, handle.
    # In-range attacks still include two equal points, as the normal UI does.
    points = sequence(struct.pack('<iiii', *position, *position))
    return action_header(actor, number, 2) + bytes([2, fight & 255]) + points + struct.pack('>III', skill, target, handle)


class Hunter:
    def __init__(self, world, navigation, send, report, tell=print, seed=None):
        self.world, self.nav, self.send = world, navigation, send
        self.report, self.tell = report, tell
        self.home = world.own.position
        self.sequence, self.fight = 1, 0
        self.attack_failure_seen=0;self.last_attack_stop=-1e9;self.attack_move_revision=-1
        self.end_action_requests=0
        self.action_open=False
        self.pending_action=None;self.clock=time.monotonic();self.queued_actions=self.flushed_actions=0
        self.last_sent_sequence=None;self.sent_action_counts={}
        self.last_sent_kind=None;self.last_attack_target=None
        self.active_fight_waits=0
        self.rejected_target_releases=0
        self.motion_anchor=None;self.motion_progress_at=None
        self.move_endpoint=None;self.move_packet=None
        self.assist_target=None;self.helper=None
        self.target = None
        self.shared_target = False
        self.opportunity_model=None;self.opportunity_targets=0;self.last_target_at=None
        self.next_action = 0
        self.mode = 'observe'
        self.mode_since=self.clock
        self.next_console_state=0;self.last_console_mode=None
        self.resting = False
        self.cancel_pending = False
        self.waypoint = 0
        self.moves = self.attacks = self.kills = 0
        self.blacklist = {}
        self.last_position = self.home
        self.stuck = 0
        self.last_target_hp = None
        self.target_since = 0
        self.started = time.monotonic()
        self.rng = random.Random(str(seed or world.own.identity))
        self.attack_interval = self.rng.uniform(.35, .5)
        self.route = list(range(len(navigation.waypoints)))
        self.rng.shuffle(self.route)
        self.adventure = None
        self.loot = None
        self.equipment = None
        self.skills = None
        self.recovery = None
        self.chests=self.town=self.party=self.career=self.story=self.market=self.travel=self.vendor=None
        from task_budget import TaskBudget
        self.task_budget=TaskBudget()
        self.death_episodes=0;self.confirmed_revivals=0;self.last_death_at=None;self.last_return_at=None
        self.dead_since = None
        self.revive_requests = 0
        self.death_attempts = 0
        self.next_revive = 0
        self.region = None
        self.move_goal = None
        self.move_sent = -1e9
        self.move_until = 0
        self.move_revision = -1
        self.move_waits = 0
        self.owner=str(seed or world.own.identity)
        self.coordination=None
        self.target_key=None
        self.combat_since=None
        self.last_damage_at=0
        self.approach_probe=False
        self.approach_angle=self.rng.uniform(0,math.tau)
        self.recoveries=self.no_damage_retargets=self.busy_targets=0
        self.next_recovery=0
        self.search_goal=None
        self.search_started=0
        self.search_deadline=0
        self.goal_blacklist={}
        self.tactic='quests'
        self.quest_phase='quests'
        self.tactic_schedule=None
        self.optional_quests=True
        from activity import Activity
        self.activity=Activity();self.offmesh_next=0;self.offmesh_requests=0
        self.offmesh_batch=0
        from farm_plan import HuntLearning
        self.learning=HuntLearning(self.owner)
        self.farm_plan_key=None;self.farm_plan_changes=0
        self.starter_search_since=None
        self.refresh_class_intent=None
        self.inventory_blocked=False
        self.inventory_blocker=None
        self.raising_travel_funds=False
        from sitting import Sitting
        self.sitting=Sitting(world)

    def update_tactic(self,now):
        if not self.tactic_schedule or not self.world.own:return
        current=self.world.entities.get(self.target)
        busy=bool(current and current.alive) or self.resting
        for feature in (self.adventure,self.career,self.story,self.town,self.equipment,self.skills,self.chests,self.market):
            if feature and (getattr(feature,'context',None) or getattr(feature,'pending',None)):busy=True
        mandatory=(self.world.own.values.get(4)==0 and self.world.own.values.get(0,1)>=9)
        if self.career and self.career.eligible():mandatory=True
        phase=self.tactic_schedule.tick(now,busy=busy,mandatory=mandatory)
        if phase!=self.quest_phase and not busy:self.clear_zone()
        self.quest_phase=phase
        self.optional_quests=phase=='quests'
        if self.adventure:self.adventure.tactic=phase

    def drop_target(self,now=None,avoid=False):
        had_target=self.target is not None or self.target_key is not None
        if self.learning.active and self.learning.active['id']==self.target:self.learning.active=None
        if self.target and avoid and now is not None:
            self.blacklist[self.target]=now+45
            if len(self.blacklist)>256:self.blacklist.pop(next(iter(self.blacklist)))
        if self.coordination:self.coordination.release(self.owner)
        self.target=None
        self.shared_target=False
        self.opportunity_model=None
        self.target_key=None
        self.combat_since=None
        self.last_target_hp=None
        if had_target:self.move_goal=None
        self.approach_probe=False

    def clear_zone(self):
        if self.coordination:self.coordination.leave_zone(self.owner)
        self.search_goal=None

    def available_spot(self,point,now):
        return not any(e.identity!=self.world.own_id and e.control==1 and e.alive
                       and distance(point,self.world.position(now,e.identity))<100
                       for e in self.world.entities.values())

    def attack_reach(self,target):
        # ATTR_ADIS is not the normal skill's range (unarmed 100, sword150, bow900).
        base=NORMAL_ATTACKS.get(self.world.default_skill,min(100,self.world.own.values.get(ATTACK_DISTANCE,100)))
        return max(40,base+self.world.own.radius+target.radius-20)

    def quest_models(self):
        """Only actual active kill/drop objectives may share local target leases."""
        models=set()
        if self.adventure and self.adventure.farm():
            models.update(self.adventure.desired_models())
        for feature in (self.career,self.story):
            if feature:
                desired=feature.desired_models()
                if isinstance(desired,(set,list,tuple)):models.update(desired)
        return models

    def approach(self,target,reach,now,shared=False):
        center=self.world.position(now,target.identity)
        radius=max(70,reach-65)
        options=[]
        for i in range(12):
            angle=self.approach_angle+i*math.tau/12
            point=(round(center[0]+math.cos(angle)*radius),round(center[1]+math.sin(angle)*radius))
            point=self.nav.nearest(point,1)
            if (point and distance(point,center)<=reach-20
                    and self.available_spot(point,now)):
                options.append(point)
        # Prefer free endpoints, but nearby players must not block every attack
        # position for a shared quest mob. Geometry/path checks still apply.
        if not options and (shared or self.shared_target or target.model in self.quest_models()):
            for i in range(12):
                angle=self.approach_angle+i*math.tau/12
                point=self.nav.nearest((round(center[0]+math.cos(angle)*radius),
                                        round(center[1]+math.sin(angle)*radius)),1)
                if point and distance(point,center)<=reach-20:options.append(point)
        for point in sorted(set(options),key=lambda pt:distance(self.position(now),pt)):
            if self.nav.path(self.position(now),point):return point
        return None

    def recover_path(self,now):
        self.drop_target(now,avoid=True)
        if self.search_goal:self.goal_blacklist[self.search_goal]=now+45
        self.clear_zone()
        self.stuck=0
        self.motion_anchor=self.position(now);self.motion_progress_at=now
        self.recoveries+=1
        self.next_recovery=now+8
        self.move_sent=-1e9
        origin=self.position(now)
        # Small checked detour, never a coordinate teleport or a forced SQL move.
        for radius in (200,400,600):
            for i in range(8):
                angle=self.approach_angle+(self.recoveries+i)*math.tau/8
                point=self.nav.nearest((round(origin[0]+radius*math.cos(angle)),
                                        round(origin[1]+radius*math.sin(angle))),1)
                if point and self.available_spot(point,now) and self.nav.path(origin,point):
                    self.move_to(point,now)
                    self.next_action=now+1
                    self.change('обход препятствия; повторный поиск цели')
                    return
        self.next_action=now+2
        self.change('ожидание свободного прохода')

    def change(self, value):
        if self.mode != value:
            self.mode = value;self.mode_since=self.clock


    def stop_action(self):
        self.send(7,b'');self.end_action_requests+=1;self.action_open=False

    def send_action(self,body):
        self.send(6,body);self.action_open=True
        self.last_sent_sequence=int.from_bytes(body[4:8],'big')
        kind=str(body[8]);self.sent_action_counts[kind]=self.sent_action_counts.get(kind,0)+1
        self.last_sent_kind=body[8]
        if body[8]==21:self.action_open=False
        if body[8]==2:
            self.attacks+=1
            self.motion_anchor=None;self.motion_progress_at=None;self.stuck=0
            self.last_attack_target=struct.unpack('>III',body[-12:])[1:]
            target=self.world.entities.get(self.last_attack_target[0])
            if target:self.learning.begin(self.world,target,self.clock)
        elif body[8]==1:
            self.move_packet=self.last_sent_sequence
            self.move_endpoint=struct.unpack('<ii',body[-8:])

    def emit(self, body):
        if self.action_stopped():
            self.action_open=False
        if self.action_open:
            self.stop_action()
            # EndAction requests a stop; native CAction ends on a later game tick.
            self.pending_action=(body,self.clock+.15,self.clock+1.0,self.world.stop_revision)
            self.queued_actions+=1
        else:
            self.send_action(body)
        self.sequence=(self.sequence+1)&0xffffffff

    def flush_action(self,now):
        if not self.pending_action:return False
        body,earliest,fallback,stop_revision=self.pending_action
        ack=(self.world.stop_revision!=stop_revision and self.action_stopped())
        if now<earliest or (not ack and now<fallback):return True
        self.pending_action=None
        kind=body[8];number=int.from_bytes(body[4:8],'big')
        own=self.world.own
        if not own or not own.alive:return True
        if kind==1 and self.move_goal:
            points=self.nav.segment(self.position(now),self.move_goal)
            if len(points)<2:return True
            body=movement(own.identity,number,points)
            self.move_sent=now;self.move_revision=self.world.move_revision
            speed=max(100,min(own.values.get(44,480),3000))
            self.move_until=now+sum(distance(a,b) for a,b in zip(points,points[1:]))/speed
        elif kind==2:
            if not self.world.default_skill:return True
            _,identity,handle=struct.unpack('>III',body[-12:])
            target=self.world.entities.get(identity)
            if not target or not target.alive or target.handle!=handle:return True
            if self.combat_since is not None and now-self.last_damage_at>=14:return False
            if distance(self.position(now),self.world.position(now,identity))>self.attack_reach(target):return True
            body=normal_attack(own.identity,number,body[10],self.world.default_skill,identity,handle,self.position(now))
        self.send_action(body);self.flushed_actions+=1
        self.next_action=max(self.next_action,now+.2)
        return True

    def position(self,now):
        return self.world.position(now)

    def action_stopped(self):
        if self.last_sent_sequence is None or self.world.stop_packet_number!=self.last_sent_sequence:return False
        kind=self.world.stop_packet_kind
        # A combined move+attack emits a movement INRANGE notification before
        # its fight starts. Only SKILL_SRC termination ends that whole action.
        return kind is None or (self.last_sent_kind==1 and kind==1) or (self.last_sent_kind==2 and kind==3)

    def move_to(self, goal, now):
        self.clock=now
        if self.pending_action:return True
        own = self.world.own
        origin = self.position(now)
        same_goal = self.move_goal and distance(self.move_goal,goal)<200
        if now-self.move_sent<.65:
            return True
        if same_goal:
            if self.world.move_revision==self.move_revision and now-self.move_sent<1.5:
                self.move_waits+=1
                return True  # Wait for server acceptance; never extrapolate a requested route.
            if (self.world.move_revision!=self.move_revision and self.world.move_state==0
                    and (self.world.move_packet_number is None or self.world.move_packet_number==self.move_packet)
                    and now<self.move_until+.5):
                self.move_waits+=1
                return True
        path = self.nav.segment(origin,goal)
        if len(path)<2:
            return False
        points=path  # Checked collinear cells are represented by native turn points.
        travelled=sum(distance(a,b) for a,b in zip(points,points[1:]))
        speed=max(100,min(own.values.get(44,480),3000))
        self.emit(movement(own.identity,self.sequence,points))
        self.moves+=1
        self.move_goal,self.move_sent,self.move_until=tuple(goal),now,now+travelled/speed
        self.move_revision=self.world.move_revision
        self.next_action=now+.15
        # Count elapsed lack of server-backed progress, not fast calls while an
        # action is still being accepted. Five near-identical requests were
        # enough to send the old policy back into city detours repeatedly.
        if self.motion_anchor is None or distance(origin,self.motion_anchor)>=100:
            self.motion_anchor=origin;self.motion_progress_at=now;self.stuck=0
        elif now-self.motion_progress_at>=10:
            self.stuck=5
        self.last_position=origin
        return True

    def fight_running(self,target,now):
        """A normal attack is a server-side repeating action, not one click/hit."""
        if self.last_sent_kind!=2 or self.last_attack_target!=(target.identity,target.handle):return False
        if self.world.failed_actions>self.attack_failure_seen:return False
        if self.action_stopped():return False
        # Let the server complete wind-up and subsequent swings. No-progress
        # recovery below still bounds the wait; never cancel a productive fight.
        return now-self.last_damage_at<6

    def mandatory_work(self):
        return (self.world.own.values.get(4)==0 and self.world.own.values.get(LV,0)>=9) or bool(self.career and self.career.eligible())

    def opportunity_models(self):
        if self.starter_models():return self.starter_models()
        if not self.region:return self.farm_models()
        return self.learning.choose(self.region,self.world.own,self.clock,fallback=True,hold=bool(self.target))

    def farm_models(self):
        if self.starter_models():return self.starter_models()
        if not self.region:return (71,75)
        return self.learning.choose(self.region,self.world.own,self.clock,hold=bool(self.target))

    def starter_models(self):
        # Owner's CharacterInfo: Forest Spirit 103 is level 3, Argent only.
        preferred=(self.region and self.world.map=='garner'
                        and '103' in self.region['farms'] and self.world.own.values.get(LV,1)<=3
                        and not self.learning.blocked(103,self.clock)
                        and not self.learning.rows)
        if not preferred:return set()
        if self.starter_search_since is None:self.starter_search_since=self.clock
        return {103} if self.clock-self.starter_search_since<90 else set()

    def planned_models(self):
        if self.starter_models():return self.starter_models()
        if self.activity.hunting(self.clock) and not self.mandatory_work():return set(self.opportunity_models())
        for feature in (self.career,self.story if self.wants_story() else None):
            if feature:
                models=feature.desired_models()
                if isinstance(models,(set,list,tuple)) and models:return set(models)
        # A tutorial object alone is not a farming objective. Only an active
        # kill/drop task may override the current earned level's farming tier.
        if self.adventure and self.adventure.farm():
            models=self.adventure.desired_models()
            if isinstance(models,(set,list,tuple)) and models:
                tutorial=self.adventure.active() in self.adventure.tutorial_ids
                # Optional starter chores must not pin a growing character to
                # level-three mobs for the whole pre-profession progression.
                useful=not tutorial or not self.region or any(
                    self.region['farms'].get(str(m),{}).get('level',0)>=self.world.own.values.get(LV,1)-3
                    for m in models)
                if useful:return set(models)
        return set(self.farm_models())

    def refresh_farm_plan(self):
        key=(self.world.map,self.world.own.values.get(LV,1),tuple(sorted(self.planned_models())))
        if key!=self.farm_plan_key:
            if self.farm_plan_key is not None:
                self.farm_plan_changes+=1
                self.clear_zone();self.waypoint=0
                if not self.target:self.move_goal=None
            self.farm_plan_key=key

    def allow_visit(self,point,now,mandatory=False):
        return not self.coordination or self.coordination.visit(self.owner,self.world.map,point,now,mandatory)

    def task(self,key,feature,callback,now):
        if self.inventory_blocked and key in ('adventure','career','story','market','town'):return False
        if self.raising_travel_funds and key in ('adventure','career','story','market','town'):return False
        if self.helper and self.helper.source is not None and not self.mandatory_work():return False
        target=self.world.entities.get(self.target)
        if target and target.alive:return False  # Finish the chosen fight before another errand.
        if key=='adventure' and not self.mandatory_work() and feature:
            destination=feature.choose_destination()
            point=feature.npcs.get(destination)
            if isinstance(point,(tuple,list)) and len(point)==2 and distance(self.position(now),point)>1500:return False
        if self.activity.hunting(self.clock) and key!='vendor' and not (key in ('adventure','career') and self.mandatory_work()):return False
        if not feature or (key!='vendor' and not self.task_budget.allow(key,now)):return False
        point=None
        if self.coordination and feature and not getattr(feature,'context',None):
            if key=='adventure' and not feature.farm():point=feature.npcs.get(feature.choose_destination())
            elif key in ('career','story') and not feature.desired_models():point=feature.quest.get('position')
        if isinstance(point,(tuple,list)) and len(point)==2 and not self.allow_visit(point,now,self.mandatory_work()):
            return False
        used=callback()
        if not used and point and self.coordination:self.coordination.leave_visit(self.owner)
        allowed=self.task_budget.track(key,feature,used,self.position(now),now,progress_only=key=='vendor')
        if used and not allowed:
            if key=='vendor':
                self.task_budget.paused.pop(key,None)
                feature.finish_sale(now)
            elif key=='town':feature.finish(now,180)
            elif key=='market':feature.next_scan=now+180
            elif hasattr(feature,'next_visit'):feature.next_visit=now+180
            self.move_goal=None
        return allowed

    def wants_story(self):
        return (self.optional_quests or bool(self.market and self.market.needs_life_study())) and not self.activity.hunting(self.clock)

    def target_score(self,entity,now):
        # Prefer reachable nearby fights, weakened targets and useful level-appropriate XP.
        own=self.world.own;maximum=max(1,entity.values.get(MAX_HP,entity.values.get(HP,1)))
        health=entity.values.get(HP,maximum)/maximum
        gap=max(0,own.values.get(LV,1)-entity.values.get(LV,1))
        preference=self.learning.scores.get(entity.model,0)
        return distance(self.position(now),self.world.position(now,entity.identity))+health*200+gap*20-preference*300

    def eligible(self, entity, now, models=None):
        own = self.world.own
        models=set(models) if models is not None else ({self.world.entities[self.assist_target].model} if self.assist_target in self.world.entities else self.planned_models())
        if entity.identity==self.target and self.opportunity_model:models=set(models)|{self.opportunity_model}
        if self.region and self.world.map!='garner' and own.values.get(LV,1)<=3:return False
        maximum_level = min(45,own.values[LV]) if self.region or self.adventure else min(2,own.values[LV]+1)
        if self.starter_models() and not self.assist_target and models==self.starter_models():
            models=self.starter_models();maximum_level=3
        elif self.region:
            maximum_level=max([maximum_level]+[self.region['farms'][str(m)]['level'] for m in models if str(m) in self.region['farms']])
        return (entity.control == 5 and (not self.assist_target or entity.identity==self.assist_target) and entity.model in models and entity.alive
                and 0 < entity.values.get(LV, 9999) <= maximum_level
                and entity.handle != 0 and distance(entity.position, self.home) <= (600000 if self.region else 45000 if self.adventure else 22000)
                and self.blacklist.get(entity.identity, 0) < now and not self.learning.dangerous(entity.model,now))

    def tick(self,now=None):
        nav=self.nav;incremental=getattr(nav,'incremental',False) is True
        from route_search import RoutePending
        previous,since=self.mode,self.mode_since
        if incremental:nav.begin_turn()
        try:return self._tick(now)
        except RoutePending:self.change('планирует безопасный маршрут; продолжает принимать сеть')
        finally:
            if incremental:nav.end_turn()
            # Ignore transient states within one decision in both diagnostics
            # and the Windows console. Report the final state, not every branch.
            if self.mode==previous:self.mode_since=since
            if self.mode!=self.last_console_mode and (self.clock>=self.next_console_state or self.mode.startswith('персонаж погиб')):
                self.tell('Состояние бота: '+self.mode)
                self.last_console_mode=self.mode;self.next_console_state=self.clock+30

    def _tick(self, now=None):
        now = time.monotonic() if now is None else now
        self.clock=now
        own = self.world.own
        if own and (own.values.get(HP,1)<=0 or own.state>=5):
            self.learning.observe(self.world,now)
            self.pending_action=None;self.action_open=False
            self.sitting.reset()
            if self.market and self.market.state in ('opening','selling','closing'):self.market.request_close(now)
            self.drop_target()
            self.clear_zone()
            self.change('персонаж погиб; обычное возвращение в город')
            if self.dead_since is None:
                self.dead_since=now;self.next_revive=0;self.death_episodes+=1;self.last_death_at=now
                if getattr(self.nav,'incremental',False) is True:self.nav.cancel_pending()
            if self.death_attempts>=3 and now>=self.next_revive+60:self.death_attempts=0
            if now-self.dead_since>=4 and now>=self.next_revive and self.death_attempts<3:
                self.send(10,b'\x01')
                self.revive_requests+=1
                self.death_attempts+=1
                self.next_revive=now+15
            return
        if self.dead_since is not None:self.confirmed_revivals+=1;self.last_return_at=now
        self.dead_since=None;self.next_revive=0
        self.death_attempts=0
        if self.last_target_at is None:self.last_target_at=now
        self.learning.observe(self.world,now)
        if self.refresh_class_intent:self.refresh_class_intent()
        self.update_tactic(now)
        completed=sum(getattr(f,'delivered',0) for f in (self.adventure,self.career,self.story) if f and isinstance(getattr(f,'delivered',0),int))
        protected=self.resting or bool(self.market and self.market.state in ('opening','selling','closing')) or bool(self.town and self.town.rest_until)
        if own:self.activity.update(now,own.values.get(LV),own.values.get(15),self.kills,completed,protected)
        if own:self.refresh_farm_plan()
        if own and self.world.map==self.nav.map and not self.nav.free(self.nav.cell(self.position(now))):
            # A server correction can invalidate interpolation; prefer its raw position.
            self.world.motion.pop(self.world.own_id,None)
        if not own or self.world.map != self.nav.map or not self.nav.free(self.nav.cell(self.position(now))):
            self.change('ожидание достоверных данных карты')
            if self.pending_action and own and own.alive:
                if self.flush_action(now):return
            if own and own.alive and self.world.map==self.nav.map and now>=self.offmesh_next:
                if self.offmesh_batch>=3:
                    self.offmesh_batch=0;self.offmesh_next=now+60;return
                goal=self.nav.nearest(own.position,3)
                if goal and distance(own.position,goal)<=400:
                    self.move_goal=None
                    self.emit(movement(own.identity,self.sequence,[own.position,goal]))
                    self.offmesh_requests+=1;self.offmesh_batch+=1;self.offmesh_next=now+10
            return
        self.offmesh_batch=0
        hp, maximum = own.values.get(HP), own.values.get(MAX_HP)
        if hp is None or not maximum:
            self.change('ожидание данных здоровья')
            return
        if self.learning.waiting_reward(now):
            self.change('проверяет опыт после боя');self.next_action=now+.15;return
        # Clear a finished fight before computing `safe` for NPC travel. Doing
        # this after errands caused a dead target to deny every trip, followed
        # immediately by another ordinary fight in the same decision.
        previous_target = self.world.entities.get(self.target)
        if self.target and (not previous_target or not previous_target.alive):
            if previous_target and previous_target.values.get(HP,1)<=0:self.kills+=1
            self.drop_target()
        if self.adventure and self.adventure.prepare_priority():
            self.task_budget.paused.pop('adventure',None)
            self.task_budget.rows.pop('adventure',None)
        before_flush=self.flushed_actions
        if self.flush_action(now):
            if self.pending_action:self.change('ожидание завершения предыдущего действия')
            elif self.flushed_actions>before_flush:
                self.change('маршрут отправлен' if self.last_sent_kind==1 else 'атака отправлена; ожидает результат' if self.last_sent_kind==2 else 'действие с предметом отправлено')
            else:self.change('повторная проверка цели после остановки')
            return
        if self.market and self.market.busy:
            self.drop_target();self.clear_zone()
            self.market.tick(now,self,hp/maximum>.55)
            self.change(self.market.reason or 'ожидание торговли');return
        if self.recovery and self.recovery.tick(now,self):
            self.next_action=now+.3
            return
        if not self.resting and self.sitting.tick(now,self,False):
            self.change('встаёт перед продолжением дел');return
        profession_trip = bool(self.adventure and self.adventure.profession_priority() and not self.adventure.farm())
        if hp / maximum <= .35 or (profession_trip and not self.target and hp / maximum <= .55):
            if not self.resting:
                self.cancel_pending = True
            self.resting = True
            self.drop_target()
            self.clear_zone()
        if self.resting:
            if hp / maximum >= .85:
                if self.sitting.tick(now,self,False):
                    self.change('встаёт после восстановления');return
                self.resting = False
            else:
                self.change('отступление и восстановление')
                if not self.cancel_pending and self.sitting.tick(now,self,True):
                    self.change('восстанавливает HP сидя' if self.world.seated else 'присаживается для восстановления');return
                # Food is a prerequisite for recovery, not optional leisure.
                # Only shop after reaching the city vicinity; never fake healing.
                if (self.town and not self.cancel_pending and distance(self.position(now),self.home)<2000
                        and not any(i.identity==1847 and i.valid and i.count>0 for i in self.world.bag.values())
                        and self.town.tick(now,self,True,medical=True)):
                    self.change('восстановление: покупает еду');return
                if self.cancel_pending:
                    self.emit(movement(own.identity,self.sequence,[self.position(now),self.position(now)]))
                    self.cancel_pending = False
                    self.moves += 1
                    self.next_action = now+1
                if now >= self.next_action and distance(self.position(now), self.home) > 300:
                    self.move_to(self.home, now)
                return
        if now < self.next_action or now-self.started < 2:
            return
        if self.skills and self.skills.tick(now,self,safe=not self.target):
            self.next_action=now+.2
            self.change('изучает навыки своего класса')
            return
        if self.equipment and self.equipment.tick(now,self,safe=not self.target):
            self.next_action=now+.2
            self.change('надевает подходящую экипировку')
            return
        if self.stuck >= 5 and now>=self.next_recovery:
            self.recover_path(now)
            return
        dialogue_busy=bool(self.adventure and self.adventure.context)
        safe=not self.target and not self.resting and hp/maximum>.55
        market_dialogue=dialogue_busy or any(getattr(f,'context',None) or getattr(f,'pending',None) for f in (self.town,self.career,self.story,self.equipment,self.skills,self.chests,self.party,self.vendor) if f)
        mandatory=(own.values.get(4)==0 and own.values.get(0,1)>=9) or bool(self.career and self.career.eligible())
        first_profession = bool(self.adventure and self.adventure.profession_priority())
        self.inventory_blocked=bool(first_profession and self.world.bag_ready and not self.world.bag_disabled
                and self.world.bag_capacity is not None and self.world.bag_capacity-len(self.world.bag)<1)
        self.inventory_blocker=('нет места в сумке; завершает текущий бой перед продажей'
                                if self.inventory_blocked and self.target else None)
        if self.inventory_blocked and not self.target:
            # Inventory relief precedes another NPC exchange, but a blocked
            # seller must not freeze active kill quests or ordinary XP farming.
            if self.adventure.context:
                self.adventure.pending=None;self.adventure.settle(now,3)
            if self.vendor and self.task('vendor',self.vendor,lambda:self.vendor.tick(now,self,safe,False),now):
                self.change('освобождает сумку: продаёт обычные трофеи');return
            self.inventory_blocker='нет места в сумке; '+(self.vendor.reason if self.vendor else 'нет обработчика продажи')
            # Keep hunting when the seller cannot make progress. No quest
            # NPC acceptance or optional purchases until a slot is really free.
        self.raising_travel_funds=bool(first_profession and self.travel
            and self.travel.destination(self)!=self.world.map and self.travel.needs_funds())
        if self.raising_travel_funds:
            self.travel.reason='зарабатывает 500G на переход к наставнику'
            self.travel.next_trip=0
        if first_profession and not self.inventory_blocked and not self.raising_travel_funds and not self.target and not self.adventure.farm():
            # No new shopping, help, ordinary loot or ordinary combat while the
            # next profession step is a journal/NPC visit. Existing paid market
            # transactions and medical recovery were serviced above.
            if self.travel and self.travel.destination(self)!=self.world.map:
                # A Senna dialogue/retry in the wrong city must not keep
                # restarting while the remote class trainer is the next task.
                self.adventure.pause_for_travel()
                other_dialogue=any(getattr(f,'context',None) or getattr(f,'pending',None)
                                   for f in (self.town,self.career,self.story,self.vendor,self.party) if f)
                if other_dialogue:
                    for feature in (self.town,self.career,self.story,self.vendor):
                        if feature and getattr(feature,'context',None):feature.tick(now,self,safe,False)
                else:self.travel.tick(now,self,safe,False)
                self.clear_zone()
                self.change('первая профессия: '+(self.travel.reason or 'ожидает перехода в город наставника'))
                self.next_action=now+.5
                return
            if self.travel and self.travel.tick(now,self,safe,market_dialogue):
                self.clear_zone();self.change(self.travel.reason);return
            if not market_dialogue or self.adventure.context:
                if self.task('adventure',self.adventure,lambda:self.adventure.tick(now,self),now):
                    self.clear_zone();self.change(self.adventure.reason);return
            else:
                # Finish an exchange already in flight; do not start a new one.
                for feature in (self.town,self.story,self.career,self.vendor):
                    if feature and getattr(feature,'context',None):
                        feature.tick(now,self,safe,False)
            self.change('первая профессия: '+self.adventure.reason)
            self.next_action=now+.5
            return
        if not self.raising_travel_funds and self.helper and self.helper.tick(now,self):return
        loot_dialogue=market_dialogue or any(getattr(f,'context',None) for f in (self.travel,self.market) if f)
        if not loot_dialogue:
            if self.loot and not (self.target and self.world.entities.get(self.target) and self.world.entities[self.target].alive):
                task = self.adventure.farm() if self.adventure else None
                needed = self.equipment.loot_needs() if self.equipment else set()
                competitive={task[1]} if task and task[1] else set()
                if self.career:competitive.update(self.career.needed_items())
                if self.story:competitive.update(self.story.needed_items())
                self.loot.competitive=competitive
                if task and task[1]:needed.add(task[1])
                if self.career:needed.update(self.career.needed_items())
                if self.story:needed.update(self.story.needed_items())
                if self.chests:needed.update(self.chests.catalog.chests)
                if self.market:needed.update(self.market.loot_needs())
                if self.vendor:needed.update(self.vendor.junk)
                if self.skills and self.skills.catalog:needed.update(self.skills.catalog.books)
                if self.chests and self.world.bag_ready and not self.world.bag_disabled:
                    free=(self.world.bag_capacity or 0)-len(self.world.bag)
                    if free>4:needed.update(item[0] for item in self.world.items.values() if item[0] in self.chests.catalog.names)
                if self.loot.tick(now,self,needed):
                    self.change('подбор нужного лута; результат подтверждает сервер')
                    return
        if self.travel and (not self.activity.hunting(now) or self.mandatory_work() or self.travel.starter_trip()) and not (self.helper and self.helper.active(now)) and self.travel.tick(now,self,safe,market_dialogue):
            self.drop_target();self.clear_zone();self.change(self.travel.reason);return
        if self.task('vendor',self.vendor,lambda:self.vendor.tick(now,self,safe,market_dialogue),now):
            self.drop_target();self.clear_zone();self.change(self.vendor.reason);return
        if self.task('market',self.market,lambda:self.market.tick(now,self,safe and not mandatory,market_dialogue),now):
            self.drop_target();self.clear_zone();self.change(self.market.reason or 'торговые дела');return
        if self.chests and self.chests.tick(now,self,safe):
            self.change('открывает собственный сундук');self.next_action=now+.3;return
        if self.task('career',self.career,lambda:self.career.tick(now,self,safe,dialogue_busy or bool(self.town and self.town.context) or bool(self.story and self.story.context)),now):
            self.drop_target();self.clear_zone();self.change(self.career.reason);return
        if self.wants_story() and self.task('story',self.story,lambda:self.story.tick(now,self,safe,dialogue_busy or bool(self.town and self.town.context) or bool(self.career and self.career.context)),now):
            self.drop_target();self.clear_zone();self.change('сюжетное задание: жизненные навыки');return
        if self.task('town',self.town,lambda:self.town.tick(now,self,safe,dialogue_busy or bool(self.career and self.career.context) or bool(self.story and self.story.context)),now):
            self.drop_target();self.clear_zone();self.change(self.town.reason);return
        if self.task('adventure',self.adventure,lambda:self.adventure.tick(now,self),now):
            self.drop_target()
            self.clear_zone()
            self.change(self.adventure.reason)
            return
        shared_models=self.quest_models()
        target = self.world.entities.get(self.target)
        if self.target and (not target or not target.alive):
            if target and target.values.get(HP,1)<=0:self.kills+=1
            self.drop_target()
            target=None
        if target:
            stopped=(self.world.skill_packet_number==self.last_sent_sequence
                     and self.world.skill_action_state in (16,64,512)
                     and self.last_sent_kind==2)
            failed=self.world.last_failed_action
            disappeared=(self.world.failed_actions>self.attack_failure_seen and failed
                         and failed['actor']==own.identity and failed['action']==2 and failed['reason']==5)
            if stopped or disappeared:
                self.rejected_target_releases+=1
                self.attack_failure_seen=self.world.failed_actions
                self.drop_target(now,avoid=True)
                target=None
        if target:
            key=(self.world.map,target.identity,target.handle)
            if (not self.eligible(target,now) or key!=self.target_key
                    or (self.coordination and not self.coordination.claim(self.owner,key,now,shared=self.shared_target or target.model in shared_models))):
                self.drop_target(now,avoid=True)
                target=None
            else:
                hp=target.values.get(HP)
                if self.last_target_hp is not None and hp is not None and hp<self.last_target_hp:
                    self.last_damage_at=now
                self.last_target_hp=hp
                # Detect an approach that never completes and attacks that cause no damage.
                stalled=(self.combat_since is not None and now-self.last_damage_at>=14)
                if stalled or (self.combat_since is None and now-self.target_since>25):
                    self.no_damage_retargets+=1
                    if stalled:self.learning.finish(self.world,now,'stalled')
                    self.drop_target(now,avoid=True)
                    target=None
        if not target:
            candidates=[e for e in self.world.entities.values() if self.eligible(e,now)]
            self.rng.shuffle(candidates)  # Distinct tie ordering for each character.
            candidates.sort(key=lambda e:self.target_score(e,now))
            if self.region and now-self.last_target_at>=20 and not self.assist_target:
                known={e.identity for e in candidates}
                models=self.learning.admissible(self.region,own,now)
                extras=[e for e in self.world.entities.values()
                        if e.identity not in known and self.eligible(e,now,models)]
                extras.sort(key=lambda e:self.target_score(e,now))
                candidates.extend(extras)
            # Prefer unclaimed reachable mobs. If every viable target is busy,
            # join a real fight instead of waiting for another bot's lease.
            # Active quest mobs can be shared on the first pass.
            for join_busy in (False,True):
                for candidate in candidates:
                    shared=join_busy or candidate.model in shared_models
                    key=(self.world.map,candidate.identity,candidate.handle)
                    if self.coordination and not self.coordination.available(self.owner,key,now,shared=shared):
                        self.busy_targets+=1
                        continue
                    reach=self.attack_reach(candidate)
                    in_range=distance(self.position(now),self.world.position(now,candidate.identity))<=reach
                    if not in_range and self.approach(candidate,reach,now,shared=shared) is None:continue
                    if self.coordination and not self.coordination.claim(self.owner,key,now,shared=shared):continue
                    target=candidate
                    self.shared_target=shared
                    if candidate.model not in self.planned_models():
                        self.opportunity_model=candidate.model;self.opportunity_targets+=1
                    self.last_target_at=now
                    self.target,self.target_since=target.identity,now
                    self.target_key=key
                    self.last_target_hp=target.values.get(HP)
                    self.last_damage_at=now
                    self.combat_since=None
                    self.approach_probe=False
                    self.clear_zone()
                    break
                if target:break
        if target:
            if self.fight_running(target,now):
                self.active_fight_waits+=1
                self.change('продолжает бой: ожидает следующий серверный удар')
                self.next_action=now+.25
                return
            reach = self.attack_reach(target)
            if distance(self.position(now),self.world.position(now,target.identity)) > reach:
                self.change('подход к слабому мобу')
                goal=self.approach(target,reach,now)
                if not goal or not self.move_to(goal,now):
                    self.drop_target(now,avoid=True)
                return
            # Already in attack range: stop the previous search/approach route
            # now, instead of waiting for its distant endpoint. emit/flush still
            # wait for the matching server stop before submitting the attack.
            if self.move_goal:
                self.attack_move_revision=self.world.move_revision;self.move_goal=None
            if self.world.failed_actions>self.attack_failure_seen:
                self.attack_failure_seen=self.world.failed_actions
                failed=getattr(self.world,'last_failed_action',None)
                if failed and failed.get('actor')==own.identity and failed.get('action')==2:
                    self.move_goal=None;self.world.motion.pop(own.identity,None)
                    if failed['reason']==1 and now-self.last_attack_stop>2:
                        self.action_open=True;self.last_attack_stop=now
            if not self.world.default_skill:
                self.change('ожидание обычной атаки от сервера')
                return
            if self.combat_since is None:self.combat_since=self.last_damage_at=now
            if now-self.last_damage_at>=6 and not self.approach_probe:
                self.approach_probe=True
                self.approach_angle+=math.pi/2
                goal=self.approach(target,max(100,reach-40),now)
                if goal and distance(self.position(now),goal)>80:
                    self.move_goal=None
                    self.move_to(goal,now)
                    self.change('повторный подход: нет подтверждённого урона')
                    return
            self.change('обычная атака')
            self.fight = (self.fight+1) & 255
            self.emit(normal_attack(own.identity, self.sequence, self.fight, self.world.default_skill,
                                    target.identity, target.handle, self.position(now)))
            self.world.freeze_prediction(now)
            self.move_goal=None
            if self.loot:
                self.loot.note_attack(target.identity,now)
            self.next_action = now+self.attack_interval
            return
        if self.region and self.world.map!='garner' and own.values.get(LV,1)<=3:
            self.change('ожидание перехода в Аргент: старт на Forest Spirit');self.next_action=now+1;return
        self.change('поиск свободного места фарма')
        if self.region:
            raw_goals=[pt for model in self.planned_models() if str(model) in self.region['farms']
                       for pt in self.region['farms'][str(model)]['points']]
        elif self.adventure:
            raw_goals=self.adventure.farm_goals()
        else:
            raw_goals=[self.nav.waypoints[i] for i in self.route]
        goals=list(dict.fromkeys(self.nav.nearest(p) for p in raw_goals))
        goals=[p for p in goals if p and self.goal_blacklist.get(p,0)<=now]
        if not goals:
            self.change('нет свободного проверенного маршрута; повторный поиск')
            self.next_action=now+2
            return
        # Stable per-bot ordering, independent of the order of the JSON species.
        # Choose a nearby available farm instead of crossing the whole region
        # in a hash-random order. Reservation ties remain different per bot.
        origin=self.position(now)
        goals.sort(key=lambda pt:(int(distance(origin,pt)//1500),
                    (pt[0]*73856093 ^ pt[1]*19349663 ^ int(self.approach_angle*100000)) & 0xffffffff))
        goal=(self.coordination.choose_zone(self.owner,self.world.map,goals,now,self.position(now))
              if self.coordination else goals[self.waypoint%len(goals)])
        if goal!=self.search_goal:
            self.search_goal,self.search_started=goal,now
            speed=max(100,self.world.own.values.get(44,480))
            self.search_deadline=now+max(45,min(900,distance(self.position(now),goal)/speed*1.8+20))
        if distance(self.position(now),goal)<300 or now>self.search_deadline:
            self.goal_blacklist[goal]=now+20
            if len(self.goal_blacklist)>128:self.goal_blacklist.pop(next(iter(self.goal_blacklist)))
            self.clear_zone()
            self.waypoint+=1
            self.next_action=now+.5
        elif not self.move_to(goal,now):
            self.goal_blacklist[goal]=now+45
            self.clear_zone()
            self.next_action=now+1

    def summary(self):
        return {'tactic':self.tactic,'activity':self.activity.summary(),'offmesh_recovery_requests':self.offmesh_requests,'schedule':self.tactic_schedule.summary() if self.tactic_schedule else None,'state': self.mode,'state_seconds':max(0,self.clock-self.mode_since),
                'inventory_blocker':self.inventory_blocker,'farm_plan':{'character_level':self.world.own.values.get(LV),'models':sorted(self.planned_models()),'replans':self.farm_plan_changes},
                'hunting_learning':self.learning.summary(),
                'action_wait':{'pending':bool(self.pending_action),'kind':self.pending_action[0][8] if self.pending_action else None,
                               'seconds':round(max(0,self.clock-self.pending_action[1]+.15),2) if self.pending_action else 0,
                               'last_sent_kind':self.last_sent_kind,'stop_kind':self.world.stop_packet_kind,'matching_stop':self.action_stopped()},
                'shared_target':self.shared_target,'target_hp':self.last_target_hp,'seconds_since_target_damage':max(0,self.clock-self.last_damage_at) if self.target else None,'target_id':self.target,'opportunity_model':self.opportunity_model,'opportunity_targets':self.opportunity_targets,'path_recoveries':self.recoveries,'end_action_requests':self.end_action_requests,'queued_actions':self.queued_actions,'action_packets_sent':dict(self.sent_action_counts),'flushed_actions':self.flushed_actions,'awaiting_action_stop':bool(self.pending_action),'town_detours_yielded':self.task_budget.yields,
                'active_fight_wait_ticks':self.active_fight_waits,'rejected_target_releases':self.rejected_target_releases,'search_destination':self.search_goal,'movement_endpoint':self.move_endpoint,'last_action_kind':self.last_sent_kind,
                'no_damage_retargets':self.no_damage_retargets,'reserved_targets_skipped':self.busy_targets, 'move_requests': self.moves, 'attack_requests': self.attacks,
                'revive_requests':self.revive_requests, 'revival':{'episodes':self.death_episodes,'confirmed_returns':self.confirmed_revivals,'last_death_ago':max(0,self.clock-self.last_death_at) if self.last_death_at is not None else None,'last_return_ago':max(0,self.clock-self.last_return_at) if self.last_return_at is not None else None,'attempts_in_batch':self.death_attempts,'dead_seconds':max(0,self.clock-self.dead_since) if self.dead_since is not None else 0,'retry_in_seconds':max(0,self.next_revive-self.clock) if self.dead_since is not None else 0}, 'movement_wait_ticks':self.move_waits, 'observed_target_deaths': self.kills, 'world': self.world.summary()}


def hunt(client, seconds, stop, report, navigation, tell=print, bot_name='', chat_budget=None, adventure_mode=False, role_store=None, fleet=None, bot_index=0, tactic='quests'):
    report.stage('reading_world')
    from equipment import ItemCatalog,Equipment
    from pathlib import Path
    catalog=getattr(navigation,'items',None) or ItemCatalog(Path(__file__).resolve().parents[1]/'assets/items.json')
    world = World(catalog.types)
    try:
        world.enter(client.enter_payload)
    except ProtocolError:
        report.result['world_decode'] = world.decode_info
        raise
    report.result['world_decode'] = world.decode_info
    nav=navigation.nav(world.map) if hasattr(navigation,'nav') else navigation
    policy = Hunter(world, nav, client.wire.send, report, tell, bot_name)
    if bot_index:policy.learning.load(Path(__file__).resolve().parents[1]/'data'/f'hunt-learning-{bot_index:03d}.json')
    policy.tactic=tactic
    from coordination import TacticSchedule
    policy.tactic_schedule=TacticSchedule(tactic,bot_name)
    policy.coordination=getattr(navigation,'coordination',None)
    policy.region=navigation.get(world.map) if hasattr(navigation,'get') else None
    if policy.region:policy.home=policy.nav.nearest(policy.region['spawns'][0],12) or policy.home
    policy.equipment=Equipment(world,catalog,client.wire.send,tell)
    from recovery import Recovery
    policy.recovery=Recovery(world)
    progression = Progression(world, client.wire.send)
    social = Social(world, client.wire.send, bot_name, chat_budget or ChatBudget(), bot_name,conversations=getattr(navigation,'conversations',None))
    from personality import Personality
    personality=Personality(bot_name);social.personality=personality
    social.scripted_dialogues=False
    role = None
    if role_store:
        role = role_store.resolve(bot_name,world.own.model,world.own.values.get(4))
        progression.first_job = role['first_job']
        progression.target_job=role['target_job']
        from skills import Skills
        policy.skills=Skills(world,role,getattr(navigation,'life',None))
        social.role_label=role['label']
        tell('Закреплённый класс: '+role['label'])
        report.result['class_path'] = role
    if adventure_mode:
        from adventure import Adventure
        from loot import QuestLoot
        if role is None:
            raise ProtocolError('Для квестов требуется сохранённый путь класса.')
        policy.adventure = Adventure(world,client.wire.send,tell,role,policy.region,tactic=tactic)
        policy.loot = QuestLoot(world,collect_all=True)

    life=getattr(navigation,'life',None)
    if life and role:
        from life import Chests
        from town import Town
        from career import Career
        from story import Story
        from party import Party
        policy.chests=Chests(world,life)
        policy.town=Town(world,life,catalog,role,policy.rng,policy.home,getattr(navigation,"rest_directory",None),bot_name)
        from vendor import Vendor
        policy.vendor=Vendor(world,life,catalog,role,policy.rng,policy.home,getattr(navigation,"assets",Path(__file__).resolve().parents[1]/"assets"))
        policy.career=Career(world,client.wire.send,role,life,navigation)
        policy.story=Story(world,client.wire.send,role,life,navigation)
        policy.party=Party(world,client.wire.send,bot_name,bot_index,navigation.directory)
        from city_travel import CityTravel
        policy.travel=CityTravel(world,client.wire.send,bot_index,role)
        if hasattr(navigation,'market_catalog'):
            from market import Market
            policy.market=Market(world,client.wire.send,bot_name,bot_index,navigation.market_catalog,catalog,life,navigation.market_directory)

    balance_checked=False
    def refresh_class_intent():
        nonlocal balance_checked
        old=policy.adventure
        if (balance_checked or not role_store or not role or not old
                or not old.journal_snapshot_received or old.context or old.pending):return
        balance_checked=True
        updated=role_store.rebalance_novice(bot_name,world.own.model,world.own.values.get(4),old.journal)
        report.result['class_balance']={'checked':True,'changed_unpromoted_intent':updated['target_job']!=role['target_job']}
        if updated['target_job']==role['target_job']:return
        role.update(updated)
        progression.first_job=role['first_job'];progression.target_job=role['target_job']
        social.role_label=role['label']
        if policy.career:policy.career.quest=life.services['quests'][str(role['target_job'])]
        replacement=Adventure(world,client.wire.send,tell,role,policy.region,tactic=old.configured_tactic)
        replacement.tactic=old.tactic
        replacement.journal=dict(old.journal)
        replacement.journal_ready=replacement.journal_snapshot_received=True
        replacement.accepted=old.accepted;replacement.delivered=old.delivered
        replacement.requests=old.requests;replacement.timeouts=old.timeouts
        policy.adventure=replacement
        tell('Будущий класс новичка для выравнивания состава: '+role['label']+'. Персонаж и его прогресс сохранены.')
    policy.refresh_class_intent=refresh_class_intent

    def sale_offer():
        if not life or not world.bag_ready or world.bag_disabled:return None
        protected=set()
        if policy.career:protected.update(policy.career.needed_items())
        if policy.story:protected.update(policy.story.needed_items())
        if policy.adventure:
            task=policy.adventure.farm()
            if task and task[1]:protected.add(task[1])
        for item in world.bag.values():
            gear=catalog.gear.get(item.identity)
            if not item.valid or not gear or item.identity in protected:continue
            current=world.own.equipment.get(gear['links'][0],0)
            worn=catalog.gear.get(current)
            if worn and worn['score']>=gear['score']:
                name=life.names.get(item.identity,str(item.identity)).encode('cp1251',errors='replace').decode('cp1251')[:40]
                return 'Предлагаю лишнюю вещь: '+name+'. Есть в сумке.'
        return None
    social.sale_offer=sale_offer
    social.market=policy.market
    from help_player import HelpPlayer
    policy.helper=HelpPlayer(world)
    policy.helper.personality=personality
    social.help_handler=lambda source,now:policy.helper.request(source,now,policy)
    contacts=cooperation=None
    if policy.party:
        policy.party.personality=personality
        social.party_handler=policy.party.request_human
        from contacts import Contacts
        contacts=Contacts(world,client.wire.send,social,personality,policy.party)
        social.friend_handler=contacts.local_friend
    if hasattr(navigation,'help_directory'):
        from cooperation import Cooperation
        cooperation=Cooperation(world,policy,social,personality,navigation.help_directory)
        social.bot_handler=cooperation.hear
    def context_line():
        if policy.resting:return 'Сначала восстановлю здоровье, потом снова за дело.'
        if policy.market and policy.market.state=='selling':return 'Ларёк открыт. Продаю то, что действительно есть в сумке.'
        if policy.vendor and policy.vendor.sale_target:return 'Отнесу лишние трофеи торговцу, место в сумке заканчивается.'
        if policy.town and policy.town.target_shop:return 'Проверю припасы и подходящие вещи у торговца.'
        if policy.town and policy.town.rest_until:return 'Немного прогуляюсь по городу и вернусь к охоте.'
        if policy.travel and policy.travel.target:return 'Иду к портальщице, нужно перейти в другой город.'
        target=world.entities.get(policy.target)
        if target and target.alive:return 'Сейчас закончу бой, потом разберу добычу.'
        if policy.learning.waiting_reward(time.monotonic()):return 'Проверяю добычу и полученный опыт.'
        if policy.learning.events:
            event=policy.learning.events.pop();policy.learning.events.clear()
            if event=='danger':return 'Слишком больно бьёт. Восстановлюсь и попробую другую охоту.'
            if event=='stalled':return 'На этой цели толку нет. Поищу другую.'
            if event=='revived':return 'Вернулся после гибели. Проверю припасы и подберу охоту полегче.'
            return 'Этот бой вышел нормально. Проверю добычу и продолжу.'
        if policy.mandatory_work():return 'Хочу получить свою профессию. Проверяю задание наставника.'
        if policy.learning.probing:return 'Проверю другой вид мобов и сравню, сколько получаю опыта.'
        return None
    social.context_provider=context_line
    from public_chat import PublicChat,PublicBudget
    public_chat=PublicChat(world,client.wire.send,getattr(navigation,"public_chat_budget",None) or PublicBudget(),bot_name)
    def public_context(channel):
        if channel=='trade':
            if not policy.market or policy.market.state!='selling' or not policy.market.stock:return None
            _,price,count,slot=policy.market.stock[0];item=world.bag.get(slot)
            if not item:return None
            name=(life.names.get(item.identity,str(item.identity)) if life else str(item.identity)).encode('cp1251',errors='replace')[:32].decode('cp1251')
            return f'В моём ларьке: {name}, {count} шт., цена {price} за штуку.'
        if (policy.market and policy.market.busy) or (policy.town and (policy.town.rest_until or policy.town.target_shop)) or (policy.vendor and policy.vendor.sale_target) or (policy.travel and policy.travel.target):return None
        if policy.mandatory_work():return f'На {world.own.values.get(0,1)} уровне разбираюсь с заданием профессии.'
        if policy.learning.probing:return 'Пробую другую охоту: сравню опыт и потери здоровья.'
        target=world.entities.get(policy.target)
        if target and target.alive:return f'Охочусь. У меня сейчас {world.own.values.get(0,1)} уровень.'
        return None
    public_chat.context_provider=public_context

    def snapshot(now):
        policy.learning.save(now)
        report.result['decision_loop']=dict(think_stats)
        report.result['route_planning']=policy.nav.planning_stats()
        report.result['sitting']=policy.sitting.summary()
        report.result['hunt']=policy.summary()
        if policy.loot:report.result['loot']=policy.loot.summary()
        if contacts:report.result['contacts']=contacts.summary()
        if cooperation:report.result['cooperation']=cooperation.summary()
        report.result['progression']=progression.summary()
        report.result['equipment']=policy.equipment.summary()
        report.result['chat']=social.summary()
        report.result['public_chat']=public_chat.summary()
        if social.conversations:report.result['chat']['shared_conversations']=social.conversations.summary()
        report.result['recovery']=policy.recovery.summary()
        for key in ('chests','town','career','story','party','market','travel','helper','vendor'):
            feature=getattr(policy,key)
            if feature:report.result[key]=feature.summary()
        if policy.skills:report.result['skills']=policy.skills.summary()
        if policy.adventure:report.result['adventure']=policy.adventure.summary()
        report.write(Path(__file__).resolve().parents[1]/f'bot-report-{bot_index:02d}.json')
        if fleet:
            values=world.own.values
            fleet.update(bot_index,connected=True,map=world.map,position=list(world.position(now)),level=values.get(0),job=values.get(4),
                         body=world.own.model,state=policy.mode,tactic=policy.tactic,phase=policy.tactic_schedule.effective_phase,hp=values.get(HP),max_hp=values.get(MAX_HP),
                         moves=policy.moves,attacks=policy.attacks,equips=policy.equipment.confirmed,
                         experience=values.get(15),start_experience=progression.start_xp,
                         start_level=progression.start_level,hunt_style=policy.learning.profile[0],farm_models=sorted(policy.planned_models()),
                         quests=policy.adventure.delivered if policy.adventure else 0,
                         target_job=role['target_job'] if role else 0)

    def observe(command, payload):
        now=time.monotonic()
        if command in (5011,5012,5403):
            if contacts:contacts.hear(command,payload,now)
            return
        if command in (5401,5402):
            try:public_chat.observe(command,payload,now)
            except ProtocolError:report.result['public_chat_decode']='unsupported'
            return
        if command in (854,856,857,858,859):
            if policy.market:
                try:policy.market.observe(command,payload,now)
                except ProtocolError:
                    report.result['market_decode']='unsupported'
                    policy.market.disabled=True
                    if policy.market.state in ('opening','selling','closing'):policy.market.request_close(now)
                    else:policy.market.finish(now);policy.market.context=None
            return
        if command in (5001,5002,5003):
            if policy.party:
                try:
                    if command==5001 and policy.market and policy.market.busy:
                        reader=Reader(payload);reader.string_bytes();identity=reader.long()
                        client.wire.send(6003,struct.pack('>I',identity))
                    else:policy.party.observe(command,payload,now)
                except ProtocolError:report.result['party_decode']='unsupported';policy.party=None
            return
        if policy.vendor and policy.vendor.context and command in (801,802,803,805,806,807,808):
            try:
                if policy.vendor.observe(command,payload,now,client.wire.send):return
            except ProtocolError:
                policy.vendor.finish_sale(now);report.result['vendor_decode']='unsupported'
        if policy.travel and command==802 and policy.travel.context:
            if policy.travel.observe(command,payload,now):return
        if command in (801,802,803,805,806,807,808,822,827,828,830,831,832):
            consumed=False
            for feature in (policy.career,policy.story):
                if feature:
                    used=feature.observe(command,payload,now)
                    consumed=consumed or used
            if policy.town and policy.town.context:
                try:consumed=policy.town.observe(command,payload,now,client.wire.send) or consumed
                except ProtocolError:policy.town.finish(now,600);report.result['shop_decode']='unsupported'
            if consumed:return
        if command==516:
            was_dead=world.own is not None and not world.own.alive
            if getattr(policy.nav,'incremental',False) is True:policy.nav.cancel_pending()
            world.enter(payload)
            policy.pending_action=None;policy.action_open=False
            policy.sitting.reset()
            policy.assist_target=None
            if policy.helper:policy.helper.source=None
            if policy.travel:policy.travel.on_map(now)
            if policy.vendor:policy.vendor.home=world.own.position;policy.vendor.finish_sale(now)
            if policy.market:
                policy.market.finish(now);policy.market.context=None;policy.market.pending=None
            policy.nav=navigation.nav(world.map) if hasattr(navigation,'nav') else nav
            if getattr(policy.nav,'incremental',False) is True:policy.nav.cancel_pending()
            policy.region=navigation.get(world.map) if hasattr(navigation,'get') else None
            policy.home=world.own.position
            if policy.region:policy.home=policy.nav.nearest(policy.region['spawns'][0],12) or policy.home
            if was_dead:
                policy.confirmed_revivals+=1;policy.last_return_at=now
                policy.learning.events.append('revived');policy.learning.events=policy.learning.events[-8:]
            if policy.town:policy.town.end_rest(now);policy.town.home=policy.home;policy.town.finish(now,120)
            policy.drop_target()
            policy.clear_zone()
            policy.move_goal=None
            policy.stuck=0
            policy.offmesh_batch=0;policy.offmesh_next=0
            policy.resting=False
            policy.cancel_pending=False
            policy.dead_since=None;policy.next_revive=0
            policy.death_attempts=0
            policy.equipment.pending=None
            policy.recovery.pending=None
            if policy.skills:policy.skills.pending=None
            if adventure_mode:
                policy.adventure=Adventure(world,client.wire.send,tell,role,policy.region,tactic=tactic)
        elif command in (801,802,803,822,827,828,830,831,832):
            if policy.adventure:
                policy.adventure.observe(command,payload)
        elif command == 501:
            reader = Reader(payload)
            source, text = reader.long(), reader.string()
            social.hear(source, text, time.monotonic())
        else:
            world.observe(command, payload)

    client.world_handler = observe
    try:
        while client.pending_world:
            observe(*client.pending_world.popleft())
        report.stage('hunting')
        tell(f'Данные мира: {world.map}, координаты {world.own.x//100},{world.own.y//100}, '
             f'здоровье {world.own.values[HP]}/{world.own.values[MAX_HP]}.')
        next_snapshot=0
        next_think=0
        think_stats={"count":0,"max_seconds":0,"total_seconds":0}
        seen_equips=seen_skills=seen_quests=0
        seen_party=seen_chests=seen_shopping=0
        deadline = float('inf') if seconds==0 else time.monotonic()+seconds
        while time.monotonic() < deadline and not stop.is_set():
            try:
                command, payload = client.wire.receive(min(deadline, time.monotonic()+.25))
                client.service(command, payload)
            except TimeoutError:
                pass
            now=time.monotonic()
            if now>=next_think:
                think_started=now
                next_think=now+.25
                if hasattr(navigation,'directory'):
                    navigation.directory.update(bot_name,bot_index,world.map,world.position(),world.own.values.get(0,1),time.monotonic())
                if policy.party:
                    dialogue_busy=any(getattr(f,'context',None) for f in (policy.adventure,policy.town,policy.career,policy.story,policy.travel) if f)
                    policy.party.tick(time.monotonic(),bot_index,safe=not policy.target and not dialogue_busy and not policy.resting and not (policy.market and policy.market.busy))
                if policy.town:
                    completed=sum(getattr(f,'delivered',0) for f in (policy.adventure,policy.career,policy.story) if f)
                    policy.town.note_progress(policy.kills,completed)
                policy.tick()
                now = time.monotonic()
                if cooperation:cooperation.tick(now)
                if contacts:contacts.tick(now)
                alive = world.own.alive
                safe = (alive and now-policy.started >= 3 and not policy.resting
                        and world.own.values.get(HP, 0) > world.own.values.get(MAX_HP, 1) * .5)
                progression.tick(now, safe and not (policy.market and policy.market.busy))
                social.activity='quest' if policy.adventure and ('NPC' in policy.mode or 'задани' in policy.mode or 'поручен' in policy.mode) else 'hunt'
                if policy.equipment.confirmed>seen_equips:social.event('equipment',now)
                if policy.skills and policy.skills.confirmed>seen_skills:social.event('skill',now)
                if policy.adventure and policy.adventure.delivered>seen_quests:social.event('quest_done',now)
                seen_equips=policy.equipment.confirmed
                seen_skills=policy.skills.confirmed if policy.skills else 0
                seen_quests=policy.adventure.delivered if policy.adventure else 0
                if policy.town and policy.town.rest_until:social.activity='city'
                social.party_size=len(policy.party.members) if policy.party else 0
                if social.party_size>seen_party and social.party_size>1:social.event('party',now)
                if policy.chests and policy.chests.confirmed>seen_chests:social.event('chest',now)
                if policy.town and policy.town.confirmed>seen_shopping:social.event('shopping',now)
                seen_party=social.party_size
                seen_chests=policy.chests.confirmed if policy.chests else 0
                seen_shopping=policy.town.confirmed if policy.town else 0
                social.busy_state=bool(policy.target or (policy.market and policy.market.busy)
                    or any(getattr(f,'context',None) for f in (policy.adventure,policy.career,policy.story,policy.town,policy.vendor,policy.travel) if f))
                social.tick(now, policy.resting, alive and now-policy.started >= 3)
                public_chat.tick(now,alive and now-policy.started>=3,policy.market)
                think_stats['count']+=1
                elapsed=time.monotonic()-think_started
                think_stats['max_seconds']=max(think_stats['max_seconds'],elapsed)
                think_stats['total_seconds']+=elapsed
            if now>=next_snapshot:
                snapshot(now)
                next_snapshot=now+15
            if time.monotonic()-client.wire.last_send > 2:
                client.wire.heartbeat()
    finally:
        policy.learning.save(time.monotonic(),force=True)
        report.result['hunt'] = policy.summary()
        report.result['sitting']=policy.sitting.summary()
        report.result['route_planning']=policy.nav.planning_stats()
        if policy.loot:report.result['loot']=policy.loot.summary()
        if contacts:report.result['contacts']=contacts.summary()
        if cooperation:
            report.result['cooperation']=cooperation.summary()
            navigation.help_directory.remove(bot_name)
        report.result['progression'] = progression.summary()
        report.result['chat'] = social.summary()
        report.result['equipment']=policy.equipment.summary()
        report.result['recovery']=policy.recovery.summary()
        for key in ('chests','town','career','story','party','market','travel','helper','vendor'):
            feature=getattr(policy,key)
            if feature:report.result[key]=feature.summary()
        if policy.skills:report.result['skills']=policy.skills.summary()
        if policy.adventure:
            report.result['adventure'] = policy.adventure.summary()
            report.result['adventure']['quest_loot_requests'] = policy.loot.requests
        policy.drop_target()
        policy.clear_zone()
        if hasattr(navigation,'directory'):navigation.directory.remove(bot_name)
        if social.conversations:social.conversations.remove(bot_name,time.monotonic())
        if policy.town:policy.town.end_rest(time.monotonic())
        if policy.market:
            if policy.market.state in ('opening','selling','closing'):
                policy.market.request_close(time.monotonic())
            policy.market.directory.release(bot_name)
        client.world_handler = None
