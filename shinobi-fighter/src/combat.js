import {byId,BASICS} from './roster.js';
import {visualFor} from './techniques.js';
export const ARENA={width:1280,ground:550,gravity:1900};
const clamp=(v,a,b)=>Math.max(a,Math.min(b,v));
export class Fight{
 constructor(player='naruto',enemy='sasuke',difficulty=1){this.ids=[player,enemy];this.difficulty=difficulty;this.wins=[0,0];this.round=1;this.time=0;this.effects=[];this.shots=[];this.summons=[];this.traps=[];this.events=[];this.phase='intro';this.phaseTime=2;this.result=null;this.paused=false;this.seed=481;this.summonSerial=0;this.hitStop=0;this.shake=0;this.reset();}
 random(){this.seed=(Math.imul(this.seed,1664525)+1013904223)>>>0;return this.seed/4294967296;}
 reset(){this.fighters=this.ids.map((id,i)=>{const d=byId(id);return {id,side:i,x:i?940:340,y:ARENA.ground,vx:0,vy:0,hp:d.hp,maxHP:d.hp,facing:i?-1:1,state:'idle',stateTime:0,stateTotal:0,crouching:false,crouchAttack:false,stun:0,cool:[0,0,0,0],attackCD:0,combo:0,comboAt:-10,blocking:false,buff:null,poison:0,aiAt:0,dashCD:0,pending:null,anim:0,hitAt:-10};});this.timer=99;this.hitStop=0;this.shake=0;this.shots=[];this.summons=[];this.traps=[];this.effects=[];this.phase='intro';this.phaseTime=1.8;}
 emit(type,x,y,extra={}){this.effects.push({type,x,y,life:.6,total:.6,...extra});}
 hurt(a,b,damage,extra={}){
  if(b.hp<=0||b.invul>this.time)return false;
  const direction=(extra.originX??a.x)<b.x?1:-1,guarded=b.blocking&&b.stun<=0&&direction*b.facing<0;
  let amount=damage*(a.buff?.power||1)*(b.buff?.defense||1);
  if(guarded)amount*=Math.max(.2,extra.pierce||0);
  b.hp=Math.max(0,b.hp-amount);b.hitAt=this.time;
  const force=(extra.push||105)*(guarded?.22:1)/(byId(b.id).hp/1200),strong=amount>=70;
  b.vx=direction*force;b.hitDirection=direction;b.hitStrength=Math.min(1,amount/110);
  if(!guarded){
   b.stun=Math.max(b.stun,Math.min(extra.stun??(strong?.28:.14),1.4));b.state='hit';b.stateTime=b.stun;b.stateTotal=b.stun;
   if(b.pending&&(strong||['melee','basicshot'].includes(b.pending.kind)))b.pending=null;
   b.crouching=false;b.crouchAttack=false;if(extra.launch)b.vy=-extra.launch;if(extra.poison)b.poison+=extra.poison;
  }else b.guardFlashUntil=this.time+.16;
  if(!extra.pet){this.hitStop=Math.max(this.hitStop,guarded?.018:strong?.055:.028);this.shake=Math.max(this.shake,guarded?1:strong?4:1.8);}
  this.emit(guarded?'guard':'hit',b.x-direction*15,b.y-(b.crouching?60:100),{color:extra.color||'#ffdfad',strength:strong?1.6:1,life:.24,total:.24});
  this.events.push({type:guarded?'block':'hit',side:b.side,amount});return !guarded;
 }
 targetBox(target){
  if(target.owner===undefined)return {x:target.x,y:target.y-(target.crouching?52:100),rx:25,ry:target.crouching?48:80};
  const sizes={clone:[76,24,72],dog:[25,35,24],puppet:[52,28,45],crow:[112,22,18],frog:[38,43,35],snake:[65,65,55]},s=sizes[target.pet]||sizes.clone;
  return {x:target.x,y:ARENA.ground-s[0],rx:s[1],ry:s[2]};
 }
 hurtTarget(attacker,target,damage,extra={}){
  if(target.owner===undefined)return this.hurt(attacker,target,damage,extra);
  if(target.hp<=0||target.life<=0)return false;
  const box=this.targetBox(target);target.hp=Math.max(0,target.hp-damage*(attacker.buff?.power||1));target.hitAt=this.time;target.stun=Math.min(.7,extra.stun??.12);
  this.emit('hit',target.x,box.y,{color:extra.color||'#f2dba6',life:.2,total:.2});this.events.push({type:'petHit',side:target.owner});
  if(target.hp<=0){target.life=0;this.emit('smoke',target.x,ARENA.ground-45,{color:'#d5dccb',life:.45,total:.45});}
  return true;
 }
 enemyTargets(side){return [this.fighters[1-side],...this.summons.filter(s=>s.owner!==side&&s.hp>0&&s.life>0)];}
 resolvePending(a,b){
  const p=a.pending;if(!p||this.time<p.at)return;
  const d=byId(a.id);
  if(p.kind==='basicshot'){
   this.shots.push({owner:a.side,x:a.x+a.facing*45,y:a.y-(a.crouching?60:135),v:a.facing*p.extra.shot,damage:p.damage,r:p.extra.size,color:p.extra.color,life:p.range/p.extra.shot,delay:0,style:d.style,visual:a.id==='temari'?'wind':'weapons'});a.pending=null;return;
  }
  if(p.kind==='storm')this.emit('fall',p.zone+(this.random()-.5)*80,ARENA.ground-230,{color:p.extra.color,life:.5,total:.5,style:d.style,visual:a.skillVisual});
  const targets=this.enemyTargets(a.side).filter(target=>{
   if(target.hp<=0)return false;const dx=target.x-a.x,box=this.targetBox(target);
   if(p.kind==='storm')return Math.abs(target.x-p.zone)<p.range&&box.y+box.ry>ARENA.ground-200;
   if(p.kind==='area')return Math.abs(target.x-p.zone)<p.range&&Math.abs(target.y-a.y)<175;
   if(dx*a.facing<-20||Math.abs(dx)> (p.kind==='rush'?110:p.range))return false;
   if(p.extra.level==='high'&&target.crouching)return false;
   if(p.kind==='melee'){const strikeY=a.y-(a.crouchAttack?42:a.state==='kick'?76:112);return Math.abs(box.y-strikeY)<box.ry+(a.state==='kick'?45:30);}
   return Math.abs(target.y-a.y)<165;
  }).sort((t,u)=>Math.abs(t.x-a.x)-Math.abs(u.x-a.x));
  if(p.kind==='rush'&&!targets.length&&this.time<p.expires){p.at=this.time+.025;return;}
  const hits=['area','storm'].includes(p.kind)?targets:targets.slice(0,1);
  for(const target of hits){this.hurtTarget(a,target,p.damage,p.extra);if(p.kind==='barrage')this.emit('palm',target.x,this.targetBox(target).y,{color:p.extra.color,life:.3,total:.3});}
  if((p.kind==='barrage'||p.kind==='storm')&&--p.left>0){p.at=this.time+(p.kind==='storm'?.2:.14);if(a.stun<=0){a.state='cast';a.stateTime=Math.max(.18,a.stateTime);a.stateTotal=Math.max(a.stateTotal,a.stateTime);}}else a.pending=null;
 }

