export const WORLD={w:2400,h:1680,cell:40};
export const BUILDINGS={
 hq:{name:'Резиденция',glyph:'木',hp:3400,cost:[0,0],time:0,size:83},
 barracks:{name:'Казармы',glyph:'⚔',hp:1200,cost:[180,120],time:15,size:66},
 house:{name:'Дом',glyph:'⌂',hp:650,cost:[80,90],time:10,size:49},
 tower:{name:'Сторожевая башня',glyph:'♜',hp:1100,cost:[150,100],time:18,size:43},
 dojo:{name:'Додзё',glyph:'忍',hp:950,cost:[200,140],time:20,size:62}
};
export const UNITS={
 worker:{name:'Рабочий',hp:150,damage:5,range:30,speed:91,rate:1.4,cost:[55,0],time:6},
 shinobi:{name:'Шиноби',hp:310,damage:21,range:39,speed:106,rate:1.05,cost:[80,20],time:7},
 kunai:{name:'Метатель кунаев',hp:210,damage:17,range:180,speed:101,rate:1.15,cost:[105,35],time:9},
 medic:{name:'Медик',hp:220,damage:8,range:145,speed:97,rate:1.4,cost:[110,55],time:10},
 hero:{name:'Герой',hp:900,damage:37,range:43,speed:126,rate:.85,cost:[0,0],time:0}
};
export const HEROES={naruto:{name:'Наруто Узумаки',short:'Наруто',color:'#ed9c43',hair:'#f7d05f',glyph:'鳴',skills:[['Спираль чакры','◉',9],['Теневые клоны','影',22],['Сила воли','✧',18],['Шторм чакры','渦',38]]},sasuke:{name:'Саске Учиха',short:'Саске',color:'#788ac9',hair:'#242b42',glyph:'佐',skills:[['Чидори','ϟ',10],['Огненный шар','炎',14],['Шаг тени','彡',16],['Грозовой разряд','雷',38]]},sakura:{name:'Сакура Харуно',short:'Сакура',color:'#d0728b',hair:'#e9a5b8',glyph:'桜',skills:[['Удар земли','✦',10],['Исцеление','✚',14],['Защитная печать','◇',19],['Цветение жизни','桜',36]]},gaara:{name:'Гаара',short:'Гаара',color:'#bb7757',hair:'#ad523e',glyph:'砂',skills:[['Песчаный удар','◉',10],['Песчаная буря','彡',18],['Песчаный щит','◇',22],['Песчаное цунами','砂',40]]}};
const dist=(a,b)=>Math.hypot(a.x-b.x,a.y-b.y),clamp=(v,a,b)=>Math.max(a,Math.min(b,v));
export class Game{
 constructor(hero='naruto',seed=513){this.entities=[];this.nextId=1;this.time=0;this.seed=seed;this.heroChoice=hero;this.effects=[];this.messages=[];this.winner=null;this.started=false;this.paused=false;this.botAt=0;this.revives=[];this.teams=[{gold:500,wood:300,attack:0,armor:0,spent:0},{gold:500,wood:300,attack:0,armor:0,spent:0}];this.nodes=[];this.init();}
 random(){this.seed=(Math.imul(1664525,this.seed)+1013904223)>>>0;return this.seed/4294967296;}
 init(){
  for(const team of [0,1]){const x=team?2070:330,y=team?480:1170;
   this.addBuilding('hq',team,x,y,true);this.addBuilding('house',team,x+(team?100:-95),y+145,true);
   this.addUnit('hero',team,x+(team?-120:145),y-30,{hero:team?'gaara':this.heroChoice});
   for(let i=0;i<3;i++)this.addUnit('worker',team,x+(team?-80:80)+i*24,y+70);
   for(let i=0;i<2;i++)this.addUnit('shinobi',team,x+(team?-145:150)+i*25,y-110);
   this.nodes.push({id:'g'+team,type:'gold',x:x+(team?-30:0),y:y-250,remaining:18000});
   this.nodes.push({id:'w'+team,type:'wood',x:x+(team?-220:220),y:y+210,remaining:22000});
  }
  this.nodes.push({id:'gc',type:'gold',x:970,y:370,remaining:16000},{id:'wc',type:'wood',x:1460,y:1310,remaining:18000});
 }
 addBuilding(type,team,x,y,complete=false){const d=BUILDINGS[type];const e={id:this.nextId++,kind:'building',type,team,x,y,hp:complete?d.hp:d.hp*.15,maxHP:d.hp,progress:complete?1:0,queue:[],cool:0,alive:true};this.entities.push(e);return e;}
 addUnit(type,team,x,y,extra={}){const d=UNITS[type];const e={id:this.nextId++,kind:'unit',type,team,x,y,hp:d.hp,maxHP:d.hp,alive:true,cool:0,order:null,target:null,path:null,repath:0,carry:0,gather:0,attackAt:-20,level:1,xp:0,cooldowns:[0,0,0,0],...extra};this.entities.push(e);return e;}
 get(id){return this.entities.find(e=>e.id===id&&e.alive);}
 units(team){return this.entities.filter(e=>e.alive&&e.kind==='unit'&&e.team===team);}
 buildings(team,type){return this.entities.filter(e=>e.alive&&e.kind==='building'&&e.team===team&&(!type||e.type===type));}
 population(team){return this.units(team).filter(e=>!e.clone).length+this.buildings(team).reduce((n,b)=>n+b.queue.length,0);}
 limit(team){return Math.min(80,20+this.buildings(team,'house').filter(e=>e.progress===1).length*10);}
 canPay(team,cost){return this.teams[team].gold>=cost[0]&&this.teams[team].wood>=cost[1];}
 pay(team,cost){if(!this.canPay(team,cost))return false;this.teams[team].gold-=cost[0];this.teams[team].wood-=cost[1];this.teams[team].spent+=cost[0]+cost[1];return true;}
 notify(text){this.messages.push(text);}
 hire(building,type){const b=this.get(building),d=UNITS[type];if(!b||b.progress!==1||!d||!((b.type==='hq'&&type==='worker')||(b.type==='barracks'&&['shinobi','kunai','medic'].includes(type))))return false;
  if(b.queue.length>=5){this.notify('Очередь заполнена: максимум 5 бойцов.');return false;}
  if(this.population(b.team)>=this.limit(b.team)){if(b.team===0)this.notify('Нужен дом: достигнут предел отряда.');return false;}
  if(!this.pay(b.team,d.cost)){if(b.team===0)this.notify('Не хватает рё или древесины.');return false;}
  b.queue.push({type,left:d.time,total:d.time});return true;
 }
 validPlacement(type,x,y){const d=BUILDINGS[type];if(!d||type==='hq'||x<100||y<100||x>WORLD.w-100||y>WORLD.h-100)return false;
  if(Math.abs(x-1200)<140)return false;
  if(this.entities.some(e=>e.alive&&e.kind==='building'&&Math.hypot(x-e.x,y-e.y)<d.size+BUILDINGS[e.type].size+30))return false;
  if(this.nodes.some(n=>Math.hypot(x-n.x,y-n.y)<d.size+60))return false;
  return true;
 }
 build(worker,type,x,y){const u=this.get(worker),d=BUILDINGS[type];if(!u||u.type!=='worker'||!this.validPlacement(type,x,y))return false;
  if(!this.pay(u.team,d.cost)){if(u.team===0)this.notify('Не хватает ресурсов для строительства.');return false;}
  const b=this.addBuilding(type,u.team,x,y);u.order={type:'build',id:b.id};u.path=null;return b;
 }
 upgrade(team,stat){const n=this.teams[team][stat];if(!['attack','armor'].includes(stat)||n>=5||!this.buildings(team,'dojo').some(b=>b.progress===1))return false;
  if(!this.pay(team,[140+n*95,75+n*55])){if(team===0)this.notify('Не хватает ресурсов для улучшения.');return false;}
  this.teams[team][stat]++;if(team===0)this.notify((stat==='attack'?'Атака':'Броня')+' отряда: уровень '+(n+1));return true;
 }
 command(ids,x,y,target=null,attackMove=false){let i=0;const list=ids.map(id=>this.get(id)).filter(e=>e?.kind==='unit');
  for(const e of list){if(target?.kind==='unit'||target?.kind==='building'){if(target.team!==e.team){e.order={type:'attack',id:target.id};}else{e.order={type:'move',x:target.x-55+this.random()*110,y:target.y+60};}}
   else if(target?.remaining!==undefined&&e.type==='worker')e.order={type:'gather',node:target.id};
   else{const cols=Math.ceil(Math.sqrt(list.length)),ox=list.length>1?(i%cols-(cols-1)/2)*28:0,oy=list.length>1?(Math.floor(i/cols)-(cols-1)/2)*28:0;e.order={type:attackMove?'attackmove':'move',x:clamp(x+ox,35,WORLD.w-35),y:clamp(y+oy,35,WORLD.h-35)};}
   e.target=null;e.path=null;e.repath=0;i++;
  }
 }
 blocked(cx,cy){if(cx<0||cy<0||cx>=60||cy>=42)return true;return (cx===29||cx===30)&&!((cy>=8&&cy<=12)||(cy>=19&&cy<=23)||(cy>=30&&cy<=34));}
 path(sx,sy,tx,ty){const w=60,h=42,start=clamp(Math.floor(sy/40),0,h-1)*w+clamp(Math.floor(sx/40),0,w-1),end=clamp(Math.floor(ty/40),0,h-1)*w+clamp(Math.floor(tx/40),0,w-1);if(this.blocked(end%w,Math.floor(end/w)))return [];
  const q=[start],came=new Int32Array(w*h).fill(-1);came[start]=start;let at=0;
  while(at<q.length&&came[end]<0){const n=q[at++],x=n%w,y=Math.floor(n/w);for(const [dx,dy]of [[1,0],[-1,0],[0,1],[0,-1]]){const a=x+dx,b=y+dy,k=b*w+a;if(!this.blocked(a,b)&&came[k]<0){came[k]=n;q.push(k);}}}
  if(came[end]<0)return [];const out=[{x:tx,y:ty}];let n=end;while(n!==start){out.push({x:(n%w)*40+20,y:Math.floor(n/w)*40+20});n=came[n];}out.reverse();return out;
 }
 move(e,x,y,dt,reach=10){if(Math.hypot(e.x-x,e.y-y)<=reach)return true;
  const target=e.pathTarget;if(!e.path||!target||Math.hypot(target.x-x,target.y-y)>70){e.path=this.path(e.x,e.y,x,y);e.pathTarget={x,y};}
  while(e.path.length&&Math.hypot(e.x-e.path[0].x,e.y-e.path[0].y)<11)e.path.shift();if(!e.path.length)return false;
  const p=e.path[0],dx=p.x-e.x,dy=p.y-e.y,d=Math.hypot(dx,dy),speed=UNITS[e.type].speed*(e.hasteUntil>this.time?1.55:1),step=Math.min(speed*dt,d);
  e.x+=dx/d*step;e.y+=dy/d*step;e.facing=dx>=0?1:-1;e.walking=true;return false;
 }
 damage(source,target,amount){if(!target?.alive)return;const armor=target.kind==='unit'?this.teams[target.team].armor*1.5:2;amount=Math.max(1,amount-armor);if(target.shieldUntil>this.time)amount*=.55;target.hp-=amount;target.attackAt=this.time;target.hitUntil=this.time+.12;
  if(target.hp<=0){target.hp=0;target.alive=false;this.effects.push({type:'death',x:target.x,y:target.y,life:.65,total:.65,team:target.team});
   if(source?.type==='hero'&&!target.clone){source.xp+=target.kind==='building'?40:16;const need=55+source.level*25;if(source.xp>=need){source.xp-=need;source.level++;source.maxHP+=65;source.hp=Math.min(source.maxHP,source.hp+150);this.effects.push({type:'level',x:source.x,y:source.y,life:1.2,total:1.2});}}
   if(source&&!target.clone)this.teams[source.team].gold+=target.kind==='building'?40:target.type==='worker'?6:12;
   if(target.type==='hero'&&!target.clone){this.revives.push({team:target.team,hero:target.hero,level:target.level,xp:target.xp,maxHP:target.maxHP,at:this.time+25});if(target.team===0)this.notify('Герой вернётся к резиденции через 25 секунд.');}
   if(target.type==='hq')this.winner=1-target.team;
  }
 }
 nearestEnemy(e,radius,unitsOnly=false){let best=null,d=radius;for(const n of this.entities){if(!n.alive||n.team===e.team||(unitsOnly&&n.kind!=='unit'))continue;const v=dist(e,n)-(n.kind==='building'?BUILDINGS[n.type].size*.5:0);if(v<d){best=n;d=v;}}return best;}
 attack(e,target,dt){const range=e.kind==='building'?240:UNITS[e.type].range+(target.kind==='building'?BUILDINGS[target.type].size*.7:0);
  if(dist(e,target)>range){if(e.kind==='unit')this.move(e,target.x,target.y,dt,range);return;}
  e.walking=false;e.facing=target.x>=e.x?1:-1;
  if(e.cool<=0){const ranged=e.kind==='building'||UNITS[e.type].range>100;const amount=(e.kind==='building'?34:UNITS[e.type].damage+this.teams[e.team].attack*4+(e.type==='hero'?(e.level-1)*3:0));
   e.cool=e.kind==='building'?.95:UNITS[e.type].rate;e.swingUntil=this.time+.22;
   if(ranged){this.effects.push({type:'projectile',x:e.x,y:e.y-15,tx:target.x,ty:target.y-10,life:.25,total:.25,team:e.team});}
   this.damage(e,target,amount);
  }
 }
 cast(hero,index){const e=this.get(hero);if(!e||e.type!=='hero'||index<0||index>3||e.cooldowns[index]>0)return false;const kit=HEROES[e.hero];e.cooldowns[index]=kit.skills[index][2];e.castUntil=this.time+.6;
  const allies=this.units(e.team).filter(u=>dist(e,u)<230),enemies=this.entities.filter(u=>u.alive&&u.team!==e.team&&dist(e,u)<(index===3?330:220));
  const heal=(amount)=>{for(const a of allies){a.hp=Math.min(a.maxHP,a.hp+amount);this.effects.push({type:'heal',x:a.x,y:a.y,life:.9,total:.9});}};
  const blast=(damage,radius,color)=>{this.effects.push({type:'blast',x:e.x,y:e.y,life:.7,total:.7,radius,color});for(const a of enemies)if(dist(e,a)<radius)this.damage(e,a,damage+e.level*7);};
  if(e.hero==='naruto'){
   if(index===0)blast(110,180,'#7bd4ec');
   if(index===1)for(let k=0;k<3;k++){const clone=this.addUnit('hero',e.team,e.x+Math.cos(k*2.1)*36,e.y+Math.sin(k*2.1)*36,{hero:'naruto',clone:true,expires:this.time+20,maxHP:120,hp:120});clone.order={type:'attackmove',x:e.x+(e.team?-250:250),y:e.y};}
   if(index===2){heal(155);e.hasteUntil=this.time+6;}
   if(index===3)blast(250,330,'#86c6e9');
  }else if(e.hero==='sasuke'){
   if(index===0)blast(145,170,'#a4b9ff');
   if(index===1)blast(120,220,'#ffae67');
   if(index===2){e.shieldUntil=this.time+5;e.hasteUntil=this.time+6;}
   if(index===3)blast(300,330,'#bec5ff');
  }else if(e.hero==='sakura'){
   if(index===0)blast(125,190,'#f4bfa8');
   if(index===1)heal(200);
   if(index===2)for(const a of allies)a.shieldUntil=this.time+8;
   if(index===3){heal(420);blast(130,330,'#eeb6cc');}
  }else{
   if(index===0)blast(115,190,'#e5c58c');
   if(index===1)blast(130,220,'#c5ad7d');
   if(index===2)e.shieldUntil=this.time+8;
   if(index===3)blast(255,330,'#eacb8d');
  }
  return true;
 }
 workerTick(e,dt){const o=e.order;if(o?.type==='build'){const b=this.get(o.id);if(!b||b.progress===1){e.order=null;return;}const reach=BUILDINGS[b.type].size+28;if(this.move(e,b.x,b.y,dt,reach)){b.progress=Math.min(1,b.progress+dt/BUILDINGS[b.type].time);b.hp=Math.max(b.hp,b.maxHP*b.progress);e.walking=false;if(b.progress===1&&e.team===0)this.notify(BUILDINGS[b.type].name+': строительство завершено.');}return true;}
  if(o?.type!=='gather')return false;const n=this.nodes.find(n=>n.id===o.node);if(!n||n.remaining<=0){e.order=null;return true;}
  const base=this.buildings(e.team,'hq')[0];if(!base)return true;
  if(e.carry>=12){if(this.move(e,base.x,base.y,dt,110)){this.teams[e.team][n.type]+=e.carry;e.carry=0;e.gather=0;e.path=null;}return true;}
  if(this.move(e,n.x,n.y,dt,48)){e.walking=false;e.gather+=dt;if(e.gather>=1){e.gather=0;const v=Math.min(4,n.remaining);n.remaining-=v;e.carry+=v;e.swingUntil=this.time+.2;}}return true;
 }
 bot(){const team=1,hq=this.buildings(team,'hq')[0];if(!hq)return;const workers=this.units(team).filter(u=>u.type==='worker');
  for(const w of workers)if(!w.order){const type=workers.indexOf(w)%3===0?'wood':'gold';w.order={type:'gather',node:this.nodes.filter(n=>n.type===type&&n.remaining>0).sort((a,b)=>dist(a,w)-dist(b,w))[0]?.id};}
  if(workers.length+ hq.queue.filter(q=>q.type==='worker').length<6)this.hire(hq.id,'worker');
  const plans=[['barracks',1870,440],['tower',1700,530],['dojo',2040,850],['barracks',2200,1080]];
  if(this.population(team)>=this.limit(team)-3&&this.buildings(team,'house').length<6){const i=this.buildings(team,'house').length,w=workers.find(w=>w.order?.type!=='build');if(w)this.build(w.id,'house',1700,850+(i-1)*140);}
  for(const [type,x,y]of plans){if(this.buildings(team).some(b=>b.type===type&&Math.abs(b.x-x)<50))continue;const w=workers.find(w=>w.order?.type!=='build');if(w&&this.canPay(team,BUILDINGS[type].cost))this.build(w.id,type,x,y);break;}
  const pending=plans.find(([type,x])=>!this.buildings(team).some(b=>b.type===type&&Math.abs(b.x-x)<50));const reserve=this.time>80&&pending?BUILDINGS[pending[0]].cost:[0,0];
  for(const b of this.buildings(team,'barracks'))if(b.progress===1&&b.queue.length<2){const type=this.random()<.32?'kunai':this.random()<.16?'medic':'shinobi',cost=UNITS[type].cost;if(this.teams[team].gold>=cost[0]+reserve[0]&&this.teams[team].wood>=cost[1]+reserve[1])this.hire(b.id,type);}
  if(this.time>120&&this.teams[1].gold>350){this.upgrade(1,this.teams[1].attack<=this.teams[1].armor?'attack':'armor');}
  const army=this.units(team).filter(u=>u.type!=='worker'),target=this.buildings(0,'hq')[0];
  const attack=this.time>=150&&army.filter(u=>u.type!=='hero').length>=8;
  for(const u of army){if(u.type==='hero'){if(u.hp<u.maxHP*.3){u.order={type:'move',x:hq.x-30,y:hq.y+40};u.path=null;continue;}const enemy=this.nearestEnemy(u,240);if(enemy){for(let k=0;k<4;k++)if(this.cast(u.id,k))break;}}
   if(target&&attack&&(!u.order||u.order.type==='move')){u.order={type:'attackmove',x:target.x,y:target.y};u.path=null;}
   if(!attack&&!u.order&&dist(u,hq)>320)u.order={type:'move',x:hq.x-170,y:hq.y+50};
  }
 }
 step(dt){if(!this.started||this.paused||this.winner!==null)return;dt=Math.min(dt,.1);this.time+=dt;
  for(const f of this.effects)f.life-=dt;this.effects=this.effects.filter(f=>f.life>0);
  for(const r of this.revives.filter(r=>r.at<=this.time)){const hq=this.buildings(r.team,'hq')[0];if(hq)this.addUnit('hero',r.team,hq.x+(r.team?-120:120),hq.y,{hero:r.hero,level:r.level,xp:r.xp,maxHP:r.maxHP,hp:r.maxHP});}this.revives=this.revives.filter(r=>r.at>this.time);
  if(this.time>=this.botAt){this.botAt=this.time+3;this.bot();}
  for(const b of this.entities.filter(e=>e.alive&&e.kind==='building')){b.cool-=dt;if(b.progress!==1)continue;if(b.queue.length){b.queue[0].left-=dt;if(b.queue[0].left<=0){const q=b.queue.shift(),u=this.addUnit(q.type,b.team,b.x+(b.team?-90:90),b.y+40);if(b.type==='barracks')u.order={type:'move',x:b.x+(b.team?-165:165),y:b.y+80+this.random()*60};}}
   if(b.type==='tower'){const target=this.nearestEnemy(b,240);if(target)this.attack(b,target,dt);}
  }
  const units=this.entities.filter(e=>e.alive&&e.kind==='unit');
  for(const e of units){e.cool-=dt;e.walking=false;for(let k=0;k<4;k++)e.cooldowns[k]=Math.max(0,e.cooldowns[k]-dt);if(e.clone&&e.expires<this.time){e.alive=false;continue;}
   const hq=this.buildings(e.team,'hq')[0];if(hq&&dist(e,hq)<210&&this.time-e.attackAt>5)e.hp=Math.min(e.maxHP,e.hp+e.maxHP*.012*dt);
   if(e.type==='worker'&&this.workerTick(e,dt))continue;
   if(e.type==='medic'&&e.cool<=0){const ally=units.find(a=>a.team===e.team&&a.hp<a.maxHP-15&&dist(a,e)<190);if(ally){ally.hp=Math.min(ally.maxHP,ally.hp+36);e.cool=1.8;this.effects.push({type:'heal',x:ally.x,y:ally.y,life:.6,total:.6});continue;}}
   const o=e.order;
   if(o?.type==='move'){if(this.move(e,o.x,o.y,dt,13)){e.order=null;e.path=null;}continue;}
   let target=o?.type==='attack'?this.get(o.id):null;
   if(!target){const old=this.get(e.target);target=old&&old.team!==e.team&&dist(e,old)<300?old:this.nearestEnemy(e,e.type==='worker'?70:235);}
   if(target){e.target=target.id;this.attack(e,target,dt);}else if(o?.type==='attackmove'){if(this.move(e,o.x,o.y,dt,20)){e.order=null;e.path=null;}}else if(o?.type==='attack'){e.order=null;}
  }
  // Small overlapping footprints: separate close bodies gently, never block bridges.
  for(let i=0;i<units.length;i++)for(let j=i+1;j<units.length;j++){const a=units[i],b=units[j];if(!a.alive||!b.alive)continue;const dx=a.x-b.x,dy=a.y-b.y,d=Math.hypot(dx,dy);if(d>0&&d<15){const push=Math.min((15-d)*.35,28*dt);const ax=clamp(a.x+dx/d*push,25,WORLD.w-25),ay=clamp(a.y+dy/d*push,25,WORLD.h-25),bx=clamp(b.x-dx/d*push,25,WORLD.w-25),by=clamp(b.y-dy/d*push,25,WORLD.h-25);if(!this.blocked(Math.floor(ax/40),Math.floor(ay/40))){a.x=ax;a.y=ay;}if(!this.blocked(Math.floor(bx/40),Math.floor(by/40))){b.x=bx;b.y=by;}}}
  this.entities=this.entities.filter(e=>e.alive);
 }
}
