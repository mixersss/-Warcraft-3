"""Bounded class-skill prerequisite plans; owned/native skill levels are authoritative."""
GOALS={
 9:((81,1),(84,1),(81,4),(84,5),(109,1),(65,3),(70,5),(86,1),(109,5),(81,10)),
 8:((81,1),(63,1),(222,4),(127,5),(67,3),(68,5),(64,3),(82,1),(83,1),(82,10)),
 12:((90,1),(74,5),(93,2),(90,4),(224,1),(75,2),(74,10),(78,5),(96,1),(90,10)),
 13:((99,1),(97,1),(99,3),(97,3),(225,3),(98,1),(99,5),(98,4),(124,1),(79,8),(80,2),(117,1),(99,10),(97,10)),
 14:((99,1),(97,1),(99,3),(97,3),(225,1),(79,8),(80,2),(116,3),(119,4),(105,3),(104,1),(120,1),(99,10)),
 16:((214,1),(210,2),(211,1),(212,5),(216,1),(214,3),(213,1),(216,5),(214,8),(220,1),(216,10)),
}

class SkillPlan:
    def __init__(self,world,role,catalog):
        self.world,self.role,self.catalog=world,role,catalog
        self.by_skill={}
        for book,record in catalog.books.items():self.by_skill.setdefault(record['skill'],[]).append((book,record))
        self.last_steps=[];self.blocker=''

    def goals(self):
        target=self.role.get('target_job');goals=GOALS.get(target,())
        if target==12 and getattr(self.world.own,'build_id',None)=='sharpshooter_speed':
            goals=((90,1),(75,4),(74,5),(90,4),(224,1),(74,10),(78,5),(90,10))
        return goals

    def next_steps(self,now=0,paused=None):
        w=self.world;job=str(w.own.values.get(4));paused=paused or {};steps=[];seen=set()
        def need(skill,target,stack):
            if skill in stack:return None
            records=[(book,record) for book,record in self.by_skill.get(skill,()) if job in record['jobs']]
            if not records:return None # Future profession; do not ask the current server job to learn it.
            book,record=min(records,key=lambda r:r[0]);target=min(target,record['jobs'][job],10)
            current=w.skills.get(skill,{}).get('level',0)
            if current>=target:return None
            for prerequisite,level in record['prerequisites']:
                if w.skills.get(prerequisite,{}).get('level',0)<level:
                    return need(prerequisite,level,stack|{skill})
            slot=next((s for s,i in w.bag.items() if i.identity==book and i.valid),None)
            reason=('нужен уровень '+str(record['level']) if w.own.values.get(0,0)<record['level'] else
                    'повтор после отказа сервера' if paused.get(skill,0)>now else
                    'нужны очки навыков' if w.own.values.get(7,0)<record['cost'] else
                    'нужна книга' if current==0 and slot is None else '')
            return {'skill':skill,'target_level':current+1,'goal_level':target,'book':book,
                    'bag_slot':slot,'cost':record['cost'],'action':'learn' if not current else 'upgrade',
                    'blocker':reason,'name':record['name']}
        for goal,level in self.goals():
            step=need(goal,level,set())
            if step and step['skill'] not in seen:steps.append(dict(step,goal_skill=goal));seen.add(step['skill'])
        self.last_steps=steps;self.blocker=steps[0]['blocker'] if steps else ''
        return steps

    def missing_books(self):
        return [s['book'] for s in self.next_steps() if s['blocker']=='нужна книга']

    def summary(self):
        return {'next_steps':self.last_steps[:6],'blocker':self.blocker,
                'goals':[{'skill':s,'level':lv} for s,lv in self.goals()]}