 action(side,action){if(this.phase!=='fight'||this.paused)return false;const a=this.fighters[side],b=this.fighters[1-side],d=byId(a.id);if(a.hp<=0||a.stun>0||a.stateTime>0||a.blocking)return false;
  if(action==='jump'){if(a.y<ARENA.ground-1)return false;a.vy=-680;a.state='jump';a.crouching=false;a.crouchAttack=false;this.emit('dust',a.x,a.y,{life:.35,total:.35});return true;}
  if(action==='dash'){if(a.dashCD>0)return false;a.dashCD=1.2;a.vx=a.facing*700;a.state='dash';a.stateTime=.18;a.stateTotal=.18;a.invul=this.time+.09;this.emit('smoke',a.x,a.y-60,{color:d.color});return true;}
  if(['light','heavy','punch','kick'].includes(action)){
   if(a.attackCD>0)return false;const heavy=action==='heavy',kick=action==='kick',punch=action==='punch',basic=BASICS[a.id],ranged=!!basic.shot&&!punch&&!kick;a.combo=this.time-a.comboAt<.95?(a.combo%3)+1:1;a.comboAt=this.time;a.state=kick?'kick':punch?'punch':heavy?'heavy':'attack';a.stateTime=heavy?.48:kick?.4:.28;a.stateTotal=a.stateTime;a.crouchAttack=a.crouching;a.attackCD=heavy?basic.rate*1.6:kick?Math.max(.4,basic.rate):basic.rate;a.vx*=.15;
   const range=punch?105:kick?(a.crouching?145:155):basic.range+(heavy?32:0);const damage=(heavy?basic.heavy:kick?basic.damage*1.2:basic.damage+(a.combo-1)*6)*d.power;
   this.emit('slash',a.x+a.facing*60,a.y-(a.crouching?45:kick?75:110),{color:d.color,face:a.facing,style:kick?'kick':d.style,life:.25,total:.25});a.pending={at:this.time+(heavy?.18:basic.delay),kind:ranged?'basicshot':'melee',range,damage,extra:{launch:heavy&&a.combo===3?280:0,push:heavy?basic.push*1.6:kick?basic.push*1.2:basic.push,level:a.crouching?'low':heavy||kick?'mid':'high',pierce:basic.pierce,color:d.color,shot:basic.shot,size:basic.size}};return true;
  }
  const index=Number(action);if(!Number.isInteger(index)||index<0||index>3)return false;const m=d.skills[index];if(a.cool[index]>0)return false;
  a.cool[index]=m.cool;a.state='cast';a.stateTime=index===3?.85:.45;a.moveName=m.name;a.skillIndex=index;a.skillVisual=visualFor(a.id,index);a.stateTotal=a.stateTime;a.crouchAttack=false;a.vx=0;this.events.push({type:'skill',side,hero:a.id,index,name:m.name,ultimate:index===3});this.emit('technique',a.x,a.y,{tx:b.x,ty:b.y,face:a.facing,hero:a.id,index,owner:side,visual:a.skillVisual,color:m.color,radius:m.radius||m.range||170,life:m.type==='storm'?Math.max(1,(m.count||1)*.2+.4):index===3?1.05:.7,total:m.type==='storm'?Math.max(1,(m.count||1)*.2+.4):index===3?1.05:.7});
  if(m.type==='heal'){a.hp=Math.min(a.maxHP,a.hp+m.damage);this.emit('heal',a.x,a.y-75,{color:m.color,life:1,total:1});}
  else if(m.type==='buff'){a.buff={...m,until:this.time+m.duration};if(m.heal)a.hp=Math.min(a.maxHP,a.hp+m.heal);this.emit('aura',a.x,a.y-75,{color:m.color,life:1,total:1});}
  else if(m.type==='summon'){if(a.id==='kiba'&&m.pet==='dog')a.dogReleased=true;this.summons=this.summons.filter(s=>s.owner!==side||s.slot!==index);for(let k=0;k<m.count;k++)this.summons.push({id:++this.summonSerial,owner:side,x:clamp(a.x-a.facing*(35+k*30),55,1225),y:ARENA.ground,hp:m.pet==='snake'?650:m.pet==='frog'?340:m.pet==='puppet'?250:m.pet==='dog'?210:m.pet==='crow'?75:120,maxHP:m.pet==='snake'?650:m.pet==='frog'?340:m.pet==='puppet'?250:m.pet==='dog'?210:m.pet==='crow'?75:120,stun:0,life:m.duration,slot:index,cool:.4+k*.18,damage:m.damage,pet:m.pet||'clone',color:m.color});}
  else if(m.type==='projectile'){for(let k=0;k<(m.count||1);k++)this.shots.push({owner:side,x:a.x+a.facing*45,y:a.y-(a.crouching?80:125)-k*13,v:a.facing*m.speed,damage:m.damage,r:m.size,color:m.color,life:m.range?m.range/m.speed:2.6,delay:k*.12,poison:m.poison,style:d.style,visual:a.skillVisual});}
  else if(m.type==='trap'){this.traps.push({owner:side,x:clamp(a.x+a.facing*m.range,45,1235),life:6,damage:m.damage,color:m.color,visual:a.skillVisual,arm:.4});}
  else if(m.type==='rush'){a.vx=a.facing*680;a.state='rush';a.stateTime=Math.max(.3,m.range/680);a.stateTotal=a.stateTime;a.pending={at:this.time+.08,kind:'rush',expires:this.time+a.stateTime,range:m.range,damage:m.damage,extra:m};}
  else if(m.type==='barrage'){a.stateTime=.18+m.count*.14;a.stateTotal=a.stateTime;a.pending={at:this.time+.16,kind:'barrage',range:m.range,damage:m.damage,count:m.count,left:m.count,extra:{...m,push:18,stun:.08}};}
  else if(m.type==='storm'){const zone=clamp(b.x,a.x-(m.range||600),a.x+(m.range||600));a.pending={at:this.time+(m.windup||.28),kind:'storm',range:m.radius||165,zone,damage:m.damage,count:m.count,left:m.count,extra:m};const cue=this.effects.at(-1);cue.tx=zone;}
  else if(m.type==='shadow'){a.pending={at:this.time+.2,kind:'shadow',range:m.range,damage:m.damage,extra:m};this.emit('shadow',a.x,a.y,{tx:b.x,color:m.color,life:.65,total:.65});}
  else {const zone=m.target==='opponent'?clamp(b.x,a.x-m.range,a.x+m.range):a.x;a.pending={at:this.time+.24,kind:'area',zone,range:m.radius,damage:m.damage,extra:m};if(m.target==='opponent')this.effects.at(-1).tx=zone;}
  return true;
 }
 ai(dt){const a=this.fighters[1],b=this.fighters[0],distance=Math.abs(a.x-b.x);if(this.time<a.aiAt)return {move:a.aiMove||0,block:a.aiBlock||false,crouch:a.aiCrouch||false};a.aiAt=this.time+.14+this.random()*.17;let move=distance>150?(b.x>a.x?1:-1):distance<70?(a.x>b.x?1:-1)*.5:0;let block=false;
  if(a.stateTime<=0&&a.stun<=0){const danger=(b.state==='attack'||b.state==='heavy'||b.state==='rush')&&distance<200||this.shots.some(p=>p.owner===0&&Math.abs(p.x-a.x)<230);block=danger&&this.random()<.45*this.difficulty;
   if(!block){if(a.hp<a.maxHP*.5&&byId(a.id).skills[2].type==='heal')this.action(1,2);
    if(a.cool[3]<=0&&distance<440)this.action(1,3);
    if(this.random()<.36*this.difficulty)this.action(1,Math.floor(this.random()*3));
    if(Math.min(distance,...this.summons.filter(s=>s.owner===0&&s.hp>0).map(s=>Math.abs(s.x-a.x)))<145)this.action(1,b.crouching?'kick':this.random()<.6?'punch':this.random()<.65?'kick':'heavy');
    else if(distance>350&&this.random()<.12)this.action(1,'dash');
    if(danger&&this.random()<.12)this.action(1,'jump');
   }
  }const crouch=!block&&this.shots.some(p=>p.owner===0&&Math.abs(p.x-a.x)<300&&p.r<20)&&this.random()<.6;
  a.aiMove=move;a.aiBlock=block;a.aiCrouch=crouch;return {move,block,crouch};
 }
 step(dt,input={}){if(this.paused||this.phase==='complete')return;dt=Math.min(dt,.05);this.shake=Math.max(0,this.shake-dt*20);if(this.hitStop>0){const freeze=Math.min(dt,this.hitStop);this.hitStop-=freeze;dt-=freeze;if(dt<=0)return;}this.time+=dt;
  for(const f of this.effects)f.life-=dt;this.effects=this.effects.filter(f=>f.life>0);
  if(this.phase!=='fight'){if(this.phase==='round'){for(const f of this.fighters){f.vx*=Math.pow(.03,dt);f.x=clamp(f.x+f.vx*dt,50,1230);f.vy+=ARENA.gravity*dt;f.y+=f.vy*dt;if(f.y>=ARENA.ground){f.y=ARENA.ground;f.vy=0;}}}this.phaseTime-=dt;if(this.phaseTime<=0){if(this.phase==='intro')this.phase='fight';else if(this.phase==='round'){if(this.wins.some(n=>n>=2)){this.phase='complete';this.result=this.wins[0]>this.wins[1]?0:1;}else{this.round++;this.reset();}}}return;}
  this.timer-=dt;const ai=this.ai(dt),controls=[input,ai];
  for(let i=0;i<2;i++){const a=this.fighters[i],b=this.fighters[1-i],d=byId(a.id),control=controls[i];a.anim+=dt;a.attackCD=Math.max(0,a.attackCD-dt);a.dashCD=Math.max(0,a.dashCD-dt);a.stun=Math.max(0,a.stun-dt);a.stateTime=Math.max(0,a.stateTime-dt);a.cool=a.cool.map(v=>Math.max(0,v-dt));if(a.buff&&this.time>=a.buff.until)a.buff=null;
   if(a.poison>0){const dot=Math.min(a.poison,12*dt);a.hp=Math.max(0,a.hp-dot);a.poison-=dot;}
   a.crouching=!!control.crouch&&a.stun<=0&&a.y>=ARENA.ground-1;if(a.stateTime>0&&a.crouchAttack)a.crouching=true;
   a.blocking=!!control.block&&a.stun<=0&&a.stateTime<=0&&a.y>=ARENA.ground-1;
   if(a.stateTime<=0&&a.stun<=0){a.facing=b.x>a.x?1:-1;const move=a.blocking||a.crouching?0:(control.move||0);const desired=move*d.speed*(a.buff?.speed||1);a.vx+=(desired-a.vx)*(1-Math.exp(-(move?15:21)*dt));if(Math.abs(a.vx)<.5)a.vx=0;a.crouchAttack=false;a.state=a.y<ARENA.ground-2?'jump':a.blocking?'guard':a.crouching?'crouch':a.landingUntil>this.time?'land':move?'walk':'idle';}
   else if(a.state==='hit')a.vx*=Math.pow(.02,dt);
   a.x=clamp(a.x+a.vx*dt,50,1230);a.vy+=ARENA.gravity*dt;a.y+=a.vy*dt;if(a.y>=ARENA.ground){if(a.vy>300){a.landingUntil=this.time+.14;this.emit('dust',a.x,ARENA.ground,{life:.32,total:.32});}a.y=ARENA.ground;a.vy=0;}
   this.resolvePending(a,b);
  }
  // Soft body collision; jumping over a fighter is allowed.
  const [a,b]=this.fighters;if(Math.abs(a.y-b.y)<85&&Math.abs(a.x-b.x)<52){const sign=a.x<b.x?-1:1,delta=(52-Math.abs(a.x-b.x))/2;a.x=clamp(a.x+sign*delta,50,1230);b.x=clamp(b.x-sign*delta,50,1230);}
  for(const p of this.shots){
   p.life-=dt;p.delay-=dt;if(p.delay>0)continue;p.x+=p.v*dt;
   const targets=this.enemyTargets(p.owner).filter(t=>{const b=this.targetBox(t);return t.hp>0&&Math.abs(t.x-p.x)<p.r+b.rx&&Math.abs(b.y-p.y)<p.r+b.ry;}).sort((a,b)=>Math.abs(a.x-p.x)-Math.abs(b.x-p.x));
   if(targets.length){this.hurtTarget(this.fighters[p.owner],targets[0],p.damage,{poison:p.poison,color:p.color,originX:p.x-Math.sign(p.v)*30,push:p.r>40?200:100});p.life=0;}
   if(p.x<0||p.x>1280)p.life=0;
  }
  this.shots=this.shots.filter(p=>p.life>0);
  for(const s of this.summons){
   s.life-=dt;s.cool-=dt;s.stun=Math.max(0,s.stun-dt);if(s.hp<=0||s.life<=0){if(s.life<=0&&s.hp>0)this.emit('smoke',s.x,ARENA.ground-45,{life:.4,total:.4,color:'#d9dfd1'});continue;}
   if(this.fighters[s.owner].hp<=0){s.life=0;continue;}if(s.stun>0)continue;
   const target=this.enemyTargets(s.owner).filter(t=>t.hp>0).sort((a,b)=>Math.abs(a.x-s.x)-Math.abs(b.x-s.x))[0];if(!target)continue;
   const direction=target.x>s.x?1:-1;if(Math.abs(s.x-target.x)>48)s.x+=direction*230*dt;s.facing=direction;
   if(Math.abs(s.x-target.x)<70&&s.cool<=0&&target.y>ARENA.ground-100){this.hurtTarget(this.fighters[s.owner],target,s.damage,{color:s.color,push:22,stun:.055,originX:s.x,pet:true});s.cool=1.05;}
  }
  this.summons=this.summons.filter(s=>s.life>0&&s.hp>0);
  for(const t of this.traps){t.life-=dt;t.arm-=dt;const target=this.enemyTargets(t.owner).find(b=>b.hp>0&&Math.abs(t.x-b.x)<70&&b.y>ARENA.ground-90);if(t.arm<=0&&target){this.hurtTarget(this.fighters[t.owner],target,t.damage,{push:190,color:t.color,launch:200,originX:t.x});this.emit('ring',t.x,ARENA.ground-10,{radius:110,color:t.color});t.life=0;}}
  this.traps=this.traps.filter(t=>t.life>0);
  if(this.fighters.some(f=>f.hp<=0)||this.timer<=0){const a=this.fighters[0],b=this.fighters[1];const winner=a.hp/a.maxHP>=b.hp/b.maxHP?0:1;this.wins[winner]++;this.roundWinner=winner;this.phase='round';this.phaseTime=2.6;this.events.push({type:'round',winner});}
 }
}
