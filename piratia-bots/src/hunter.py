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
from route_search import RoutePending
from contextlib import nullcontext
from progression import Progression
from social import Social, ChatBudget
from world import World, HP, MAX_HP, LV, ATTACK_DISTANCE
from coral_supplies import spent_basic
from farm_plan import MAX_RECOVERY_LEVEL_GAP, PREFERRED_LEVEL_GAP, xp_level_divisor


def distance(a, b):
    return math.hypot(a[0]-b[0], a[1]-b[1])


def action_header(actor, number, kind):
    return struct.pack('>IIB', actor, number, kind)


def movement(actor, number, points):
    if not 2 <= len(points) <= 32:
        raise ValueError('Expected 2..32 movement points')
    return action_header(actor, number, 1) + sequence(b''.join(struct.pack('<ii', *p) for p in points))


def normal_attack(actor, number, fight, skill, target, handle, position, approach=None):
    # Native BeginAction 0x5198b0: chMove=2, fight ID, path, skill, world ID, handle.
    # In-range attacks still include two equal points, as the normal UI does.
    points = sequence(struct.pack('<iiii', *position, *(approach or position)))
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
        self.sent_move_points=();self.move_map=None;self.cancelled_move_packet=None
        self.move_stop_seen=-1;self.blocked_move_stops=0;self.last_blocked_step=None
        self.assist_target=None;self.helper=None
        self.group_hunt=None
        self.repair=None
        self.escape_plan=None
        self.treasure=None
        from progress_monitor import ProgressMonitor
        self.progress_monitor=ProgressMonitor()
        self.target = None
        self.shared_target = False
        self.opportunity_model=None;self.opportunity_targets=0;self.last_target_at=None
        self.next_action = 0
        self.fast_progression=False
        self.immediate_defences=0
        self.combat_wakes=0;self.next_combat_wake=0;self.goldie_exit_retry=0
        self.approach_attacks=0;self.approach_attack_tried=False
        self.mode = 'observe'
        self.mode_since=self.clock
        self.next_console_state=0;self.last_console_mode=None
        self.resting = False
        self.retreat_goal=None;self.retreat_replans=0
        self.cancel_pending = False
        self.waypoint = 0
        self.moves = self.attacks = self.kills = 0
        self.own_hit_deaths=0
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
        self.combat_skills=None;self.last_attack_skill=None;self.mana_resting=False
        self.recovery = None
        self.chests=self.town=self.party=self.career=self.story=self.market=self.travel=self.vendor=None
        self.bank=None
        self.direct_trade=None;self.commerce=None
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
        self.search_recovery=False
        self.search_started=0
        self.search_deadline=0
        self.camp_arrival_until=0
        self.goal_blacklist={}
        self.tactic='quests'
        self.quest_phase='quests'
        self.tactic_schedule=None
        self.optional_quests=True
        self.owner_services=None
        self.crafting=None
        self.xp_boosters=None
        self.hunt_travel=None
        self.camp_scouting=False
        from activity import Activity
        self.activity=Activity();self.offmesh_next=0;self.offmesh_requests=0
        from stuck_return import StuckReturn
        self.stuck_return=StuckReturn();self.offmesh_since=None
        self.offmesh_batch=0
        self.offmesh_route=();self.offmesh_origin=None;self.offmesh_blocked={};self.offmesh_reason=''
        from farm_plan import HuntLearning
        self.learning=HuntLearning(self.owner)
        self.farm_plan_key=None;self.farm_plan_changes=0
        self.starter_search_since=None
        self.refresh_class_intent=None
        self.background_task=None
        self.mob_knowledge=None;self.npc_knowledge=None
        self.mechanics=None
        self.petcare=None
        self.economy=None
        self.professions=None
        self.shortcut=None
        self.quest_combat_ready=False
        self.protected_fights_stopped=0;self.immune_fights_released=0
        self.protected_target_checks=0;self.last_protected_target=None
        self.inventory_blocked=False
        self.inventory_blocker=None
        self.raising_travel_funds=False
        self.supply_funding_goal=0;self.supply_funding_models=set();self.paused_camp=None
        from sitting import Sitting
        self.sitting=Sitting(world)

    def update_tactic(self,now):
        if not self.tactic_schedule or not self.world.own:return
        current=self.world.entities.get(self.target)
        busy=bool(current and current.alive) or self.resting or self.camp_route_active(now)
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
        self.approach_attack_tried=False

    def clear_zone(self):
        if self.coordination:self.coordination.leave_zone(self.owner)
        self.search_goal=None
        self.search_recovery=False
        self.camp_arrival_until=0

    def pause_camp(self,now):
        if self.search_goal and self.search_deadline>now and not self.paused_camp:
            self.paused_camp=(self.world.map,self.search_goal,now+900)
        self.clear_zone()

    def camp_route_active(self,now):
        return bool((self.search_goal and now<self.search_deadline) or now<self.camp_arrival_until)

    def hunt_before_errands(self,now):
        last=self.learning.last_progress_at
        mine_approach=getattr(self.hunt_travel,'mine_approach',lambda:False)
        return bool(self.supply_funding_goal) or self.camp_route_active(now) or mine_approach() or bool(
            getattr(self,'fast_progression',False) and self.region and last is not None and now-last>=180)

    def available_spot(self,point,now):
        return not any(e.identity!=self.world.own_id and e.control==1 and e.alive
                       and distance(point,self.world.position(now,e.identity))<100
                       for e in self.world.entities.values())

    def attack_reach(self,target):
        # ATTR_ADIS is not the normal skill's range (unarmed 100, sword150, bow900).
        base=NORMAL_ATTACKS.get(self.world.default_skill,min(100,self.world.own.values.get(ATTACK_DISTANCE,100)))
        return max(40,base+self.world.own.radius+target.radius-20)

    def combat_allowed(self,position):
        rule=getattr(self.nav,'combat_allowed',None)
        return bool(rule(position)) if rule else True

    def cancel_protected_fight(self,now):
        target=self.world.entities.get(self.target)
        if target is None:return
        protected=not self.combat_allowed(self.world.position(now,target.identity))
        own_protected=not self.combat_allowed(self.position(now))
        if not (protected or own_protected):return
        if self.pending_action and self.pending_action[0][8]==2:
            identity=struct.unpack('>III',self.pending_action[0][-12:])[1]
            if identity==target.identity:self.pending_action=None
        if self.action_open and self.last_sent_kind==2:
            self.stop_action();self.protected_fights_stopped+=1
            self.next_action=max(self.next_action,now+.2)
        if protected:
            self.last_protected_target={'map':self.world.map,'model':target.model,
                                        'position':list(self.world.position(now,target.identity))}
            # Exclude its current zone, not its species or permanent identity.
            # It may be selected again once the server moves it outside.
            self.drop_target(now)

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
        if not self.combat_allowed(center):return None
        radius=max(70,reach-65)
        options=[]
        for i in range(12):
            angle=self.approach_angle+i*math.tau/12
            point=(round(center[0]+math.cos(angle)*radius),round(center[1]+math.sin(angle)*radius))
            point=self.nav.nearest(point,1)
            if (point and self.combat_allowed(point) and distance(point,center)<=reach-20
                    and self.available_spot(point,now)):
                options.append(point)
        # Prefer free endpoints, but nearby players must not block every attack
        # position for a shared quest mob. Geometry/path checks still apply.
        if not options and (shared or self.shared_target or target.model in self.quest_models()):
            for i in range(12):
                angle=self.approach_angle+i*math.tau/12
                point=self.nav.nearest((round(center[0]+math.cos(angle)*radius),
                                        round(center[1]+math.sin(angle)*radius)),1)
                if point and self.combat_allowed(point) and distance(point,center)<=reach-20:options.append(point)
        origin=self.position(now)
        options=sorted(set(options),key=lambda pt:distance(origin,pt))
        line_clear=getattr(self.nav,'line_clear',None)
        if line_clear:
            direct=next((point for point in options if line_clear(origin,point)),None)
            if direct:return direct
        for point in options:
            if self.nav.path(origin,point):return point
        return None

    def move_to_recovery(self,now):
        origin=self.position(now)
        if self.stuck>=5:
            if self.retreat_goal:
                self.goal_blacklist[self.retreat_goal]=now+20
                if len(self.goal_blacklist)>128:self.goal_blacklist.pop(next(iter(self.goal_blacklist)))
            self.retreat_replans+=1
            self.retreat_goal=self.move_goal=None
            self.motion_anchor=origin;self.motion_progress_at=now;self.stuck=0
        if self.retreat_goal and distance(origin,self.retreat_goal)>150:
            if self.move_to(self.retreat_goal,now,use_portals=False):return
        self.retreat_goal=None
        mobs=[self.world.position(now,e.identity) for e in self.visible_mobs(now)]
        threats=[point for point in mobs if distance(origin,point)<1800]
        component=self.nav.land_component(origin)
        home=self.home
        if (not threats and distance(origin,home)>300 and self.goal_blacklist.get(home,0)<=now
                and (not component or self.nav.land_component(home)==component)):
            if self.move_to(home,now,use_portals=False):
                self.retreat_goal=home
                return
        if threats:
            clearance=min(distance(origin,point) for point in threats)
            options=[]
            for radius in (1000,500,230):
                for i in range(16):
                    angle=i*math.tau/16
                    point=self.nav.nearest((round(origin[0]+radius*math.cos(angle)),
                                            round(origin[1]+radius*math.sin(angle))),1)
                    if not point or distance(origin,point)<150 or self.goal_blacklist.get(point,0)>now:continue
                    gap=min(distance(point,mob) for mob in threats)
                    if gap<clearance+100 or not self.nav.line_clear(origin,point):continue
                    midpoint=((origin[0]+point[0])/2,(origin[1]+point[1])/2)
                    if min(distance(midpoint,mob) for mob in threats)<clearance-100:continue
                    options.append((gap,point))
                if options:break
            if options:
                _,point=max(options)
                if self.move_to(point,now,use_portals=False):
                    self.retreat_goal=point
                    return
        self.next_action=now+1

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
        if self.last_sent_kind==1:self.cancelled_move_packet=self.move_packet
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
            self.last_attack_skill,*victim=struct.unpack('>III',body[-12:])
            self.last_attack_target=tuple(victim)
            if self.combat_skills:self.combat_skills.sent(self.last_attack_skill,self.clock)
            if self.petcare and self.last_attack_skill==280:self.petcare.possession_sent(self.clock)
            target=self.world.entities.get(self.last_attack_target[0])
            if target and target.control==5:self.learning.begin(self.world,target,self.clock)
        elif body[8]==1:
            if getattr(self.nav,'incremental',False) is True:self.nav.cancel_pending()
            self.move_packet=self.last_sent_sequence
            self.move_map=self.world.map
            count=int.from_bytes(body[9:11],'big')
            self.sent_move_points=tuple(struct.iter_unpack('<ii',body[11:11+count]))
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

    def acknowledged_attack_release(self):
        if not self.fast_progression or not self.pending_action:
            return None
        body,earliest,fallback,revision=self.pending_action
        if body[8]!=2 or self.world.stop_revision==revision or not self.action_stopped():
            return None
        return self.action_release_time(body,earliest,fallback,True)

    def action_release_time(self,body,earliest,fallback,ack):
        if not ack:return fallback
        return earliest-.10 if self.fast_progression and body[8]==2 else earliest

    def flush_action(self,now):
        if not self.pending_action:return False
        body,earliest,fallback,stop_revision=self.pending_action
        ack=(self.world.stop_revision!=stop_revision and self.action_stopped())
        if now<self.action_release_time(body,earliest,fallback,ack):return True
        self.pending_action=None
        kind=body[8];number=int.from_bytes(body[4:8],'big')
        own=self.world.own
        if not own or not own.alive:return True
        if kind==1 and self.move_goal:
            points=(self.nav.movement_segment(self.position(now),self.move_goal)
                    if hasattr(self.nav,'movement_segment') else self.nav.segment(self.position(now),self.move_goal))
            if len(points)<2:return True
            body=movement(own.identity,number,points)
            self.move_sent=now;self.move_revision=self.world.move_revision
            speed=max(100,min(own.values.get(44,480),3000))
            self.move_until=now+sum(distance(a,b) for a,b in zip(points,points[1:]))/speed
        elif kind==2:
            skill,identity,handle=struct.unpack('>III',body[-12:])
            if not skill:return True
            target=self.world.entities.get(identity)
            if not target or not target.alive or target.handle!=handle:return True
            if skill==280 and identity==own.identity and self.petcare and self.petcare.possession_usable(now):
                self.send_action(normal_attack(own.identity,number,body[10],skill,identity,handle,self.position(now)))
                self.flushed_actions+=1;self.next_action=max(self.next_action,now+.2);return True
            healing=bool(self.combat_skills and self.combat_skills.rules.get(skill,{}).get('role')=='heal')
            if healing:
                if not self.combat_skills.healing_target_valid(target,self.party,now):return True
            else:
                if target.control==5 and not self.hunting_level_allowed(target,now):return True
                if not self.combat_allowed(self.position(now)) or not self.combat_allowed(self.world.position(now,identity)):return True
                if self.combat_since is not None and now-self.last_damage_at>=14:return False
            if self.combat_skills and skill in self.combat_skills.rules:
                if not self.combat_skills.usable(skill,now):return True
                reach=self.combat_skills.reach(skill,target)
            elif skill==self.world.default_skill:reach=self.attack_reach(target)
            else:return True
            origin=self.position(now)
            point=self.world.position(now,identity)
            approach=None
            if distance(origin,point)>reach:
                x,y,end_x,end_y=struct.unpack('<iiii',body[13:29])
                expected=(end_x,end_y)
                if (healing or (x,y)==expected or not 0<distance(origin,expected)<=800
                        or not self.combat_allowed(expected) or not self.nav.line_clear(origin,expected)
                        or distance(expected,point)>reach):
                    self.approach_attack_tried=False
                    return False
                approach=expected
            body=normal_attack(own.identity,number,body[10],skill,identity,handle,origin,approach)
        self.send_action(body);self.flushed_actions+=1
        self.next_action=max(self.next_action,now+.2)
        return True

    def position(self,now):
        return self.world.position(now)

    def recover_to_ground(self,now):
        own=self.world.own
        if self.escape_plan and self.escape_plan.tick(now,self):
            self.offmesh_reason=self.escape_plan.reason;return
        motion=self.world.motion.get(self.world.own_id)
        if (self.offmesh_route and motion and self.world.move_state==0 and self.world.move_packet_number==self.last_sent_sequence):
            points,started,speed=motion
            duration=sum(distance(a,b) for a,b in zip(points,points[1:]))/max(1,speed)
            if now<started+min(20,duration+2):
                self.offmesh_reason='сервер подтвердил выход с кромки; продолжает движение';return
        if now<self.offmesh_next:return
        self.offmesh_blocked={c:t for c,t in self.offmesh_blocked.items() if t>now}
        if self.offmesh_origin is not None and distance(own.position,self.offmesh_origin)<50:
            convert=getattr(self.nav,'recovery_cell',self.nav.cell)
            origin_cell=convert(own.position)
            step=next((convert(p) for p in self.offmesh_route if distance(p,own.position)>=50 and convert(p)!=origin_cell),None)
            if step is not None:self.offmesh_blocked[step]=now+30
        scale=2 if getattr(self.nav,'recovery_bits',None) is not None else 1
        blocked=set(self.offmesh_blocked)|{(x*scale+dx,y*scale+dy)
            for x,y in getattr(getattr(self.nav,'local',None),'blocked_cells',())
            for dx in range(scale) for dy in range(scale)}
        route=self.nav.recovery_path(own.position,blocked) if hasattr(self.nav,'recovery_path') else []
        shore_probe=False
        if not route and self.offmesh_batch<4 and hasattr(self.nav,'shore_exit'):
            route=self.nav.shore_exit(own.position,blocked) or self.nav.shore_exit(own.position,blocked,maximum_cm=550)
            shore_probe=bool(route)
        if not route and getattr(self.nav,'recovery_cells',None) is None and getattr(self.nav,'recovery_bits',None) is None:
            # Compatibility with older small grids; new maps use checked egress.
            goal=self.nav.nearest(own.position,3)
            if goal and distance(own.position,goal)<=400:route=[own.position,goal]
        if len(route)<2:
            self.offmesh_reason='нет выхода по физической сетке; повторная проверка через 5 секунд'
            self.offmesh_next=now+5;self.offmesh_route=();self.offmesh_origin=None
            if self.offmesh_since is not None and now-self.offmesh_since>=30:
                if self.stuck_return.tick(now,self):self.offmesh_reason=self.stuck_return.reason
                elif self.stuck_return.reason=='билет требует полные HP и SP':
                    self.sitting.tick(now,self,True);self.offmesh_reason=self.stuck_return.reason
                elif self.stuck_return.reason:self.offmesh_reason+='; '+self.stuck_return.reason
            return
        self.move_goal=None
        self.emit(movement(own.identity,self.sequence,route))
        self.offmesh_requests+=1;self.offmesh_batch+=1
        self.offmesh_origin=own.position;self.offmesh_route=tuple(route)
        seconds=sum(distance(a,b) for a,b in zip(route,route[1:]))/max(100,own.values.get(44,480))
        self.offmesh_next=now+max(2,min(10,seconds+1))
        self.offmesh_reason=('короткая попытка выхода с кромки; ждёт реальное движение сервера' if shore_probe else 'выходит из исключённой клетки по проверенным физическим ячейкам')

    def action_stopped(self):
        if self.last_sent_sequence is None or self.world.stop_packet_number!=self.last_sent_sequence:return False
        kind=self.world.stop_packet_kind
        # A combined move+attack emits a movement INRANGE notification before
        # its fight starts. Only SKILL_SRC termination ends that whole action.
        return kind is None or (self.last_sent_kind==1 and kind==1) or (self.last_sent_kind==2 and kind==3)

    def observe_movement(self,now):
        """Respect real stops before the requested end; do not blacklist our EndAction."""
        w=self.world
        if not self.sent_move_points or self.move_map!=w.map or self.last_sent_kind!=1:return
        origin=self.position(now)
        if w.move_revision!=self.move_stop_seen:
            self.move_stop_seen=w.move_revision
            if (w.move_state and w.move_packet_number==self.move_packet
                    and self.cancelled_move_packet!=self.move_packet
                    and distance(origin,self.move_endpoint)>150):
                self.blocked_move_stops+=1;self.stuck=5
                self.action_open=False;self.move_until=now
                # Locate the rejected forward step, never the occupied origin.
                # Corrections far from the sent route do not imply a new obstacle.
                closest=None
                for a,b in zip(self.sent_move_points,self.sent_move_points[1:]):
                    dx,dy=b[0]-a[0],b[1]-a[1];length=math.hypot(dx,dy)
                    if not length:continue
                    t=max(0,min(1,((origin[0]-a[0])*dx+(origin[1]-a[1])*dy)/(length*length)))
                    projected=(a[0]+dx*t,a[1]+dy*t)
                    score=distance(origin,projected)
                    if t<1 and (closest is None or score<closest[0]):closest=(score,projected,(dx/length,dy/length),length*(1-t))
                if closest and closest[0]<=150 and hasattr(self.nav,'avoid_cell'):
                    _,point,direction,left=closest
                    for step in (80,120,160):
                        step=min(step,left)
                        ahead=(round(point[0]+direction[0]*step),round(point[1]+direction[1]*step))
                        cell=self.nav.cell(ahead)
                        if cell!=self.nav.cell(origin) and self.nav.avoid_cell(cell,now):
                            self.last_blocked_step={'map':w.map,'position':list(self.nav.position(cell)),
                                                    'stop_position':list(origin),'packet':self.move_packet}
                            break
                return
        if self.move_goal and self.cancelled_move_packet!=self.move_packet:
            if distance(origin,self.move_endpoint)<=100:
                self.motion_anchor=origin;self.motion_progress_at=now;return
            if self.motion_anchor is None or distance(origin,self.motion_anchor)>=100:
                self.motion_anchor=origin;self.motion_progress_at=now;self.stuck=0
            elif now-self.motion_progress_at>=10:self.stuck=5

    def acknowledged_move_deadline(self):
        motion=self.world.motion.get(self.world.own_id)
        if motion and self.world.move_packet_number==self.move_packet:
            points,started,speed=motion
            return started+sum(distance(a,b) for a,b in zip(points,points[1:]))/max(1,speed)
        return self.move_until

    def move_to(self, goal, now,use_portals=True):
        self.clock=now
        own=self.world.own
        if (use_portals and self.shortcut and not self.target and not self.resting
                and own and own.values.get(HP,0)>own.values.get(MAX_HP,1)*.55
                and not (self.travel and self.travel.target)
                and self.shortcut.consider(goal,now,self)):
            return True
        self.observe_movement(now)
        if self.stuck>=5:return False
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
                    and now<self.acknowledged_move_deadline()+.5):
                self.move_waits+=1
                return True
        path = (self.nav.movement_segment(origin,goal) if hasattr(self.nav,'movement_segment')
                else self.nav.segment(origin,goal))
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
        if not self.action_open:return False
        if self.last_sent_kind!=2 or self.last_attack_target!=(target.identity,target.handle):return False
        if self.world.failed_actions>self.attack_failure_seen:return False
        if self.action_stopped():return False
        if not self.combat_allowed(self.position(now)) or not self.combat_allowed(self.world.position(now,target.identity)):return False
        # Let the server complete wind-up and subsequent swings. No-progress
        # recovery below still bounds the wait; never cancel a productive fight.
        if self.combat_skills and self.last_attack_skill in self.combat_skills.rules:
            if (self.world.skill_packet_number==self.last_sent_sequence and self.world.skill_action_state is not None
                    and self.world.skill_action_state & (1|16|32|64|128|256|512|1024|2048)):return False
            return now-self.combat_skills.last_sent_at<2
        return now-self.last_damage_at<6

    def mandatory_work(self):
        if self.owner_services:return bool(self.owner_services.profession())
        return (self.world.own.values.get(4)==0 and self.world.own.values.get(LV,0)>=9) or bool(self.career and self.career.eligible())

    def transaction_busy(self):
        return any(feature and feature.busy for feature in (self.market,self.bank,self.direct_trade,self.repair,self.owner_services,self.crafting,self.xp_boosters,self.hunt_travel))

    def opportunity_models(self):
        if self.starter_models():return self.starter_models()
        if not self.region:return self.farm_models()
        return self.learning.choose(self.local_hunting_region(),self.world.own,self.clock,fallback=True,hold=bool(self.target),position=self.position(self.clock))

    def farm_models(self):
        if self.starter_models():return self.starter_models()
        if not self.region:return (71,75)
        return self.learning.choose(self.local_hunting_region(),self.world.own,self.clock,hold=bool(self.target),position=self.position(self.clock))

    def local_hunting_region(self,funding=False):
        if not self.region or not (funding or self.activity.hunting(self.clock)) or not hasattr(self.nav,'land_component'):return self.region
        component=self.nav.land_component(self.position(self.clock))
        if not component:return self.region
        key=(id(self.region),self.world.map,component)
        if getattr(self,'local_region_key',None)!=key:
            farms={}
            for model,record in self.region['farms'].items():
                points=[p for p in record['points'] if self.nav.land_component(p)==component]
                if points:farms[model]=dict(record,points=points)
            self.local_region_key=key;self.local_region=dict(self.region,farms=farms)
        return self.local_region

    def starter_models(self):
        # Owner's CharacterInfo: Forest Spirit 103 is level 3, Argent only.
        preferred=(self.region and self.world.map=='garner'
                        and '103' in self.region['farms'] and self.world.own.values.get(LV,1)<=3
                        and not self.learning.blocked(103,self.clock)
                        and not self.learning.rows)
        if not preferred:return set()
        if self.starter_search_since is None:self.starter_search_since=self.clock
        return {103} if self.clock-self.starter_search_since<90 else set()

    def travel_farm_preference(self,now):
        travel=self.hunt_travel
        if not travel or not travel.preferred_model or travel.plan or now>=travel.site_until:
            return None
        arrival=getattr(travel,'site_arrival',None)
        if arrival:
            name,arrived=arrival
            progress=self.learning.last_progress_at
            if name!=self.world.map or now-max(arrived,progress or arrived)>=90:
                return None
        return travel.preferred_model

    def class_funding_models(self):
        if not self.raising_travel_funds or not self.economy:return set()
        if getattr(self.economy,'all_mobs_patchouli',False):
            return self.economy.weak_funding_models(self.world,self.local_hunting_region(),self.learning,self.clock)
        return self.economy.funding_models(self.world,self.region,self.learning,self.clock)

    def planned_models(self):
        if self.starter_models():return self.starter_models()
        if self.supply_funding_models:return set(self.supply_funding_models)
        preferred=self.travel_farm_preference(self.clock)
        if preferred and self.region and preferred in self.learning.admissible(self.local_hunting_region(),self.world.own,self.clock):
            return {preferred}
        funding=self.class_funding_models()
        if funding:return funding
        group_target=self.group_hunt.target(self.clock) if self.group_hunt else None
        if group_target and self.region and not self.mandatory_work():
            if group_target.model in self.learning.admissible(self.region,self.world.own,self.clock):
                return {group_target.model}
        if self.economy and not self.mandatory_work():
            economic=self.economy.models(self.world,self.region,self.learning,self.clock)
            if economic:return economic
        history=bool(self.economy and self.economy.phase(self.world,self.clock)=='history')
        if self.activity.hunting(self.clock) and not self.mandatory_work() and not history:return set(self.opportunity_models())
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

    def farm_recovery(self,now):
        last=self.learning.last_progress_at
        return bool(self.camp_scouting and self.region and last is not None and now-last>=90
                    and not self.supply_funding_models and not self.mandatory_work() and not self.starter_models()
                    and not self.quest_models() and not self.assist_target
                    and not (self.group_hunt and self.group_hunt.active())
                    and not self.travel_farm_preference(now))

    def reachable_camp_goals(self,raw_goals,now):
        component=self.nav.land_component(self.position(now)) if hasattr(self.nav,'land_component') else None
        goals=dict.fromkeys(self.nav.nearest(p) for p in raw_goals)
        return [p for p in goals if p and self.goal_blacklist.get(p,0)<=now
                and (not component or self.nav.land_component(p)==component)]

    def refresh_farm_plan(self):
        key=(self.world.map,self.world.own.values.get(LV,1),tuple(sorted(self.planned_models())))
        if key!=self.farm_plan_key:
            if self.farm_plan_key is not None:
                self.farm_plan_changes+=1
                # Species scores refresh while the actor is still walking. Keep
                # the current recovery destination if the new goal set validates it.
                if self.farm_plan_key[:2]!=key[:2] or not (self.camp_route_active(self.clock) or self.farm_recovery(self.clock)):
                    self.clear_zone();self.waypoint=0
                    if not self.target:self.move_goal=None
            self.farm_plan_key=key

    def allow_visit(self,point,now,mandatory=False):
        return not self.coordination or self.coordination.visit(self.owner,self.world.map,point,now,mandatory)

    def task(self,key,feature,callback,now):
        if self.group_hunt and self.group_hunt.active() and not self.mandatory_work():
            # A confirmed XP session finishes before optional city errands.
            # Full bags still use unlimited ordinary vendor sales; food can be
            # replenished, and owned gear/books are used earlier in the loop.
            if key in ('market','story','career','adventure'):return False
            if key=='town' and sum(i.count for i in self.world.bag.values() if i.identity==1847)>=2 and not (self.petcare and self.petcare.affordable_care()):return False
        if self.quest_combat_ready and key in ('vendor','market','town','story','career','adventure'):return False
        if key=='market' and self.hunt_before_errands(now):return False
        if (key=='town' and feature and (self.hunt_before_errands(now)
                or (self.hunt_travel and self.hunt_travel.settling_site(now,self)))
                and not (feature.context or feature.pending or feature.combat_supply_required()
                         or (self.petcare and self.petcare.urgent_hunger())
                         or (not self.camp_route_active(now) and self.hunt_travel and self.hunt_travel.plan
                             and not self.hunt_travel.plan.get('returning')
                             and self.hunt_travel.purchase_goals()))):
            return False
        can_sell_full=(key=='market' and (self.world.skills.get(241,{}).get('level',0)>0 or
                       self.world.own.values.get(13,0)>0 and any(i.identity==3296 and i.valid for i in self.world.bag.values())))
        if self.inventory_blocked and key in ('adventure','career','story','market','town') and not can_sell_full:return False
        if self.raising_travel_funds and key in ('adventure','career','story','market','town'):return False
        if self.helper and self.helper.source is not None and not self.mandatory_work():return False
        target=self.world.entities.get(self.target)
        if target and target.alive:return False  # Finish the chosen fight before another errand.
        if key=='adventure' and not self.mandatory_work() and feature:
            destination=feature.choose_destination()
            point=feature.npcs.get(destination)
            if isinstance(point,(tuple,list)) and len(point)==2 and distance(self.position(now),point)>1500:return False
        business=bool(self.economy and self.economy.business(self.world,now) and not self.mandatory_work())
        essential_combat=False;travel_work=False
        if key=='town' and feature and hasattr(feature,'critical_items'):
            critical=feature.critical_items()
            if isinstance(critical,(list,tuple,set)):
                essential_combat=any(i in getattr(feature,'combat_items',()) and 0<feature.life.prices.get(i,0)<=self.world.own.values.get(8,0)-(0 if i in (817,867,635) and feature.life.prices.get(i)==1 else 100) for i in critical)
            # A missing staff/bow cannot be repaired by farming without it.
            # Allow the supplier scan and paid trip even when its shop is in
            # another city and the current-map offers contain no such weapon.
            if hasattr(feature,'combat_supply_required') and feature.combat_supply_required() is True:essential_combat=True
            trip=getattr(feature,'hunt_travel',None)
            travel_work=bool(trip and trip.purchase_goals())
        ready_stall=bool(key=='market' and feature and getattr(feature,'broad_goods',False) and feature.next_shift is not None and now>=feature.next_shift
                         and (not getattr(feature,"progression_first",False) or feature.shift_allowed(self,now))
                         and self.world.own.values.get(0,0)>=feature.minimum_level and self.world.skills.get(241,{}).get('level') and feature.offers(self) and not self.mandatory_work())
        if key=='town' and self.petcare and self.petcare.needs_food_visit():essential_combat=True
        if key=='town' and self.petcare and self.petcare.affordable_care():essential_combat=True
        if key=='repair' and feature and feature.candidates():essential_combat=True
        if (key in ('town','market','story') and not essential_combat and not ready_stall and not self.mandatory_work()
                and self.local_combat_ready(now)):
            return False
        if self.activity.hunting(self.clock) and key!='vendor' and not essential_combat and not travel_work and not ready_stall and not (key in ('adventure','career') and self.mandatory_work()) and not (business and key in ('market','town','story')):return False
        if (key=='vendor' and self.activity.hunting(now) and self.world.bag_ready
                and (self.world.bag_capacity or 0)-len(self.world.bag)>2
                and not self.raising_travel_funds and not self.supply_funding_goal and not (getattr(feature,'sell_patchouli',False) and any(i.identity==1000 for i in self.world.bag.values())) and feature
                and not any(spent_basic(self.world,i) for i in self.world.bag.values())
                and not getattr(feature,'context',None) and not getattr(feature,'pending',None)):
            return False # A stalled optional selling trip must yield to the earned-XP watchdog.
        if not feature or (key!='vendor' and not self.task_budget.allow(key,now)):return False
        point=None
        if self.coordination and feature and not getattr(feature,'context',None):
            if key=='adventure' and not feature.farm():point=feature.npcs.get(feature.choose_destination())
            elif key in ('career','story') and not feature.desired_models():point=feature.quest.get('position')
        if isinstance(point,(tuple,list)) and len(point)==2 and not self.allow_visit(point,now,self.mandatory_work()):
            return False
        if (key=='vendor' and self.adventure and self.adventure.profession_priority()
                and isinstance(self.adventure.farm(),(tuple,list)) and self.world.bag_ready
                and self.world.bag_capacity is not None and self.world.bag_capacity-len(self.world.bag)>2
                and not self.raising_travel_funds and not getattr(feature,'context',None)
                and not getattr(feature,'pending',None)
                and not any(spent_basic(self.world,i) for i in self.world.bag.values())):
            return False  # Finish required farming instead of leaving camp for a small sale.
        optional=key in ('vendor','market','town','story','repair')
        nearby=optional and self.local_combat_ready(now)
        scope=self.nav.background_work(nearby or self.search_goal is not None) if optional and hasattr(self.nav,'background_work') else nullcontext()
        try:
            with scope:used=callback()
        except RoutePending:
            if key not in ('vendor','market','town','story','repair'):raise
            self.background_task=key
            return False  # Keep the planning job, but allow a visible fight/direct move.
        if not used and point and self.coordination:self.coordination.leave_visit(self.owner)
        wanted=getattr(feature,'wanted',None) if key=='town' and used else None
        required_supply=(wanted and wanted[0] in getattr(feature,'combat_items',())
                         and feature.combat_supply_required())
        allowed=self.task_budget.track(key,feature,used,self.position(now),now,progress_only=key=='vendor' or required_supply)
        if used and not allowed:
            if key=='vendor':
                self.task_budget.paused.pop(key,None)
                feature.finish_sale(now)
            elif key=='town':feature.finish(now,180)
            elif key=='repair':feature.finish(now,'маршрут ремонта без прогресса; ищет другой вариант',True)
            elif key=='market':feature.next_scan=now+180
            elif hasattr(feature,'next_visit'):feature.next_visit=now+180
            self.move_goal=None
        return allowed

    def wants_story(self):
        if not self.story:return False
        needed=bool(self.market and self.market.needs_life_study()) or bool(self.professions and self.professions.needs_points())
        historical=bool(self.economy and self.economy.phase(self.world,self.clock)=='history')
        wanted=needed or self.optional_quests or historical
        turn=getattr(self.story,'study_turn',None)
        return (wanted and (needed or historical or not self.activity.hunting(self.clock))
                and (turn(self.clock) if turn else True))

    def target_score(self,entity,now):
        # Prefer reachable nearby fights, weakened targets and useful level-appropriate XP.
        own=self.world.own;maximum=max(1,entity.values.get(MAX_HP,entity.values.get(HP,1)))
        health=entity.values.get(HP,maximum)/maximum
        gap=max(0,own.values.get(LV,1)-entity.values.get(LV,1))
        preference=self.learning.scores.get(entity.model,0)
        return distance(self.position(now),self.world.position(now,entity.identity))+health*200+gap*20-preference*300

    def visible_mobs(self,now):
        cached=getattr(self,'visible_mob_cache',None)
        if cached is None or cached[0]!=now:
            cached=now,tuple(e for e in self.world.entities.values() if e.control==5 and e.alive)
            self.visible_mob_cache=cached
        return cached[1]

    def minimum_xp_mob_level(self,now):
        own=self.world.own
        level=own.values.get(LV,1)
        if not self.region:return max(1,level-MAX_RECOVERY_LEVEL_GAP) if self.fast_progression else 1
        key=(now,self.world.map,id(self.region),level)
        cached=getattr(self,'xp_level_floor_cache',None)
        if cached and cached[0]==key:return cached[1]
        floor=self.learning.minimum_farm_level(self.local_hunting_region(funding=True),own,now)
        self.xp_level_floor_cache=key,floor
        return floor

    def weak_target_exception(self,entity,now):
        if self.assist_target==entity.identity:return 'requested_assist'
        hit=self.world.own_attackers.get(entity.identity)
        if self.fast_progression and hit and hit[0]==entity.handle and 0<=now-hit[1]<=8:
            return 'self_defence'
        if entity.model in self.supply_funding_models:return 'essential_supply_funding'
        if entity.model in self.class_funding_models():return 'class_travel_funding'
        if entity.model in self.quest_models():return 'active_quest'
        return None

    def hunting_level_allowed(self,entity,now):
        return (entity.values.get(LV,0)>=self.minimum_xp_mob_level(now)
                or self.weak_target_exception(entity,now) is not None)

    def visible_ground_opportunities(self,now,origin):
        if (not self.camp_scouting or not self.mob_knowledge or not self.region
                or self.supply_funding_models or self.assist_target
                or self.starter_models() or self.quest_models()
                or (self.group_hunt and self.group_hunt.active())):
            return set()
        own=self.world.own
        level=own.values.get(LV,1)
        floor=self.minimum_xp_mob_level(now)
        max_hp=own.values.get(MAX_HP,1)
        choices=set()
        for candidate in self.visible_mobs(now):
            if (not floor<=candidate.values.get(LV,0)<=level
                    or distance(origin,candidate.position)>2500):
                continue
            record=self.mob_knowledge.get(candidate.model)
            if (record and record['territory']==0 and record.get('base_xp',0)>0
                    and record['hp']<=max_hp*self.learning.profile[3]
                    and not self.learning.blocked(candidate.model,now)):
                choices.add(candidate.identity)
        return choices

    def local_combat_ready(self,now):
        if not self.camp_scouting or not self.world.own or not self.region:
            return False
        cached=getattr(self,'local_combat_cache',None)
        if cached and cached[0]==now:
            return cached[1]
        spell=self.combat_skills.select(now,ignore_cooldown=True) if self.combat_skills else None
        caster=self.combat_skills and self.world.own.values.get(4) in (4,5,13,14,16)
        if not spell and (self.world.default_skill not in NORMAL_ATTACKS
                          or (caster and not self.supply_funding_models)):
            self.local_combat_cache=now,False
            return False
        origin=self.position(now)
        models=self.planned_models()
        opportunities=self.visible_ground_opportunities(now,origin)
        found=False
        for entity in self.visible_mobs(now):
            if distance(origin,entity.position)>1500:
                continue
            if not self.eligible(entity,now,{entity.model} if entity.identity in opportunities else models):
                continue
            point=self.world.position(now,entity.identity)
            reach=self.combat_skills.reach(spell,entity) if spell else self.attack_reach(entity)
            if (distance(origin,point)<=reach and self.combat_allowed(origin)
                    or getattr(self.nav,'line_clear',lambda *a:False)(origin,point)):
                found=True
                break
        self.local_combat_cache=now,found
        return found

    def target_explanation(self):
        target=self.world.entities.get(self.target)
        if not target:return None
        level=self.world.own.values.get(LV,1);ml=target.values.get(LV)
        reason=self.farm_reason()
        floor=self.minimum_xp_mob_level(self.clock)
        return {'identity':target.identity,'model':target.model,'level':ml,
                'character_level':level,'level_gap':level-ml if ml is not None else None,
                'minimum_xp_mob_level':floor,
                'level_xp_divisor':xp_level_divisor(level,ml) if ml else None,
                'weak_target_exception':self.weak_target_exception(target,self.clock) if ml and ml<floor else None,
                'quest_required':target.model in self.quest_models(),
                'selection_source':reason['source'],
                'opportunity':target.model==self.opportunity_model,
                'distance_cm':distance(self.position(self.clock),self.world.position(self.clock,target.identity)),
                'learning':self.learning.candidate_details.get(target.model)}

    def eligible(self, entity, now, models=None):
        if (entity.control!=5 or not entity.alive or not entity.handle
                or (self.assist_target and entity.identity!=self.assist_target)):
            return False
        own = self.world.own
        if not self.hunting_level_allowed(entity,now):return False
        if self.mob_knowledge:
            record=self.mob_knowledge.get(entity.model)
            if record and record.get('territory')!=0:return False
        models=set(models) if models is not None else ({self.world.entities[self.assist_target].model} if self.assist_target in self.world.entities else self.planned_models())
        if entity.identity==self.target and self.opportunity_model:models=set(models)|{self.opportunity_model}
        if self.region and self.world.map!='garner' and own.values.get(LV,1)<=3:return False
        maximum_level = own.values[LV] if self.region or self.adventure else min(2,own.values[LV]+1)
        if self.starter_models() and not self.assist_target and models==self.starter_models():
            models=self.starter_models();maximum_level=3
        elif self.region:
            maximum_level=max([maximum_level]+[self.region['farms'][str(m)]['level'] for m in models if str(m) in self.region['farms']])
        valid=(entity.model in models and 0 < entity.values.get(LV, 9999) <= maximum_level
                and distance(entity.position, self.home) <= (600000 if self.region else 45000 if self.adventure else 22000)
                and self.blacklist.get(entity.identity, 0) < now and not self.learning.dangerous(entity.model,now))
        if not valid:return False
        point=self.world.position(now,entity.identity) or entity.position
        if not self.combat_allowed(point):
            self.protected_target_checks+=1
            self.last_protected_target={'map':self.world.map,'model':entity.model,'position':list(point)}
            return False
        return True

    def nearby_attacker(self,now):
        own=self.world.own
        if not self.fast_progression or not own or self.assist_target or self.resting:
            return None
        if own.values.get(HP,0)<=own.values.get(MAX_HP,1)*.55:
            return None
        origin=self.position(now)
        if not self.combat_allowed(origin):return None
        for identity,(handle,stamp) in reversed(self.world.own_attackers.items()):
            if not 0<=now-stamp<=8:continue
            mob=self.world.entities.get(identity)
            if (mob and mob.handle==handle and distance(origin,mob.position)<=1200
                    and self.eligible(mob,now,{mob.model}) and not self.learning.dangerous(mob.model,now)):
                return mob
        return None

    def wake_for_combat(self,now):
        if (not self.fast_progression or now<self.next_combat_wake or self.resting
                or self.transaction_busy()
                or any(getattr(f,'context',None) or getattr(f,'pending',None)
                       for f in (self.town,self.vendor,self.petcare,self.equipment) if f)):
            return False
        attacker=self.nearby_attacker(now)
        if self.pending_action:
            body,earliest,_,stop_revision=self.pending_action
            defence=bool(attacker and body[8]==1)
            ack=self.world.stop_revision!=stop_revision and self.action_stopped()
            ready=(body[8]==2 and ack and now>=self.action_release_time(body,earliest,earliest,True))
            if not (defence or ready):return False
        else:
            target=self.world.entities.get(self.target)
            if target and target.alive and not attacker:return False
        self.next_combat_wake=now+.1
        self.next_action=min(now,self.next_action)
        self.combat_wakes+=1
        return True

    def send_in_range_attack(self,now,target,spell,funding_attack=False):
        own=self.world.own
        if self.combat_since is None:self.combat_since=self.last_damage_at=now
        self.change('применяет боевой навык '+str(spell) if spell else
                    'бьёт слабого моба ради Пачкули' if funding_attack else 'обычная атака')
        self.fight=(self.fight+1)&255
        self.emit(normal_attack(own.identity,self.sequence,self.fight,spell or self.world.default_skill,
                                target.identity,target.handle,self.position(now)))
        self.world.freeze_prediction(now)
        self.move_goal=None
        if self.loot:self.loot.note_attack(target.identity,now)
        self.next_action=now+(.15 if spell else self.attack_interval)

    def immediate_defence(self,now,target):
        if not target or self.target or self.pending_action or self.transaction_busy():
            return False
        if self.world.failed_actions!=self.attack_failure_seen:
            return False
        if any(getattr(f,'context',None) or getattr(f,'pending',None) for f in
               (self.town,self.vendor,self.petcare,self.equipment,self.shortcut) if f):
            return False
        own=self.world.own
        spell=self.combat_skills.select(now) if self.combat_skills else None
        if not spell and (self.world.default_skill not in NORMAL_ATTACKS
                           or (self.combat_skills and own.values.get(4) in (4,5,13,14,16))):
            return False
        reach=self.combat_skills.reach(spell,target) if spell else self.attack_reach(target)
        if distance(self.position(now),self.world.position(now,target.identity))>reach:
            return False
        key=self.world.map,target.identity,target.handle
        if self.coordination and not self.coordination.claim(self.owner,key,now,shared=True):
            return False
        self.target=target.identity;self.target_key=key
        self.shared_target=True;self.opportunity_model=target.model
        self.target_since=self.last_target_at=now
        self.last_target_hp=target.values.get(HP)
        self.clear_zone()
        self.send_in_range_attack(now,target,spell)
        self.immediate_defences+=1
        return True

    def attack_on_approach(self,now,target,goal,spell,ranged):
        if (not self.fast_progression or self.approach_attack_tried or not goal
                or (self.action_open and not self.action_stopped() and self.last_sent_kind!=1)
                or self.world.failed_actions!=self.attack_failure_seen):
            return False
        own=self.world.own
        if not spell and ranged and own.values.get(4) in (4,5,13,14,16):return False
        skill=spell or self.world.default_skill
        if not skill:return False
        origin=self.position(now)
        reach=self.combat_skills.reach(spell,target) if spell else self.attack_reach(target)
        if (not 0<distance(origin,goal)<=800 or not self.combat_allowed(origin)
                or not self.combat_allowed(goal) or not self.nav.line_clear(origin,goal)
                or distance(goal,self.world.position(now,target.identity))>reach):
            return False
        self.fight=(self.fight+1)&255
        self.emit(normal_attack(own.identity,self.sequence,self.fight,skill,target.identity,target.handle,origin,goal))
        self.approach_attack_tried=True
        self.approach_attacks+=1
        self.move_goal=None
        self.combat_since=self.last_damage_at=now
        if self.loot:self.loot.note_attack(target.identity,now)
        self.next_action=now+.15
        self.change('подходит и атакует одной командой')
        return True

    def leave_goldie_area(self,now):
        last=self.learning.last_progress_at
        if self.world.map!='garner' or last is None or now-last<90 or self.target:
            return False
        position=self.position(now)
        goal=(219650,272350)
        if distance(position,goal)<=150 or now<self.goldie_exit_retry:
            return False
        if self.move_goal!=goal and distance(position,(219750,270400))>450:
            return False
        if not self.nav.line_clear(position,goal):
            self.goldie_exit_retry=now+60
            return False
        if self.stuck>=5:
            if self.move_goal==goal:
                self.goldie_exit_retry=now+60
                return False
            self.stuck=0
        if not self.move_to(goal,now,use_portals=False):
            self.goldie_exit_retry=now+60
            return False
        self.change('выходит от кузнеца по проверенному проходу')
        return True

    def tick(self,now=None):
        nav=self.nav;incremental=getattr(nav,'incremental',False) is True
        from route_search import RoutePending
        previous,since=self.mode,self.mode_since
        if hasattr(nav,'expire_obstacles'):nav.expire_obstacles(time.monotonic() if now is None else now)
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
        self.background_task=None
        # Recompute per decision: a previous quest fight must not suppress the
        # NPC visit after objective review switches from farming to verification.
        self.quest_combat_ready=False
        own = self.world.own
        if own:self.learning.record_progress(own,now)
        self.progress_monitor.tick(now,self)
        if own and (own.values.get(HP,1)<=0 or own.state>=5):
            if self.shortcut and self.shortcut.busy:self.shortcut.abort(now,'персонаж погиб')
            self.learning.observe(self.world,now)
            self.pending_action=None;self.action_open=False
            self.sitting.reset()
            self.retreat_goal=None
            if self.market and self.market.state in ('opening','selling','closing'):self.market.request_close(now)
            if self.bank and self.bank.busy:self.bank.end(now)
            if self.direct_trade and self.direct_trade.busy:self.direct_trade.cancel('персонаж погиб')
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
        if self.target:
            previous_target=self.world.entities.get(self.target)
            if not previous_target or not previous_target.alive:
                hit=self.world.own_hits.get(self.target)
                credited=bool(hit and hit[1] and hit[0]>=self.target_since)
                if credited:self.own_hit_deaths+=1
                if credited or (previous_target and previous_target.values.get(HP,1)<=0):
                    self.kills+=1
                self.drop_target()
                self.next_action=min(now,self.next_action)
        if self.town and (self.town.context or self.town.pending):
            # Finish an already-open merchant exchange before optional task
            # gates, which can reject shopping as soon as its goal is fulfilled.
            self.town.tick(now,self,False)
            if self.town.context or self.town.pending:
                self.change('ожидает подтверждение операции торговца')
                self.next_action=now+.2
                return
        if self.stuck_return.pending and self.pending_action:
            self.flush_action(now)
        if self.stuck_return.poll(now,self):
            self.change(self.stuck_return.reason);return
        if self.repair and self.repair.busy:
            if self.repair.tick(now,self,False):self.change(self.repair.reason or 'ожидает ремонт от сервера');return
        self.cancel_protected_fight(now)
        if self.refresh_class_intent:self.refresh_class_intent()
        if self.adventure and hasattr(self.adventure,'review_objective'):
            current=self.world.entities.get(self.target)
            self.adventure.review_objective(now,busy=bool(current and current.alive))
        prior_funding=self.supply_funding_goal
        self.supply_funding_goal=0
        self.supply_funding_models=set()
        if (self.economy and getattr(self.economy,'all_mobs_patchouli',False) and self.town and self.region
                and self.world.bag_ready and not self.world.bag_disabled and not self.mandatory_work() and not self.assist_target):
            repair_cost=self.repair.weapon_funding_target() if self.repair else 0
            budget=self.town.essential_funding_target(repair_cost)
            if self.hunt_travel:
                budget=max(budget,self.hunt_travel.funding_target())
            if own.values.get(8,0)<budget:
                if not prior_funding and self.search_goal and not self.paused_camp:
                    self.paused_camp=(self.world.map,self.search_goal,now+900)
                self.supply_funding_goal=budget
                self.supply_funding_models=self.economy.weak_funding_models(
                    self.world,self.local_hunting_region(funding=True),self.learning,now)
        current=self.world.entities.get(self.target)
        if current and current.alive and not self.hunting_level_allowed(current,now):
            if self.pending_action and self.pending_action[0][8]==2:
                if struct.unpack('>I',self.pending_action[0][-8:-4])[0]==current.identity:self.pending_action=None
            self.next_action=min(now,self.next_action)
            if self.action_open and not self.action_stopped() and self.last_attack_target==(current.identity,current.handle):
                self.stop_action()
                self.next_action=now+.2
            self.drop_target()
            self.learning.until=0
        self.update_tactic(now)
        if self.economy:
            self.economy.camp_hunting=self.hunt_before_errands(now)
            self.economy.group_hunting=bool(self.group_hunt and self.group_hunt.active())
            target=self.world.entities.get(self.target)
            self.economy.busy=bool(self.group_hunt and self.group_hunt.active()) or bool(target and target.alive) or self.transaction_busy() or bool(self.pending_action) or any(
                getattr(f,'context',None) or getattr(f,'pending',None) for f in (self.town,self.vendor,self.adventure,self.career,self.story,self.petcare,self.professions) if f)
        completed=sum(getattr(f,'delivered',0) for f in (self.adventure,self.career,self.story) if f and isinstance(getattr(f,'delivered',0),int))
        protected=self.resting or self.transaction_busy() or bool(self.town and self.town.rest_until)
        if own:self.activity.update(now,own.values.get(LV),own.values.get(15),self.kills,completed,protected)
        if own:self.refresh_farm_plan()
        if own and self.world.map==self.nav.map and not self.nav.free(self.nav.cell(self.position(now))) and not (self.offmesh_route and self.world.move_state==0 and self.world.move_packet_number==self.last_sent_sequence):
            # A server correction can invalidate interpolation; prefer its raw position.
            self.world.motion.pop(self.world.own_id,None)
        needs_recovery=(own and (self.nav.needs_recovery(self.position(now)) if hasattr(self.nav,'needs_recovery')
                                else not self.nav.free(self.nav.cell(self.position(now)))))
        if own and own.alive and needs_recovery and not self.pending_action and not self.transaction_busy() and not any(getattr(f,'context',None) for f in (self.town,self.vendor,self.career,self.story,self.travel,self.adventure) if f):
            if self.petcare and self.petcare.urgent_hunger() and self.petcare.tick(now,self,safe=True):
                self.change(self.petcare.reason);return
            if self.equipment and self.equipment.tick(now,self,True):
                self.change('надевает рабочую экипировку перед выходом с кромки');return
        if not own or self.world.map != self.nav.map or needs_recovery:
            self.change('ожидание достоверных данных карты')
            if self.pending_action and own and own.alive:
                if self.flush_action(now):return
            if own and own.alive and self.world.map==self.nav.map:
                if self.offmesh_since is None:self.offmesh_since=now
                self.recover_to_ground(now)
                self.change(self.offmesh_reason or 'проверяет выход на сушу')
            return
        self.offmesh_batch=0
        self.offmesh_since=None
        self.offmesh_route=();self.offmesh_origin=None;self.offmesh_reason=''
        hp, maximum = own.values.get(HP), own.values.get(MAX_HP)
        if hp is None or not maximum:
            self.change('ожидание данных здоровья')
            return
        if self.learning.waiting_reward(now):
            self.change('проверяет опыт после боя');self.next_action=now+.15;return
        if self.adventure and self.adventure.prepare_priority():
            self.task_budget.paused.pop('adventure',None)
            self.task_budget.rows.pop('adventure',None)
        self.observe_movement(now)
        defence=self.nearby_attacker(now)
        if defence and self.target and self.target!=defence.identity and self.combat_since is None:
            self.drop_target()
        if defence and not self.target:
            if self.pending_action and self.pending_action[0][8]==1:
                _,earliest,fallback,revision=self.pending_action
                acknowledged=self.world.stop_revision!=revision and self.action_stopped()
                if now>=earliest and (acknowledged or now>=fallback):
                    self.pending_action=None
                    self.move_goal=None
            self.next_action=min(now,self.next_action)
        before_flush=self.flushed_actions
        if self.flush_action(now):
            if self.pending_action:self.change('ожидание завершения предыдущего действия')
            elif self.flushed_actions>before_flush:
                self.change('маршрут отправлен' if self.last_sent_kind==1 else 'атака отправлена; ожидает результат' if self.last_sent_kind==2 else 'действие с предметом отправлено')
            else:self.change('повторная проверка цели после остановки')
            return
        if self.crafting and self.crafting.busy:
            if self.crafting.tick(now,self):self.change(self.crafting.reason);self.next_action=now+.15;return
        if self.xp_boosters and self.xp_boosters.busy:
            if self.xp_boosters.tick(now,self,False):self.change(self.xp_boosters.reason);self.next_action=now+.2;return
        if self.hunt_travel and self.hunt_travel.busy:
            if self.hunt_travel.tick(now,self,False):self.change(self.hunt_travel.reason);self.next_action=now+.2;return
        if (not defence and hp/maximum>.55 and self.petcare and self.petcare.urgent_hunger() and not self.transaction_busy()
                and self.petcare.tick(now,self,safe=True,dialogue_busy=any(getattr(f,'context',None) for f in (self.town,self.vendor,self.travel,self.career,self.story) if f))):
            self.change(self.petcare.reason);self.next_action=now+.2;return

        if self.direct_trade and self.direct_trade.busy:
            self.drop_target();self.clear_zone()
            if self.direct_trade.tick(now,self):
                self.change(self.direct_trade.reason or 'личная торговля');return
        if self.market and self.market.busy:
            if self.petcare and self.petcare.needs_food_visit() and self.market.state in ('opening','selling'):
                self.market.request_close(now)
            self.drop_target();self.clear_zone()
            self.market.tick(now,self,hp/maximum>.55)
            self.change(self.market.reason or 'ожидание торговли');return
        if self.bank and self.bank.busy:
            self.drop_target();self.clear_zone()
            if self.bank.tick(now,self,hp/maximum>.55):
                self.change(self.bank.reason or 'проверяет перемещение вещей в банке');return
        if self.recovery and self.recovery.tick(now,self):
            self.next_action=now+.3
            return
        if not self.resting and self.sitting.tick(now,self,False):
            self.change('встаёт перед продолжением дел');return
        # A learned heal can prevent the retreat; one-shot native targeted cast.
        if self.combat_skills and not self.pending_action:
            heal=self.combat_skills.select(now,healing=True)
            patient=self.combat_skills.healing_target(heal,self.party,now) if heal else None
            if patient:
                self.fight=(self.fight+1)&255
                self.emit(normal_attack(own.identity,self.sequence,self.fight,heal,patient.identity,patient.handle,self.position(now)))
                self.change('применяет лечение');self.next_action=now+.5;return
        if self.combat_skills and self.combat_skills.needs_mana(now):
            self.mana_resting=True;self.resting=True;self.drop_target();self.clear_zone()
        profession_trip = bool(self.adventure and self.adventure.profession_priority() and not self.adventure.farm())
        recent_loss=sum(amount for stamp,amount in self.world.own_recent_damage if 0<=now-stamp<=3)
        retreat_hp=max(maximum*.35,min(maximum*.60,recent_loss*1.5))
        if hp <= retreat_hp or (profession_trip and not self.target and hp / maximum <= .55):
            if not self.resting:
                self.cancel_pending = True
            self.resting = True
            self.drop_target()
            self.clear_zone()
        if self.resting:
            if hp / maximum >= .85 and not (self.mana_resting and self.combat_skills and self.combat_skills.needs_mana(now,True)):
                if self.sitting.tick(now,self,False):
                    self.change('встаёт после восстановления');return
                self.resting = False;self.mana_resting=False;self.retreat_goal=None
            else:
                self.change('восстанавливает SP для боевых навыков' if self.mana_resting else 'отступление и восстановление')
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
                if now >= self.next_action:
                    self.move_to_recovery(now)
                return
        if self.shortcut and self.shortcut.busy and (not defence or self.shortcut.context or self.shortcut.ticket):
            if self.shortcut.resume(now,self):
                self.change(self.shortcut.reason);return
        if now < self.next_action or now-self.started < 2:
            return
        if self.immediate_defence(now,defence):
            return
        if self.owner_services and self.owner_services.busy:
            if self.owner_services.tick(now,self,False):
                self.change(self.owner_services.reason);return
        if self.skills and self.skills.pending:self.skills.tick(now,self,False)
        if self.chests and self.chests.pending:
            self.chests.tick(now,self,False)
            if self.chests.pending:
                self.change('ожидает содержимое сундука от сервера');self.next_action=now+.2;return
        if (self.professions and not self.transaction_busy() and
                self.professions.tick(now,self,safe=not self.target,dialogue_busy=any(getattr(f,'context',None) for f in (self.town,self.vendor,self.travel,self.adventure,self.career,self.story) if f))):
            self.change(self.professions.reason);self.next_action=now+.2;return
        if (self.petcare and not self.transaction_busy() and
                self.petcare.tick(now,self,safe=not self.target,dialogue_busy=any(getattr(f,'context',None) for f in (self.town,self.vendor,self.travel,self.adventure,self.career,self.story) if f))):
            self.change(self.petcare.reason);self.next_action=now+.2;return
        if self.equipment and self.equipment.tick(now,self,safe=not self.target and not defence):
            self.next_action=now+.2
            self.change('надевает подходящую экипировку')
            return
        repair_safe=(not self.target and not self.resting and hp/maximum>.55 and not self.transaction_busy()
                     and not any(getattr(f,'context',None) or getattr(f,'pending',None) for f in (self.town,self.vendor,self.adventure,self.career,self.story,self.travel,self.petcare) if f))
        if self.repair and repair_safe and self.repair.candidates() and self.task('repair',self.repair,lambda:self.repair.tick(now,self,repair_safe),now):
            self.change(self.repair.reason);return
        if self.skills and self.skills.tick(now,self,safe=not self.target):
            self.next_action=now+.2
            self.change('изучает навыки своего класса')
            return
        if self.fast_progression and not self.transaction_busy() and self.leave_goldie_area(now):
            return
        if self.stuck >= 5 and now>=self.next_recovery:
            self.recover_path(now)
            return
        dialogue_busy=bool(self.adventure and self.adventure.context)
        safe=not self.target and not defence and not self.resting and hp/maximum>.55
        market_dialogue=dialogue_busy or any(getattr(f,'context',None) or getattr(f,'pending',None) for f in (self.town,self.career,self.story,self.equipment,self.skills,self.chests,self.party,self.vendor) if f)
        mandatory=(own.values.get(4)==0 and own.values.get(0,1)>=9) or bool(self.career and self.career.eligible())
        self.quest_combat_ready=False
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
            waiting_retry=bool(self.adventure.journal_ready and not self.adventure.context
                               and not self.adventure.pending and
                               (now<self.adventure.next_visit or not self.task_budget.allow('adventure',now)))
            if not waiting_retry:
                self.change('первая профессия: '+self.adventure.reason)
                self.next_action=now+.5
                return
            # A real NPC/path retry delay must not become a whole-AI pause.
            # Finish useful nearby work, then give the teacher priority again.
            self.change('визит к учителю отложен; продолжает охоту до повторной попытки')
        kill_task=self.adventure.farm() if self.adventure else None
        self.quest_combat_ready=bool(first_profession and isinstance(kill_task,(tuple,list))
            and len(kill_task)==2 and kill_task[0] and kill_task[1] is None
            and not self.inventory_blocked and not market_dialogue
            and not (self.travel and self.travel.context)
            and any(e.model==kill_task[0] and self.eligible(e,now)
                    and distance(self.position(now),self.world.position(now,e.identity))<=2000
                    for e in self.world.entities.values()))
        business=bool(self.economy and self.economy.business(self.world,now) and not mandatory)
        if not mandatory and not self.quest_combat_ready and self.group_hunt and self.group_hunt.work(now,self,safe):return
        if business and not self.quest_combat_ready:
            if self.wants_story() and (self.economy.phase(self.world,now)=='history' or (self.market and self.market.needs_life_study()) or (self.professions and self.professions.needs_points())) and self.task('story',self.story,lambda:self.story.tick(now,self,safe,market_dialogue),now):
                self.drop_target();self.clear_zone();self.change('получает очки жизненных навыков для ларька');return
            if self.task('town',self.town,lambda:self.town.tick(now,self,safe,market_dialogue),now):
                self.drop_target();self.pause_camp(now);self.change(self.town.reason);return
        if not self.quest_combat_ready and not self.raising_travel_funds and self.helper and self.helper.tick(now,self):return
        loot_dialogue=market_dialogue or any(getattr(f,'context',None) for f in (self.travel,self.market) if f)
        if self.hunt_travel and not self.transaction_busy():
            mine_approach=getattr(self.hunt_travel,'mine_approach',lambda:False)
            scope=self.nav.background_work(True) if hasattr(self.nav,'background_work') and not mine_approach() else nullcontext()
            try:
                with scope:
                    travelling=self.hunt_travel.tick(now,self,safe,loot_dialogue)
            except RoutePending:
                self.background_task='hunt_travel'
                if mine_approach():
                    self.clear_zone()
                    self.change('строит путь к выбранному входу в шахту')
                    return
                travelling=False
            if travelling:
                self.drop_target();self.clear_zone();self.change(self.hunt_travel.reason);return
        if self.owner_services and not (self.target and self.world.entities.get(self.target) and self.world.entities[self.target].alive):
            if self.owner_services.tick(now,self,safe,loot_dialogue or bool(self.town and self.town.context)):
                self.drop_target();self.clear_zone();self.change(self.owner_services.reason);return
        if not defence and not loot_dialogue and not self.quest_combat_ready:
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
                if self.market:
                    needed.update(self.market.loot_needs())
                    self.loot.value_priority={i:(0 if i==684 else 1 if m['category'] in ('gear','sealed') else 2) for i,m in self.market.catalog.items.items()}
                if self.vendor:needed.update(self.vendor.junk)
                if self.skills and self.skills.catalog:needed.update(self.skills.catalog.books)
                if self.chests and self.world.bag_ready and not self.world.bag_disabled:
                    free=(self.world.bag_capacity or 0)-len(self.world.bag)
                    if free>4:needed.update(item[0] for item in self.world.items.values() if item[0] in self.chests.catalog.names)
                if self.owner_services:
                    from owner_services import LOOT
                    needed=set(LOOT)
                if self.vendor and self.vendor.sell_patchouli:
                    needed.add(1000);self.loot.value_priority[1000]=0
                for identity in self.loot.ground_gems:
                    if identity in needed:self.loot.value_priority[identity]=0
                if self.loot.tick(now,self,needed):
                    self.change('подбор нужного лута; результат подтверждает сервер')
                    return
        if not self.quest_combat_ready and self.travel and (not self.activity.hunting(now) or self.mandatory_work() or self.travel.starter_trip()) and not (self.helper and self.helper.active(now)) and self.travel.tick(now,self,safe,market_dialogue):
            self.drop_target();self.clear_zone();self.change(self.travel.reason);return
        if self.task('vendor',self.vendor,lambda:self.vendor.tick(now,self,safe,market_dialogue),now):
            self.drop_target();self.pause_camp(now);self.change(self.vendor.reason);return
        bank_available=self.bank and not mandatory and not (self.group_hunt and self.group_hunt.active())
        relief=(self.fast_progression and self.world.bag_ready and self.world.bag_capacity is not None
                and self.world.bag_capacity-len(self.world.bag)<=1)
        if bank_available and relief and self.bank.tick(now,self,safe,market_dialogue):
            self.drop_target();self.pause_camp(now);self.change(self.bank.reason);return
        if self.treasure and not mandatory and not self.raising_travel_funds and not self.supply_funding_goal and self.treasure.tick(now,self,safe,market_dialogue):
            self.drop_target();self.clear_zone();self.change(self.treasure.reason);return
        if self.economy and self.economy.business(self.world,now) and self.task('market',self.market,lambda:self.market.tick(now,self,safe and not mandatory,market_dialogue),now):
            self.drop_target();self.clear_zone();self.change(self.market.reason or 'городская торговля');return
        if bank_available and not relief and (not self.activity.hunting(now) or business) and self.bank.tick(now,self,safe,market_dialogue):
            self.drop_target();self.pause_camp(now);self.change(self.bank.reason);return
        if self.task('market',self.market,lambda:self.market.tick(now,self,safe and not mandatory,market_dialogue),now):
            self.drop_target();self.clear_zone();self.change(self.market.reason or 'торговые дела');return
        if not self.quest_combat_ready and self.chests and self.chests.tick(now,self,safe):
            self.change('открывает собственный сундук');self.next_action=now+.3;return
        if self.task('career',self.career,lambda:self.career.tick(now,self,safe,dialogue_busy or bool(self.town and self.town.context) or bool(self.story and self.story.context)),now):
            self.drop_target();self.clear_zone();self.change(self.career.reason);return
        if self.wants_story() and self.task('story',self.story,lambda:self.story.tick(now,self,safe,dialogue_busy or bool(self.town and self.town.context) or bool(self.career and self.career.context)),now):
            self.drop_target();self.clear_zone();self.change('сюжетное задание: жизненные навыки');return
        if self.task('town',self.town,lambda:self.town.tick(now,self,safe,dialogue_busy or bool(self.career and self.career.context) or bool(self.story and self.story.context)),now):
            self.drop_target();self.pause_camp(now);self.change(self.town.reason);return
        if self.crafting and self.crafting.tick(now,self,safe,market_dialogue):
            self.drop_target();self.clear_zone();self.change(self.crafting.reason);return
        if self.xp_boosters and self.xp_boosters.tick(now,self,safe,market_dialogue):
            self.change(self.xp_boosters.reason);self.next_action=now+.2;return
        if self.task('adventure',self.adventure,lambda:self.adventure.tick(now,self),now):
            self.drop_target()
            self.clear_zone()
            self.change(self.adventure.reason)
            return
        shared_models=self.quest_models()
        caster=own.values.get(4) in (4,5,13,14,16) and self.combat_skills
        needs_spell=bool(caster and not self.combat_skills.select(now,ignore_cooldown=True))
        funding_attack=bool(needs_spell and self.supply_funding_models and self.world.default_skill in NORMAL_ATTACKS)
        if (needs_spell and not funding_attack
                and not (self.owner_services and self.combat_skills.training_weapon_bridge())):
            self.drop_target();self.change('готовит магию: '+(self.combat_skills.reason or 'нужен изученный боевой навык и подходящее снаряжение'))
            self.next_action=now+.5;return
        target = self.world.entities.get(self.target)
        if target and funding_attack and target.model not in self.supply_funding_models:
            self.drop_target()
            target=None
        if target:
            stopped=(self.world.skill_packet_number==self.last_sent_sequence
                     and self.world.skill_action_state is not None
                     and self.world.skill_action_state & (16|64|512)
                     and self.last_sent_kind==2)
            failed=self.world.last_failed_action
            disappeared=(self.world.failed_actions>self.attack_failure_seen and failed
                         and failed['actor']==own.identity and failed['action']==2 and failed['reason']==5)
            if stopped or disappeared:
                if stopped and self.world.skill_action_state & 64:self.immune_fights_released+=1
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
        selected_approach=None
        if not target:
            origin=self.position(now)
            visible=self.visible_ground_opportunities(now,origin)
            models=None if self.assist_target else self.planned_models()
            mobs=self.visible_mobs(now)
            candidates=[e for e in mobs if self.eligible(e,now,{e.model} if e.identity in visible else models)]
            if defence and defence not in candidates:candidates.append(defence)
            self.rng.shuffle(candidates)  # Distinct tie ordering for each character.
            candidates.sort(key=lambda e:self.target_score(e,now))
            group_target=self.group_hunt.target(now) if self.group_hunt else None
            if group_target:candidates.sort(key=lambda e:e.identity!=group_target.identity)
            if self.region and now-self.last_target_at>=20 and not self.assist_target and not self.supply_funding_models:
                known={e.identity for e in candidates}
                models=self.learning.admissible(self.local_hunting_region(),own,now,recovery=self.farm_recovery(now))
                extras=[e for e in mobs if e.identity not in known and self.eligible(e,now,models)]
                extras.sort(key=lambda e:self.target_score(e,now))
                candidates.extend(extras)
            approach_spell=(self.combat_skills.select(now,ignore_cooldown=True)
                            if self.combat_skills and not funding_attack else None)
            can_attack_here=self.combat_allowed(origin)
            reaches={candidate.identity:(self.combat_skills.reach(approach_spell,candidate)
                                           if approach_spell else self.attack_reach(candidate))
                     for candidate in candidates}
            in_range={candidate.identity for candidate in candidates if can_attack_here
                      and distance(origin,self.world.position(now,candidate.identity))<=reaches[candidate.identity]}
            # Within each level band, try in-range targets before pathfinding.
            preferred_floor=max(1,own.values.get(LV,1)-PREFERRED_LEVEL_GAP)
            candidates.sort(key=lambda candidate:(
                candidate is not defence if defence else False,
                not (candidate.values.get(LV,0)>=preferred_floor or candidate.model in shared_models
                     or self.raising_travel_funds or self.supply_funding_models),
                candidate.identity not in in_range))
            # Prefer unclaimed reachable mobs. If every viable target is busy,
            # join a real fight instead of waiting for another bot's lease.
            # Active quest mobs can be shared on the first pass.
            waiting_route=False
            for join_busy in (False,True):
                for candidate in candidates:
                    shared=join_busy or candidate is defence or candidate.model in shared_models or bool(group_target and candidate.identity==group_target.identity)
                    key=(self.world.map,candidate.identity,candidate.handle)
                    if self.coordination and not self.coordination.available(self.owner,key,now,shared=shared):
                        self.busy_targets+=1
                        continue
                    approach_point=None
                    if candidate.identity not in in_range:
                        try:
                            approach_point=self.approach(candidate,reaches[candidate.identity],now,shared=shared)
                        except RoutePending:
                            waiting_route=True
                            continue
                        if approach_point is None:continue
                    if self.coordination and not self.coordination.claim(self.owner,key,now,shared=shared):continue
                    target=candidate
                    selected_approach=approach_point
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
            if target is None and waiting_route:raise RoutePending()
        if target:
            spell=(self.combat_skills.select(now) or self.combat_skills.control(now)) if self.combat_skills and not funding_attack else None
            ranged=self.combat_skills.select(now,ignore_cooldown=True) if self.combat_skills else None
            # Finish a current one-shot cast; a ready spell may replace repeating melee.
            casting=bool(self.combat_skills and self.last_attack_skill in self.combat_skills.rules
                         and self.fight_running(target,now))
            if casting or (not spell and self.fight_running(target,now)):
                self.active_fight_waits+=1
                self.change('продолжает бой: ожидает следующий серверный удар')
                self.next_action=now+.25
                return
            reach = self.combat_skills.reach(ranged or spell,target) if (ranged or spell) else self.attack_reach(target)
            if (not self.combat_allowed(self.position(now)) or
                    distance(self.position(now),self.world.position(now,target.identity)) > reach):
                self.change('подход к выбранному мобу')
                goal=selected_approach or self.approach(target,reach,now)
                if self.attack_on_approach(now,target,goal,spell,ranged):return
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
            if not spell and ranged and own.values.get(4) in (4,5,13,14,16):
                self.change('боевой навык перезаряжается');self.next_action=now+.25;return
            if not spell and not self.world.default_skill:
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
            self.send_in_range_attack(now,target,spell,funding_attack)
            return
        if self.region and self.world.map!='garner' and own.values.get(LV,1)<=3:
            self.change('ожидание перехода в Аргент: старт на Forest Spirit');self.next_action=now+1;return
        self.change('поиск свободного места фарма')
        scout_goal=self.hunt_travel.scout_goal(now) if hasattr(self.hunt_travel,'scout_goal') else None
        if scout_goal and distance(self.position(now),scout_goal)>=300:
            if self.move_to(scout_goal,now):
                self.change('проверяет место появления мобов на острове')
                return
        if self.region:
            raw_goals=[pt for model in self.planned_models() if str(model) in self.region['farms']
                       for pt in self.region['farms'][str(model)]['points']]
        elif self.adventure:
            raw_goals=self.adventure.farm_goals()
        else:
            raw_goals=[self.nav.waypoints[i] for i in self.route]
        goals=[]
        recovery=self.farm_recovery(now)
        origin=self.position(now)
        if recovery:
            region=self.local_hunting_region()
            models=self.learning.admissible(region,own,now,recovery=True)
            nearby=self.reachable_camp_goals((p for model in models for p in region['farms'][str(model)]['points']),now)
            goals=[p for p in nearby if self.combat_allowed(p)]
            if self.search_recovery and self.search_goal in goals:
                goals=[self.search_goal]
            elif goals:
                closest=min(distance(origin,p) for p in goals)
                # Spread bots across nearby sites without sending one far away
                # merely because the nearest good patch is shared.
                goals=[p for p in goals if distance(origin,p)<=closest+3000]
        using_recovery=bool(goals)
        if self.paused_camp and not (self.supply_funding_goal or self.raising_travel_funds):
            map_name,point,expires=self.paused_camp
            if now>=expires:
                self.paused_camp=None
            elif map_name==self.world.map and point in map(tuple,raw_goals):
                resumed=self.reachable_camp_goals([point],now)
                if resumed:
                    goals=resumed
                    using_recovery=False
                self.paused_camp=None
        if not goals:
            goals=self.reachable_camp_goals(raw_goals,now)
        if not goals:
            if self.camp_scouting and self.region and not self.local_hunting_region()['farms']:
                if self.stuck_return.tick(now,self):
                    self.change(self.stuck_return.reason)
                    return
                if self.stuck_return.reason=='билет требует полные HP и SP':
                    self.sitting.tick(now,self,True)
                    self.change(self.stuck_return.reason)
                    return
            if self.camp_scouting:
                for model in self.planned_models():self.learning.avoid[model]=max(self.learning.avoid.get(model,0),now+15)
                self.learning.until=0
            self.change('нет свободного проверенного маршрута; повторный поиск')
            self.next_action=now+2
            return
        # Stable per-bot ordering, independent of the order of the JSON species.
        # Choose a nearby available farm instead of crossing the whole region
        # in a hash-random order. Reservation ties remain different per bot.
        goals.sort(key=lambda pt:(int(distance(origin,pt)//1500),
                    (pt[0]*73856093 ^ pt[1]*19349663 ^ int(self.approach_angle*100000)) & 0xffffffff))
        goal=(self.coordination.choose_zone(self.owner,self.world.map,goals,now,origin)
              if self.coordination else goals[self.waypoint%len(goals)])
        self.search_recovery=using_recovery
        if goal!=self.search_goal:
            self.search_goal,self.search_started=goal,now
            speed=max(100,self.world.own.values.get(44,480))
            self.search_deadline=now+max(45,min(900,distance(self.position(now),goal)/speed*1.8+20))
        arrived=distance(origin,goal)<300
        if arrived or now>=self.search_deadline:
            if getattr(self.nav,'incremental',False) is True:self.nav.cancel_pending(goal)
            self.goal_blacklist[goal]=now+(90 if self.camp_scouting else 20)
            if len(self.goal_blacklist)>128:self.goal_blacklist.pop(next(iter(self.goal_blacklist)))
            arrival_window=self.camp_arrival_until
            self.clear_zone()
            if arrived and self.region:self.camp_arrival_until=arrival_window or now+45
            self.waypoint+=1
            self.next_action=now+.5
        elif not self.move_to(goal,now):
            self.goal_blacklist[goal]=now+45
            self.clear_zone()
            self.next_action=now+1

    def hunting_coordinates(self):
        """Bounded source-backed sites, in native cm and the client's tile units."""
        region=self.local_hunting_region();sites=[]
        if region and self.world.own:
            origin=self.position(self.clock)
            for model in sorted(self.planned_models()):
                farm=region['farms'].get(str(model))
                if not farm or farm.get('territory',0)!=0:continue
                points=sorted(farm['points'],key=lambda p:distance(origin,p))[:3]
                record=self.mob_knowledge.get(model) if self.mob_knowledge else None
                sites.append({'model':model,'name':record.get('name') if record else None,'level':farm['level'],
                    'map':self.world.map,'points_cm':[list(p) for p in points],
                    'coordinates':[[round(p[0]/100,2),round(p[1]/100,2)] for p in points]})
        paused=self.paused_camp
        return {'sites':sites,'current_goal_cm':self.search_goal,
                'paused_camp':{'map':paused[0],'goal_cm':paused[1]} if paused and paused[2]>self.clock else None,'nearby_recovery':self.search_recovery,'camp_route_priority':self.camp_route_active(self.clock),
                'hunt_before_errands':self.hunt_before_errands(self.clock),
                'source_regions_not_live_monster_positions':True}

    def farm_reason(self):
        models=set(self.planned_models())
        if self.supply_funding_goal:return {'source':'essential_supply_funding','models':sorted(models),'goal_gold':self.supply_funding_goal,'patchouli_sale_to_npc':True}
        if self.raising_travel_funds and self.economy:return {'source':'class_travel_funding','models':sorted(models),'goal_gold':500,'patchouli_sale_to_npc':True}
        if self.economy and self.economy.phase(self.world,self.clock)=='income' and models==set(self.economy.last_models) and models:
            return {'source':'economic_patchouli_hunt','models':sorted(models),'player_unit_price':None,'npc_buyback':500,'bounded_phase':True}
        adaptive={'source':'adaptive_xp_hunt','models':sorted(models),
                  'character_level':self.world.own.values.get(LV,1),
                  'selected_levels':{str(m):self.region['farms'][str(m)]['level'] for m in models
                                     if self.region and str(m) in self.region['farms']},
                  'minimum_candidate_level':self.minimum_xp_mob_level(self.clock) if self.region else None}
        if self.starter_models():return {'source':'initial_trial','models':sorted(models)}
        if self.activity.hunting(self.clock) and not self.mandatory_work():return adaptive
        for name,feature in (('advanced_profession',self.career),('story_quest',self.story if self.wants_story() else None),('profession_quest',self.adventure)):
            if feature:
                required=feature.desired_models()
                if isinstance(required,(set,list,tuple)) and required and set(required)==models:
                    if feature is not self.adventure or feature.farm():return {'source':name,'models':sorted(models)}
        return adaptive

    def summary(self):
        return {'escape_plan':self.escape_plan.summary() if self.escape_plan else {},'economy':self.economy.summary(self.world,self.clock) if self.economy else {},'farm_reason':self.farm_reason(),'npc_knowledge':self.npc_knowledge.summary(self.world.map,self.world.own.position) if self.npc_knowledge else {},'combat_skills':self.combat_skills.summary() if self.combat_skills else {},'combat_safety':{'zone_revision':getattr(self.nav,'combat_zone_revision','unknown'),'protected_fights_stopped':self.protected_fights_stopped,'protected_target_checks':self.protected_target_checks,'last_protected_target':self.last_protected_target,'immune_fights_released':self.immune_fights_released,'own_position_allows_combat':self.combat_allowed(self.world.own.position) if self.world.own else None},'portal_shortcut':self.shortcut.summary() if self.shortcut else {},'offmesh_recovery':{'reason':self.offmesh_reason,'route':list(self.offmesh_route),'retry_in_seconds':max(0,self.offmesh_next-self.clock),'rejected_steps':len(self.offmesh_blocked)},'mob_knowledge':self.mob_knowledge.summary(self.world.map,self.world.own.position,self.world.own.values.get(LV,1)) if self.mob_knowledge else {},'tactic':self.tactic,'activity':self.activity.summary(),'stuck_return':self.stuck_return.summary(),'offmesh_recovery_requests':self.offmesh_requests,'schedule':self.tactic_schedule.summary() if self.tactic_schedule else None,'state': self.mode,'state_seconds':max(0,self.clock-self.mode_since),
                'background_planning_task':self.background_task,'quest_combat_priority':self.quest_combat_ready,'movement_obstacles':{'unexpected_stops':self.blocked_move_stops,'last_step':self.last_blocked_step},'retreat':{'active':self.resting,'goal_cm':self.retreat_goal,'replans_after_stop':self.retreat_replans},'inventory_blocker':self.inventory_blocker,'farm_plan':{'target':self.target_explanation(),'character_level':self.world.own.values.get(LV),'models':sorted(self.planned_models()),'replans':self.farm_plan_changes},
                'hunting_learning':self.learning.summary(),'hunting_coordinates':self.hunting_coordinates(),
                'action_wait':{'pending':bool(self.pending_action),'kind':self.pending_action[0][8] if self.pending_action else None,
                               'seconds':round(max(0,self.clock-self.pending_action[1]+.15),2) if self.pending_action else 0,
                               'last_sent_kind':self.last_sent_kind,'stop_kind':self.world.stop_packet_kind,'matching_stop':self.action_stopped()},
                'shared_target':self.shared_target,'target_hp':self.last_target_hp,'seconds_since_target_damage':max(0,self.clock-self.last_damage_at) if self.target else None,'target_id':self.target,'opportunity_model':self.opportunity_model,'opportunity_targets':self.opportunity_targets,'path_recoveries':self.recoveries,'end_action_requests':self.end_action_requests,'queued_actions':self.queued_actions,'action_packets_sent':dict(self.sent_action_counts),'flushed_actions':self.flushed_actions,'awaiting_action_stop':bool(self.pending_action),'town_detours_yielded':self.task_budget.yields,
                'combat_event_wakes':self.combat_wakes,'immediate_defence_attempts':self.immediate_defences,'combined_approach_attacks':self.approach_attacks,'active_fight_wait_ticks':self.active_fight_waits,'rejected_target_releases':self.rejected_target_releases,'search_destination':self.search_goal,'movement_endpoint':self.move_endpoint,'last_action_kind':self.last_sent_kind,
                'no_damage_retargets':self.no_damage_retargets,'reserved_targets_skipped':self.busy_targets, 'move_requests': self.moves, 'attack_requests': self.attacks,
                'revive_requests':self.revive_requests, 'revival':{'episodes':self.death_episodes,'confirmed_returns':self.confirmed_revivals,'last_death_ago':max(0,self.clock-self.last_death_at) if self.last_death_at is not None else None,'last_return_ago':max(0,self.clock-self.last_return_at) if self.last_return_at is not None else None,'attempts_in_batch':self.death_attempts,'dead_seconds':max(0,self.clock-self.dead_since) if self.dead_since is not None else 0,'retry_in_seconds':max(0,self.next_revive-self.clock) if self.dead_since is not None else 0}, 'movement_wait_ticks':self.move_waits, 'observed_target_deaths': self.kills, 'observed_deaths_with_own_hit':self.own_hit_deaths, 'world': self.world.summary()}


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
    policy.learning.record_progress(world.own, time.monotonic())
    if bot_index:policy.learning.load(Path(__file__).resolve().parents[1]/'data'/f'hunt-learning-{bot_index:03d}.json')
    policy.tactic=tactic
    from coordination import TacticSchedule
    policy.tactic_schedule=TacticSchedule(tactic,bot_name)
    policy.coordination=getattr(navigation,'coordination',None)
    policy.mob_knowledge=getattr(navigation,'mob_knowledge',None)
    observations=getattr(navigation,'hunt_observations',None)
    if observations and bot_index and policy.mob_knowledge:policy.learning.location_observer=navigation.record_hunting_observation
    region_for=getattr(navigation,'hunting_region',getattr(navigation,'get',lambda name:None))
    policy.mechanics=getattr(navigation,'mechanics',None)
    policy.region=region_for(world.map)
    if policy.region and policy.region['spawns']:policy.home=policy.nav.nearest(policy.region['spawns'][0],12) or policy.home
    policy.npc_knowledge=getattr(navigation,'npc_knowledge',None)
    policy.equipment=Equipment(world,catalog,client.wire.send,tell)
    from combat_skills import CombatSkills
    policy.combat_skills=CombatSkills(world,catalog,Path(__file__).resolve().parents[1]/'assets')
    from recovery import Recovery
    policy.recovery=Recovery(world)
    progression = Progression(world, client.wire.send)
    social = Social(world, client.wire.send, bot_name, chat_budget or ChatBudget(), bot_name,conversations=getattr(navigation,'conversations',None))
    if policy.npc_knowledge:social.npc_provider=lambda words:policy.npc_knowledge.answer(words,world.map,world.own.position)
    if policy.mechanics:social.mechanics_provider=lambda words:policy.mechanics.answer(words,world)
    from personality import Personality
    personality=Personality(bot_name);social.personality=personality
    social.scripted_dialogues=False
    role = None
    build_store=None
    if role_store:
        role = role_store.resolve(bot_name,world.own.model,world.own.values.get(4))
        progression.first_job = role['first_job']
        progression.target_job=role['target_job']
        from builds import BuildStore
        build_store=BuildStore(role_store.path.parent/'bot-builds.json')
        progression.build_id=build_store.resolve(bot_name,role['target_job'])
        world.own.build_id=progression.build_id
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
        from repairs import Repairs
        policy.repair=Repairs(world,life.npcs,catalog,client.wire.send)
        if hasattr(navigation,'rescue_resyncs'):
            from escape_plan import EscapePlan
            policy.escape_plan=EscapePlan(bot_name,navigation.rescue_resyncs)
        from pet_care import PetCare
        policy.petcare=PetCare(world,life,policy.mechanics,bot_name,role)
        policy.town.petcare=policy.petcare
        from economy import Economy
        policy.economy=Economy(bot_name,getattr(navigation,'assets',Path(__file__).resolve().parents[1]/'assets'))
        if getattr(getattr(navigation,'market_catalog',None),'curated_mode',False):policy.economy.trade_data=navigation.market_catalog.curated
        policy.economy.npc_income_enabled=bool(life.owner_shops and life.owner_shops.get('catalog_revision',0)>=55)
        policy.economy.patchouli_to_npc=True
        from treasure_hunt import TreasureHunt
        policy.treasure=TreasureHunt(world,policy.economy);policy.town.treasure=policy.treasure
        from life_professions import LifeProfessions
        policy.professions=LifeProfessions(world,life,bot_name,policy.economy)
        policy.town.professions=policy.professions
        from vendor import Vendor
        policy.vendor=Vendor(world,life,catalog,role,policy.rng,policy.home,getattr(navigation,"assets",Path(__file__).resolve().parents[1]/"assets"))
        policy.vendor.sell_patchouli=True;policy.vendor.junk[1000]={'name':'Чертёж Пачкули','npc_buyback':policy.vendor.patchouli_buyback}
        policy.career=Career(world,client.wire.send,role,life,navigation)
        policy.story=Story(world,client.wire.send,role,life,navigation)
        policy.story.owner=bot_name
        if bot_index:policy.story.load(Path(__file__).resolve().parents[1]/'data'/f'story-progress-{bot_index:03d}.json')
        policy.party=Party(world,client.wire.send,bot_name,bot_index,navigation.directory)
        from city_travel import CityTravel
        policy.travel=CityTravel(world,client.wire.send,bot_index,role,getattr(navigation,'portal_catalog',None))
        policy.petcare.home_city=policy.travel.home_city
        if getattr(navigation,'portal_catalog',None):
            from portal_shortcut import PortalShortcut
            policy.shortcut=PortalShortcut(world,client.wire.send,navigation.portal_catalog,getattr(navigation,'hunting_travel_data',None))
        if hasattr(navigation,'market_catalog'):
            from market import Market
            policy.market=Market(world,client.wire.send,bot_name,bot_index,navigation.market_catalog,catalog,life,navigation.market_directory)
            policy.market.focused_goods=True;policy.market.broad_goods=True;policy.market.policy_reference=policy
            policy.market.keep_stall_stock=True
            if life.npcs:
                from bank import Bank
                policy.bank=Bank(world,client.wire.send,life.npcs)

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
        if build_store:
            progression.build_id=build_store.resolve(bot_name,role['target_job'],allow_novice_change=world.own.values.get(4)==0)
            world.own.build_id=progression.build_id
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
    if policy.market:
        from direct_trade import DirectTrade
        from commerce import Commerce
        policy.direct_trade=DirectTrade(world,client.wire.send)
        policy.direct_trade.notify=lambda name,text,now:social.queue_line(name+', '+text,now)
        policy.commerce=Commerce(policy,policy.direct_trade,life,bot_name)
        social.commerce_provider=policy.commerce.answer
        social.trade_ad_provider=policy.commerce.due_advertisement
        social.trade_ad_sent=policy.commerce.advertised
        social.sale_offer=lambda:policy.commerce.advertisement(time.monotonic())
        if contacts:contacts.commerce_provider=policy.commerce.answer
    def context_line():
        if policy.crafting and policy.crafting.busy:return 'Я у кузнеца: проверяю цену, материалы и результат улучшения.'
        if policy.hunt_travel and policy.hunt_travel.busy:return 'Перехожу к другой точке прокачки; жду подтверждения прибытия.'
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
    policy.solo_progression=True
    if life and life.owner_shops and life.owner_shops.get('catalog_revision',0)>=56:
        from owner_services import OwnerServices,LOOT
        policy.owner_services=OwnerServices(world,role,life.owner_shops,client.wire.send)
        policy.adventure=policy.career=policy.story=None
        policy.optional_quests=False;policy.town.professions=policy.town.treasure=None
        policy.professions=policy.treasure=None
        policy.petcare.maintenance_only=life.owner_shops.get('catalog_revision',0)<60
        policy.petcare.progression_first=life.owner_shops.get('catalog_revision',0)>=60
        if policy.repair:
            policy.repair.preventive=life.owner_shops.get('catalog_revision',0)>=60
            policy.repair.budget_preflight=life.owner_shops.get('catalog_revision',0)>=60
        policy.town.next_break=float('inf')
        if policy.loot:
            policy.loot.collect_all=False;policy.loot.allowed_items=set(LOOT)
            policy.loot.ground_gems=set(life.owner_shops['owner_progression']['gem_ids'])
        if policy.economy:policy.economy.focused=True
        if policy.market:policy.market.focused=True
        if life.owner_shops.get('catalog_revision',0)>=57:
            policy.fast_progression=True
            policy.equipment.progression_first=True
            policy.learning.async_rewards=True
            policy.petcare.cost_based_possession=True
            if policy.vendor:policy.vendor.batch_farming=True
            if policy.loot:
                policy.loot.fast_mode=True;policy.loot.ground_gems.add(1000)
            if policy.economy:policy.economy.all_mobs_patchouli=True
        if life.owner_shops.get('catalog_revision',0)>=58:
            from crafting import Crafting
            from economy import role_for
            policy.economy.economic_role=role_for(bot_index)
            policy.economy.cycle=None
            policy.crafting=Crafting(world,catalog,policy.mechanics,life,policy.economy,client.wire.send,bot_name)
            if policy.economy.economic_role!='gem_seller' and policy.crafting.is_specialist:policy.economy.economic_role='crafter'
            policy.town.crafting=policy.crafting
            from xp_boosters import XPBoosters
            policy.xp_boosters=XPBoosters(world,life,policy.economy);policy.town.xp_boosters=policy.xp_boosters
            if getattr(navigation,'hunting_travel_data',None) and policy.mob_knowledge:
                from hunt_travel import HuntTravel
                policy.hunt_travel=HuntTravel(world,navigation,life,policy.economy,client.wire.send,bot_name)
                policy.town.hunt_travel=policy.hunt_travel
            if policy.market:
                policy.market.forging_economy=True;policy.market.gem_seller=policy.economy.economic_role=='gem_seller'
                policy.market.crafting=policy.crafting
        if life.owner_shops.get('catalog_revision',0)>=60:policy.camp_scouting=True
    if policy.bank:policy.bank.patchouli_audit=True
    if policy.market:policy.market.progression_first=True
    social.context_provider=context_line
    from public_chat import PublicChat,PublicBudget
    public_chat=PublicChat(world,client.wire.send,getattr(navigation,"public_chat_budget",None) or PublicBudget(),bot_name)
    if policy.party:
        # Earned XP takes priority; direct human invites and existing teams still work.
        policy.party.auto_groups_enabled=False
    def public_context(channel):
        if channel=='trade':
            if policy.commerce:return policy.commerce.advertisement(time.monotonic())
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
    chat_adapter=None
    if getattr(navigation,'dialogue_data',None) and getattr(navigation,'chat_coordinator',None):
        from chat_adapter import ChatAdapter
        chat_adapter=ChatAdapter(world,policy,social,public_chat,contacts,navigation.dialogue_data,navigation.chat_coordinator,client.wire.send,bot_name)
        social.chat_adapter=chat_adapter;social.scripted_dialogues=False
        if policy.direct_trade:
            policy.direct_trade.notify=lambda name,text,now:chat_adapter.enqueue(chat_adapter.quote_scopes.get(name.casefold(),'private'),name,text,now)

    def snapshot(now):
        if observations:
            policy.region=region_for(world.map)
            if bot_index:observations.save(now)
        policy.learning.save(now)
        if policy.market and policy.market.catalog.prices:policy.market.catalog.prices.save()
        report.result['decision_loop']=dict(think_stats)
        if network_pump:report.result['network_pump']=network_pump.summary()
        receive_at=getattr(client.wire,'last_receive_at',None)
        report.result['connection_health']={'seconds_since_received_bytes':round(max(0,now-receive_at),2) if type(receive_at) in (int,float) else None,
                                          'seconds_since_sent_frame':round(max(0,now-client.wire.last_send),2),
                                          'gate_ping_answers':report.result.get('gate_ping_answers',0),
                                          'game_ping_answers':report.result.get('game_ping_answers',0)}
        report.result['route_planning']=policy.nav.planning_stats()
        if policy.group_hunt:report.result['hunt_party']=policy.group_hunt.summary()
        report.result['sitting']=policy.sitting.summary()
        report.result['hunt']=policy.summary()
        report.result['progress_monitor']=policy.progress_monitor.summary()
        if policy.owner_services:report.result['owner_services']=policy.owner_services.summary()
        if policy.crafting:report.result['crafting']=policy.crafting.summary()
        if policy.xp_boosters:report.result['xp_boosters']=policy.xp_boosters.summary()
        if policy.hunt_travel:report.result['hunting_travel']=policy.hunt_travel.summary()
        if policy.treasure:report.result['treasure_hunt']=policy.treasure.summary()
        if policy.mechanics:report.result['mechanics']={**policy.mechanics.summary(),**policy.mechanics.owned_summary(world)}
        if policy.loot:report.result['loot']=policy.loot.summary()
        if contacts:report.result['contacts']=contacts.summary()
        if cooperation:report.result['cooperation']=cooperation.summary()
        report.result['progression']=progression.summary()
        report.result['equipment']=policy.equipment.summary()
        report.result['chat']=social.summary()
        if chat_adapter:report.result['dialogue']=chat_adapter.summary()
        if getattr(navigation,'dialogue_error',None):report.result['dialogue_start_error']=navigation.dialogue_error
        report.result['public_chat']=public_chat.summary()
        if social.conversations:report.result['chat']['shared_conversations']=social.conversations.summary()
        report.result['recovery']=policy.recovery.summary()
        for key in ('chests','town','career','story','party','market','travel','helper','vendor','bank','direct_trade','petcare','professions','repair'):
            feature=getattr(policy,key)
            if feature:report.result[key]=feature.summary()
        if policy.skills:report.result['skills']=policy.skills.summary()
        if policy.adventure:report.result['adventure']=policy.adventure.summary()
        report.write(Path(__file__).resolve().parents[1]/f'bot-report-{bot_index:02d}.json')
        if fleet:
            values=world.own.values
            xp=policy.learning.summary()
            fleet.update(bot_index,connected=True,map=world.map,position=list(world.position(now)),level=values.get(0),job=values.get(4),gold=values.get(8),
                         body=world.own.model,state=policy.mode,tactic=policy.tactic,phase=policy.tactic_schedule.effective_phase,hp=values.get(HP),max_hp=values.get(MAX_HP),
                         moves=policy.moves,attacks=policy.attacks,equips=policy.equipment.confirmed,
                         experience=values.get(15),start_experience=progression.start_xp,
                         xp_per_minute=xp['session_xp_per_minute'],session_xp_net=xp['session_xp_net'],seconds_without_xp=xp['seconds_without_xp'],
                         start_level=progression.start_level,hunt_style=policy.learning.profile[0],farm_models=sorted(policy.planned_models()),
                         quests=policy.adventure.delivered if policy.adventure else 0,
                         target_job=role['target_job'] if role else 0)

    from xp_diagnostics import XPDiagnostics
    xp_diagnostics=XPDiagnostics()
    def observe(command, payload):
        now=time.monotonic()
        if xp_diagnostics.observe(command,payload):
            report.result['xp_server']=xp_diagnostics.summary();return
        if policy.treasure:policy.treasure.observe(command,payload)
        if command==811 or command in range(812,820):
            if policy.direct_trade:policy.direct_trade.observe(command,payload,now,policy)
            return
        if command in (5011,5012,5403):
            if policy.group_hunt:policy.group_hunt.observe(command,payload,now)
            if chat_adapter and command==5403 and chat_adapter.observe(command,payload,now):return
            if contacts:contacts.hear(command,payload,now)
            return
        if command in (5401,5402):
            if policy.group_hunt:policy.group_hunt.observe(command,payload,now)
            if chat_adapter:chat_adapter.observe(command,payload,now)
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
                except ProtocolError:
                    report.result['party_decode']='unsupported';policy.party=None;policy.group_hunt=None
                    public_chat.recruitment_provider=None
            return
        if policy.repair and policy.repair.context and command in (517,802,544,546):
            try:
                if policy.repair.observe(command,payload,now):return
            except ProtocolError:
                policy.repair.finish(now,'неподдерживаемый ответ ремонта; нужен свежий отчёт',True)
                report.result['repair_decode']='unsupported';return
        if policy.owner_services:
            try:
                if policy.owner_services.observe(command,payload,now):return
            except ProtocolError:
                policy.owner_services.finish(now)
                report.result['owner_services_decode']='unsupported'
        if policy.crafting:
            try:
                if policy.crafting.observe(command,payload,now):return
            except ProtocolError:
                policy.crafting.finish(now,'Неизвестный формат ответа ковки',True)
                report.result['crafting_decode']='unsupported'
        if policy.hunt_travel:
            try:
                if policy.hunt_travel.observe(command,payload,now):return
            except ProtocolError:
                policy.hunt_travel.abort(now,'Неизвестный ответ портальщицы')
                report.result['hunting_travel_decode']='unsupported'
        if policy.vendor and policy.vendor.context and command in (801,802,803,805,806,807,808):
            try:
                if policy.vendor.observe(command,payload,now,client.wire.send):return
            except ProtocolError:
                policy.vendor.finish_sale(now);report.result['vendor_decode']='unsupported'
        if policy.bank and policy.bank.context and command==802:
            try:
                if policy.bank.observe(command,payload,now):return
            except ProtocolError:
                policy.bank.end(now,policy);report.result['bank_decode']='unsupported'
        if policy.shortcut and command==802 and policy.shortcut.context:
            if policy.shortcut.observe(command,payload,now):return
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
            if policy.repair:policy.repair.finish(now,'карта изменилась; перепроверяет необходимость ремонта')
            policy.stuck_return.on_map(world.map)
            if policy.bank:policy.bank.end(now)
            if policy.direct_trade:policy.direct_trade.reset()
            world.own.build_id=progression.build_id
            policy.pending_action=None;policy.action_open=False
            policy.sitting.reset()
            policy.retreat_goal=None
            policy.assist_target=None
            if policy.helper:policy.helper.source=None
            if policy.travel:policy.travel.on_map(now)
            if policy.shortcut and policy.shortcut.busy:policy.shortcut.on_map(now)
            policy.sent_move_points=();policy.move_map=None;policy.cancelled_move_packet=None
            policy.motion_anchor=None;policy.motion_progress_at=None;policy.stuck=0
            if policy.vendor:policy.vendor.home=world.own.position;policy.vendor.finish_sale(now)
            if policy.market:
                policy.market.finish(now);policy.market.context=None;policy.market.pending=None
            policy.nav=navigation.nav(world.map) if hasattr(navigation,'nav') else nav
            if getattr(policy.nav,'incremental',False) is True:policy.nav.cancel_pending()
            policy.region=region_for(world.map)
            policy.home=world.own.position
            if policy.region and policy.region['spawns']:policy.home=policy.nav.nearest(policy.region['spawns'][0],12) or policy.home
            if was_dead:
                policy.confirmed_revivals+=1;policy.last_return_at=now
                policy.learning.events.append('revived');policy.learning.events=policy.learning.events[-8:]
            if policy.town:policy.town.end_rest(now);policy.town.home=policy.home;policy.town.on_map(now,was_dead)
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
            if adventure_mode and not policy.owner_services:
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
    network_pump=None
    try:
        while client.pending_world:
            observe(*client.pending_world.popleft())
        from network_pump import start_pump
        network_pump=start_pump(client)
        report.stage('hunting')
        tell(f'Данные мира: {world.map}, координаты {world.own.x//100},{world.own.y//100}, '
             f'здоровье {world.own.values[HP]}/{world.own.values[MAX_HP]}.')
        next_snapshot=0
        next_think=0
        combat_seen=(world.combat_revision,world.stop_revision)
        think_stats={"count":0,"max_seconds":0,"total_seconds":0}
        from connection_watchdog import ConnectionWatchdog
        connection_watchdog=ConnectionWatchdog()
        seen_equips=seen_skills=seen_quests=0
        seen_party=seen_chests=seen_shopping=0
        deadline = float('inf') if seconds==0 else time.monotonic()+seconds
        while time.monotonic() < deadline and not stop.is_set():
            try:
                source=network_pump or client.wire
                poll_deadline=min(deadline,time.monotonic()+.15)
                if next_think:poll_deadline=min(poll_deadline,next_think)
                release=policy.acknowledged_attack_release()
                if release is not None and release>time.monotonic():
                    poll_deadline=min(poll_deadline,release)
                command,payload=source.receive(poll_deadline)
                client.service(command, payload)
                # Drain a bounded burst before expensive decisions; preserve ordering.
                drain_started=time.thread_time()
                catchup=bool(network_pump and network_pump.backlogged())
                for _ in range(1023 if catchup else 63):
                    if time.thread_time()-drain_started>=(.012 if catchup else .004):break
                    if network_pump is None or network_pump.queue.empty():break
                    command,payload=network_pump.receive(time.monotonic()+.001);client.service(command,payload)
            except TimeoutError:
                pass
            now=time.monotonic()
            if (not network_pump or network_pump.queue.empty()) and connection_watchdog.expired(now,client.wire,sum(policy.sent_action_counts.values())):
                report.result['connection_watchdog']=connection_watchdog.summary()
                raise ConnectionError(connection_watchdog.reason)
            if network_pump and network_pump.backlogged(now):
                network_pump.catchup_skips+=1
                continue # Apply authoritative packets before deciding from stale state.
            combat_wake=False
            signals=(world.combat_revision,world.stop_revision)
            release=policy.acknowledged_attack_release()
            if signals!=combat_seen or release is not None and now>=release:
                combat_seen=signals
                combat_wake=policy.wake_for_combat(now)
            if combat_wake or now>=next_think:
                think_started=now
                next_think=now+(.15+(bot_index%5)*.015 if getattr(policy,'fast_progression',False) and not policy.transaction_busy() else .25 if network_pump is None or policy.pending_action or policy.target else 1.0 if policy.transaction_busy() else .65+(bot_index%5)*.03)
                think_cpu_started=time.thread_time()
                if hasattr(navigation,'directory'):
                    navigation.directory.update(bot_name,bot_index,world.map,world.position(),world.own.values.get(0,1),time.monotonic())
                if policy.party:
                    if policy.group_hunt:policy.group_hunt.tick(now)
                    dialogue_busy=any(getattr(f,'context',None) for f in (policy.adventure,policy.town,policy.career,policy.story,policy.travel,policy.shortcut,policy.repair) if f)
                    policy.party.tick(time.monotonic(),bot_index,safe=not policy.target and not dialogue_busy and not policy.resting and not policy.transaction_busy())
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
                progression.tick(now, safe and not policy.transaction_busy())
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
                    or any(getattr(f,'context',None) for f in (policy.adventure,policy.career,policy.story,policy.town,policy.vendor,policy.travel,policy.shortcut,policy.repair) if f))
                social.tick(now, policy.resting, alive and now-policy.started >= 3)
                if chat_adapter:chat_adapter.tick(now)
                public_chat.tick(now,alive and now-policy.started>=3,policy.market)
                think_stats['cpu_seconds']=think_stats.get('cpu_seconds',0)+time.thread_time()-think_cpu_started
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
        if network_pump:
            network_pump.close();report.result['network_pump']=network_pump.summary()
        policy.learning.save(time.monotonic(),force=True)
        if policy.market and policy.market.catalog.prices:policy.market.catalog.prices.save(force=True)
        report.result['hunt'] = policy.summary()
        if policy.mechanics:report.result['mechanics']={**policy.mechanics.summary(),**policy.mechanics.owned_summary(world)}
        report.result['sitting']=policy.sitting.summary()
        report.result['route_planning']=policy.nav.planning_stats()
        if policy.loot:report.result['loot']=policy.loot.summary()
        if contacts:report.result['contacts']=contacts.summary()
        if cooperation:
            report.result['cooperation']=cooperation.summary()
            navigation.help_directory.remove(bot_name)
        report.result['progression'] = progression.summary()
        report.result['chat'] = social.summary()
        if chat_adapter:
            report.result['dialogue']=chat_adapter.summary();navigation.chat_coordinator.remove(bot_name)
        report.result['equipment']=policy.equipment.summary()
        report.result['recovery']=policy.recovery.summary()
        for key in ('chests','town','career','story','party','market','travel','helper','vendor','bank','direct_trade','petcare','professions','repair'):
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
