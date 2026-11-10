// Distinct technique silhouettes: sphere, electrical thrust, rotating chakra shell,
// ground fissure, sand hands, seals, eyes, weapons and animal/puppet silhouettes.
export function drawTechnique(c,f,time,actor){
 const p=Math.max(0,Math.min(1,1-f.life/f.total)),v=f.visual,col=f.color||'#b9deed',face=f.face||1,x=actor?.x??f.x,y=actor?.y??f.y;
 c.save();c.globalAlpha=Math.min(1,f.life*4);c.lineCap='round';c.lineJoin='round';
 const line=(points,color=col,w=3)=>{c.beginPath();points.forEach(([x,y],i)=>i?c.lineTo(x,y):c.moveTo(x,y));c.strokeStyle=color;c.lineWidth=w;c.stroke();};
 const ellipse=(x,y,rx,ry,fill)=>{c.beginPath();c.ellipse(x,y,Math.max(.1,rx),Math.max(.1,ry),0,0,Math.PI*2);if(fill){c.fillStyle=fill;c.fill();}else{c.strokeStyle=col;c.lineWidth=2;c.stroke();}};
 const orb=(x,y,r)=>{const g=c.createRadialGradient(x,y,1,x,y,r);g.addColorStop(0,'#f3ffff');g.addColorStop(.25,'#b5f0ff');g.addColorStop(.6,col);g.addColorStop(1,col+'00');ellipse(x,y,r,r,g);for(let k=0;k<4;k++){c.beginPath();c.ellipse(x,y,r*(.45+k*.12),r*.35,time*7+k,0,Math.PI*1.7);c.strokeStyle='#e8ffffbb';c.lineWidth=2;c.stroke();}};
 const eye=(x,y,color)=>{c.fillStyle='#eeeeef';c.beginPath();c.moveTo(x-30,y);c.quadraticCurveTo(x,y-19,x+30,y);c.quadraticCurveTo(x,y+19,x-30,y);c.fill();ellipse(x,y,10,10,color);ellipse(x,y,4,4,'#373547');};
 if(v==='rasenganGiant'){c.restore();return;}
 if(v==='kirin'&&p<.35){ellipse(f.tx,550,80,13,'#c2e8ff44');c.restore();return;}
 if(v.startsWith('rasengan')){const r=v==='rasenganGiant'?60:28,orbY=y-(actor?.crouching?74:117);orb(x+face*70,orbY,r*(.7+Math.sin(p*Math.PI)*.4));if(v==='rasenganGiant')for(let k=0;k<7;k++)line([[x+face*70,y-117],[x+face*(95+k*12),y-117+Math.sin(k*2+time)*65]],'#c2e9ff66',2);}
 else if(v==='chidori'||v==='lightningCuts'||v==='kirin'){
  const xx=v==='kirin'?f.tx:x+face*75,yy=v==='kirin'?f.ty-105:y-(actor?.crouching?74:120);
  if(v==='kirin'){for(let k=0;k<3;k++)line([[xx-100+k*90,30],[xx-60+k*40,150],[xx+10+k*35,210],[xx-20,310],[xx+15,yy],[xx,yy+70]],'#ccedff',7-k*2);ellipse(xx,yy+80,95*p,15,'#d2eaff55');}
  else{orb(xx,yy,26);for(let k=0;k<8;k++){const a=k*Math.PI/4+time*4;line([[xx,yy],[xx+Math.cos(a)*30,yy+Math.sin(a)*30],[xx+Math.cos(a+.15)*67,yy+Math.sin(a+.15)*67]],'#d7ecff',2);}}
 }
 else if(v==='kaiten'||v==='windBarrier'){
  const r=v==='kaiten'?110:125;ellipse(x,y-95,r,115,col+'18');
  for(let k=0;k<7;k++){c.beginPath();c.ellipse(x,y-45-k*15,r*Math.sin((k+1)/8*Math.PI)*(.85+p*.15),22,time*6+k*.1,0,Math.PI*1.6);c.strokeStyle=col;c.lineWidth=3;c.stroke();}ellipse(x,y-10,r*1.1,21);
 }
 else if(v==='byakugan'||v==='sharingan'||v==='redMoon'){
  const isRed=v!=='byakugan',xx=v==='redMoon'?f.tx:x;eye(xx-27,y-235,isRed?'#d6677d':'#c4c5ee');eye(xx+27,y-235,isRed?'#d6677d':'#c4c5ee');
  if(v==='byakugan')for(const sign of [-1,1]){line([[x+sign*12,y-158],[x+sign*24,y-161],[x+sign*32,y-153]],'#d0cff7',1.5);}
  else if(v==='redMoon'){ellipse(f.tx,f.ty-130,110,120,'#932c4e22');for(let k=0;k<4;k++)line([[f.tx-80+k*45,f.ty-220],[f.tx-70+k*45,f.ty-35]],'#d7709b88',3);}
 }
 else if(v==='palms'||v==='palms128'||v==='lionFists'){
  const n=v==='palms128'?16:8;for(let k=0;k<n;k++){const a=k*Math.PI*2/n;line([[x,y-85],[x+Math.cos(a)*110,y-85+Math.sin(a)*95]],col+'aa',2);}
  ellipse(x,y-2,110,20);if(v==='lionFists'){orb(x+face*75,y-110,47);ellipse(x+face*82,y-126,15,20,'#ecf6ff88');}
 }
 else if(['earth','earthBloom','lotus','lotusStorm','leafKick'].includes(v)){
  const r=v==='earthBloom'?300:175;for(let k=0;k<9;k++){const dx=(k-4)*r/5;line([[x+dx*.3,y],[x+dx*.65,y+15],[x+dx,y+12+Math.sin(k)*10]],'#4c4a43',3);if(p>.2){c.fillStyle='#a49c82';c.fillRect(x+dx,y-5-Math.sin(p*Math.PI)*30-k%3*8,7,9);}}
  if(v.startsWith('lotus')){for(let k=0;k<3;k++){c.beginPath();c.ellipse(f.tx,y-100,65+k*12,150,time*5+k*.7,0,Math.PI*1.7);c.strokeStyle='#e3dfc0';c.lineWidth=2;c.stroke();}}
  if(v==='leafKick'){c.beginPath();c.arc(x,y-80,120,-1+time*9,2+time*9);c.strokeStyle='#b6e7b5';c.lineWidth=9;c.stroke();}
 }
 else if(v==='sandCoffin'||v==='sandBurial'){
  const tx=f.tx;for(let k=0;k<8;k++){line([[tx-90+k*25,y],[tx-70+k*20,y-65-Math.sin(p*Math.PI)*80],[tx-30+k*8,y-155]],'#ceb17d',12);}
  if(v==='sandBurial')for(let k=0;k<18;k++)ellipse(tx+Math.sin(k*6)*120*p,y-40-Math.cos(k)*80,6,4,'#dfc596');
 }
 else if(v==='sandShield'){for(let k=0;k<25;k++){const a=k*2.4+time*2;ellipse(x+Math.cos(a)*70,y-95+Math.sin(a)*105,4,6,'#dbbe87');}}
 else if(['seal','puppetTrap','sealShot'].includes(v)){
  c.save();c.translate(x+face*60,y-95);c.rotate(-.15*face);c.fillStyle='#e4d8b3';c.fillRect(-12,-28,24,56);c.strokeStyle='#9d6156';c.lineWidth=2;c.strokeRect(-9,-24,18,48);c.fillStyle='#684d45';c.font='20px serif';c.textAlign='center';c.fillText('爆',0,8);c.restore();
 }
 else if(v==='tornado'||v==='windSummon'||v==='weaponStorm'||v==='twinDragons'||v==='blackFlame'){
  const xx=f.tx;if(v==='blackFlame'){for(let k=0;k<9;k++){c.beginPath();c.moveTo(xx-90+k*22,y);c.quadraticCurveTo(xx-120+k*25,y-90,xx-60+k*20,y-130-Math.sin(time*16+k)*35);c.quadraticCurveTo(xx-35+k*20,y-40,xx-60+k*22,y);c.fillStyle=k%2?'#6c416e':'#242437';c.fill();}}
  else if(v==='weaponStorm'||v==='twinDragons'){for(let k=0;k<16;k++){const a=k*1.8+time*5,xx2=xx+Math.cos(a)*100,yy=y-100+Math.sin(a)*115;c.save();c.translate(xx2,yy);c.rotate(a);line([[-11,0],[13,0]],'#dddacb',3);line([[0,-11],[0,12]],'#e8e0bf',3);c.restore();}}
  else for(let k=0;k<10;k++){c.beginPath();c.ellipse(xx+Math.sin(time*10+k)*10,y-15-k*20,28+k*7,9+k*.8,time*.7,0,Math.PI*1.8);c.strokeStyle=col;c.lineWidth=3;c.stroke();}
 }
 else if(['fang','wolf','beast'].includes(v)){
  for(let k=0;k<3;k++){c.beginPath();c.ellipse(x,y-90,45+k*20,105,time*12+k,0,Math.PI*1.6);c.strokeStyle='#e9e7d2';c.lineWidth=3;c.stroke();}if(v==='wolf'){for(const ox of [-35,35]){c.beginPath();c.moveTo(x+ox,y-200);c.lineTo(x+ox-18,y-237);c.lineTo(x+ox+20,y-213);c.stroke();}}
 }
 else if(['clones','dog','frog','puppet','puppetDance','crows'].includes(v)){
  ellipse(x,y-5,72,15,col+'44');for(let k=0;k<7;k++){ellipse(x+Math.sin(k*3)*60*p,y-20-k*8,12+18*p,12+12*p,'#d9dfd08a');}
 }
 else if(v==='snakeSword'){line([[x+face*55,y-119],[x+face*185,y-126]],'#e4e9f0',5);line([[x+face*65,y-117],[x+face*172,y-122]],'#b5adcc',1);}
 else if(v==='manda'||v==='snake'){
  const xx=v==='manda'?f.tx:x+face*45;c.beginPath();c.moveTo(xx,y);c.bezierCurveTo(xx-70,y-80,xx+95,y-120,xx+20,y-190);c.strokeStyle='#8f829f';c.lineWidth=v==='manda'?45:14;c.stroke();ellipse(xx+20,y-190,v==='manda'?35:15,v==='manda'?20:10,'#b7a5c3');ellipse(xx+29,y-194,3,3,'#efdf97');
 }
 else if(['healing','shedding','sage','strategy','gates','kyubi'].includes(v)){
  const r=80+Math.sin(p*Math.PI)*20;for(let k=0;k<7;k++)line([[x+Math.sin(k*2)*r,y-10],[x+Math.sin(k*2+.4)*r,y-150-p*70]],col+'bb',3);if(v==='healing'||v==='shedding')for(let k=0;k<5;k++){const xx=x+Math.sin(k*3)*45,yy=y-50-k*20-p*35;line([[xx-6,yy],[xx+6,yy]],col,3);line([[xx,yy-6],[xx,yy+6]],col,3);}
 }
 c.restore();
}
export function drawProjectile(c,p,time){
 c.save();c.translate(p.x,p.y);const col=p.color,visual=p.visual||'';c.shadowColor=col;c.shadowBlur=12;
 if(visual==='rasenganGiant'){const g=c.createRadialGradient(0,0,2,0,0,p.r);g.addColorStop(0,'#fff');g.addColorStop(.3,'#bcefff');g.addColorStop(.75,'#79cce9');g.addColorStop(1,'#8bcff400');c.fillStyle=g;c.beginPath();c.arc(0,0,p.r,0,Math.PI*2);c.fill();for(let k=0;k<5;k++){c.beginPath();c.ellipse(0,0,p.r*(.5+k*.08),p.r*.35,time*7+k,0,Math.PI*1.8);c.strokeStyle='#eaffffbb';c.lineWidth=2;c.stroke();}}
 else if(visual==='wind'||p.style==='fan'){for(let k=0;k<3;k++){c.beginPath();c.arc(0,0,p.r+k*8,Math.PI*.6,Math.PI*1.5);c.strokeStyle=col;c.lineWidth=4-k;c.stroke();}}
 else if(visual==='sandWave'){c.shadowBlur=0;for(let k=0;k<25;k++){const xx=Math.sin(k*5+time*8)*p.r,yy=Math.cos(k*3)*p.r;c.fillStyle=k%2?'#ddc18b':'#b89967';c.fillRect(xx,yy,5+k%3,5);}}
 else if(visual==='snake'||visual==='waterDragon'){c.shadowBlur=0;c.beginPath();c.moveTo(-Math.sign(p.v)*60,0);c.bezierCurveTo(-30,-25,-12,25,15,0);c.strokeStyle=col;c.lineWidth=visual==='waterDragon'?24:12;c.stroke();c.fillStyle=col;c.beginPath();c.ellipse(15,0,20,12,0,0,Math.PI*2);c.fill();c.fillStyle='#ebe1b2';c.fillRect(18,-6,4,3);}
 else if(p.r<20){c.rotate(time*17);c.fillStyle=col;for(let k=0;k<4;k++){c.rotate(Math.PI/2);c.beginPath();c.moveTo(0,0);c.lineTo(-5,-p.r);c.lineTo(5,-p.r*.65);c.closePath();c.fill();}}
 else{const g=c.createRadialGradient(0,0,2,0,0,p.r);g.addColorStop(0,'#fff2c8');g.addColorStop(.4,col);g.addColorStop(1,col+'00');c.fillStyle=g;c.beginPath();c.arc(0,0,p.r,0,Math.PI*2);c.fill();for(let k=0;k<4;k++){c.strokeStyle=col;c.lineWidth=3;c.beginPath();c.moveTo(-Math.sign(p.v)*p.r*.4,(k-1.5)*9);c.quadraticCurveTo(-Math.sign(p.v)*(p.r+25),(k-1.5)*12,-Math.sign(p.v)*(p.r+65),Math.sin(time*20+k)*20);c.stroke();}}
 c.restore();
}
