import {WORLD,BUILDINGS,HEROES} from './engine.js';
export class Renderer{
 constructor(canvas,game){this.canvas=canvas;this.ctx=canvas.getContext('2d');this.game=game;this.camera={x:1000,y:870,zoom:.67};this.width=0;this.height=0;this.decor=[];let seed=271;const rand=()=>{seed=(Math.imul(seed,1664525)+1013904223)>>>0;return seed/4294967296;};
  for(let k=0;k<540;k++){const x=rand()*WORLD.w,y=rand()*WORLD.h;const inBase=(Math.hypot(x-330,y-1170)<285)||(Math.hypot(x-2070,y-480)<295);const road=Math.abs(y-1050+x*.25)<78||Math.abs(y-1320+x*.12)<60||Math.abs(y-500)<55;const river=Math.abs(x-1200)<115;if(!inBase&&!road&&!river)this.decor.push({x,y,size:rand()*17+18,kind:rand()<.91?'tree':'rock',shade:rand()});}
  this.terrain=document.createElement('canvas');this.terrain.width=WORLD.w;this.terrain.height=WORLD.h;this.drawTerrain();
 }
 resize(){const r=this.canvas.getBoundingClientRect();this.width=r.width;this.height=r.height;this.dpr=Math.min(devicePixelRatio||1,2);this.canvas.width=Math.floor(this.width*this.dpr);this.canvas.height=Math.floor(this.height*this.dpr);}
 screen(x,y){return {x:(x-this.camera.x)*this.camera.zoom+this.width/2,y:(y-this.camera.y)*this.camera.zoom+this.height/2};}
 world(x,y){return {x:(x-this.width/2)/this.camera.zoom+this.camera.x,y:(y-this.height/2)/this.camera.zoom+this.camera.y};}
 drawTerrain(){const c=this.terrain.getContext('2d');c.fillStyle='#536b40';c.fillRect(0,0,WORLD.w,WORLD.h);
  let seed=12;const rnd=()=>{seed=(Math.imul(seed,1664525)+1013904223)>>>0;return seed/4294967296;};
  for(let k=0;k<24000;k++){const x=rnd()*WORLD.w,y=rnd()*WORLD.h;c.fillStyle=['#6c7d4930','#1b432f30','#aec67912','#d8d39908'][k%4];c.fillRect(x,y,2+rnd()*10,1+rnd()*4);}
  const road=(points,width)=>{c.beginPath();points.forEach(([x,y],i)=>i?c.lineTo(x,y):c.moveTo(x,y));c.lineWidth=width;c.lineCap='round';c.lineJoin='round';c.strokeStyle='#98a16c';c.stroke();c.lineWidth=width-10;c.strokeStyle='#b0ae7c';c.stroke();c.lineWidth=1;c.strokeStyle='#bec18c';c.stroke();};
  road([[300,1170],[670,970],[1040,870],[1370,875],[1730,670],[2050,480]],67);
  road([[720,980],[920,470],[1200,420],[1560,420],[1770,650]],37);
  road([[700,980],[990,1340],[1200,1300],[1510,1320],[1750,670]],39);
  // Sealed river with three broad wooden crossings; navigation uses the same bands.
  c.fillStyle='#315d5c';c.fillRect(1160,0,80,WORLD.h);c.fillStyle='#244d4b';c.fillRect(1160,0,7,WORLD.h);c.fillRect(1233,0,7,WORLD.h);
  for(let y=0;y<WORLD.h;y+=28){c.strokeStyle='#b2d9b01d';c.lineWidth=2;c.beginPath();c.moveTo(1174,y);c.lineTo(1194,y+4);c.moveTo(1205,y+14);c.lineTo(1224,y+18);c.stroke();}
  for(const y of [420,860,1300]){c.fillStyle='#312e2680';c.fillRect(1140,y-100,123,205);c.fillStyle='#867250';c.fillRect(1147,y-99,106,198);for(let b=-94;b<99;b+=13){c.fillStyle=b%2?'#ad9569':'#98805a';c.fillRect(1147,y+b,106,10);}c.fillStyle='#d5ba81';c.fillRect(1143,y-97,7,193);c.fillRect(1250,y-97,7,193);for(let b=-95;b<=95;b+=38){c.fillStyle='#504734';c.fillRect(1139,y+b,14,11);c.fillRect(1246,y+b,14,11);}}
  for(const [x,y]of [[330,1170],[2070,480]]){c.beginPath();c.ellipse(x,y+20,260,205,0,0,Math.PI*2);c.fillStyle='#c3b98d30';c.fill();c.strokeStyle='#e6d9aa20';c.lineWidth=3;c.stroke();}
  // Weathered route stones and grass tufts.
  for(let k=0;k<160;k++){const x=rnd()*WORLD.w,y=rnd()*WORLD.h;if(Math.abs(x-1200)<70)continue;c.strokeStyle='#c4d29422';c.lineWidth=1;c.beginPath();c.moveTo(x,y);c.lineTo(x-4,y-6);c.moveTo(x,y);c.lineTo(x+4,y-8);c.stroke();}
 }
 ellipse(c,x,y,rx,ry,fill){c.fillStyle=fill;c.beginPath();c.ellipse(x,y,rx,ry,0,0,Math.PI*2);c.fill();}
 tree(c,t){const {x,y,size:s}=t;this.ellipse(c,x+8,y+5,s*.9,s*.4,'#0c241e46');c.fillStyle='#63513a';c.fillRect(x-3,y-s*.9,6,s);const shades=t.shade>.5?['#284e37','#3c6342','#5a7b49']:['#2d523b','#436a43','#6a844c'];for(let k=0;k<3;k++){const w=s*(1-k*.16),yy=y-s*.35-k*s*.48;c.fillStyle=shades[k];c.beginPath();c.moveTo(x,yy-s*.9);c.quadraticCurveTo(x+w*.3,yy-s*.35,x+w,yy+s*.28);c.quadraticCurveTo(x,yy+s*.62,x-w,yy+s*.28);c.quadraticCurveTo(x-w*.3,yy-s*.35,x,yy-s*.9);c.fill();}c.strokeStyle='#aac17925';c.lineWidth=2;c.beginPath();c.moveTo(x,y-s*2.1);c.lineTo(x-s*.5,y-s*1.4);c.stroke();}
 rock(c,t){const {x,y,size:s}=t;this.ellipse(c,x,y+3,s*.7,s*.3,'#122c2244');c.fillStyle='#72786a';c.beginPath();c.moveTo(x-s*.6,y);c.lineTo(x-s*.4,y-s*.5);c.lineTo(x+s*.25,y-s*.7);c.lineTo(x+s*.65,y-s*.15);c.lineTo(x+s*.5,y+s*.1);c.closePath();c.fill();c.fillStyle='#9b9c80';c.beginPath();c.moveTo(x-s*.4,y-s*.5);c.lineTo(x+s*.25,y-s*.7);c.lineTo(x+s*.65,y-s*.15);c.lineTo(x,y-s*.2);c.closePath();c.fill();}
 building(c,e,selected=false,ghost=false){const d=BUILDINGS[e.type],x=e.x,y=e.y,s=d.size;const own=e.team===0,roof=own?'#ad6147':'#9a8352',highlight=own?'#d38d68':'#c8af72';
  if(selected){this.ellipse(c,x,y+16,s+18,(s+18)*.58,'#bad48012');c.strokeStyle=own?'#c4e698':'#e7b28a';c.lineWidth=2;c.beginPath();c.ellipse(x,y+16,s+18,(s+18)*.58,0,0,Math.PI*2);c.stroke();}
  this.ellipse(c,x+12,y+18,s+14,s*.52,'#11251b55');
  c.save();if(ghost)c.globalAlpha=.6;if(e.progress<1)c.globalAlpha=.5+e.progress*.5;
  if(e.type==='tower'){
   c.fillStyle='#a4a182';c.beginPath();c.moveTo(x-22,y+20);c.lineTo(x-15,y-72);c.lineTo(x+15,y-72);c.lineTo(x+24,y+20);c.closePath();c.fill();c.fillStyle='#777c65';c.fillRect(x,y-70,15,88);c.fillStyle='#dbca9c';c.fillRect(x-24,y-75,48,12);c.fillStyle='#29392e';c.fillRect(x-13,y-62,26,18);c.fillStyle=roof;c.beginPath();c.moveTo(x-35,y-80);c.lineTo(x,y-105);c.lineTo(x+35,y-80);c.closePath();c.fill();c.strokeStyle=highlight;c.lineWidth=3;c.stroke();
  }else{
   const w=s*.94,h=s*.8;c.fillStyle='#c4b793';c.fillRect(x-w,y-h*.7,w*2,h*1.1);c.fillStyle='#a79976';c.fillRect(x+3,y-h*.7,w-3,h*1.1);c.fillStyle='#635a43';c.fillRect(x-15,y-h*.25,30,h*.68);c.fillStyle='#d3bc87';c.fillRect(x-20,y+h*.37,40,7);
   for(const n of [-1,1]){c.fillStyle='#424f3e';c.fillRect(x+n*w*.67-9,y-h*.35,18,16);c.strokeStyle='#d3c69b';c.lineWidth=2;c.strokeRect(x+n*w*.67-9,y-h*.35,18,16);}
   c.fillStyle=roof;c.beginPath();c.moveTo(x-w-14,y-h*.63);c.quadraticCurveTo(x-w*.4,y-h*1.04,x,y-h*1.48);c.quadraticCurveTo(x+w*.5,y-h*1.03,x+w+14,y-h*.63);c.lineTo(x+w+7,y-h*.4);c.quadraticCurveTo(x,y-h*.72,x-w-10,y-h*.4);c.closePath();c.fill();c.strokeStyle=highlight;c.lineWidth=3;c.stroke();
   c.strokeStyle='#713e324d';c.lineWidth=2;for(let k=-3;k<=3;k++){c.beginPath();c.moveTo(x+k*w*.25,y-h*(1.4-Math.abs(k)*.17));c.lineTo(x+k*w*.34,y-h*.55);c.stroke();}
   if(e.type==='hq'){c.fillStyle='#d6c6a1';c.fillRect(x-35,y-h*1.7,70,27);c.fillStyle=roof;c.beginPath();c.moveTo(x-45,y-h*1.7);c.lineTo(x,y-h*2.07);c.lineTo(x+45,y-h*1.7);c.closePath();c.fill();c.fillStyle='#283e31';c.font='20px serif';c.textAlign='center';c.fillText(own?'木':'砂',x,y-h*1.4);}
   if(e.type==='dojo'){c.fillStyle='#d7c69c';c.fillRect(x-12,y-h*.93,24,27);c.fillStyle='#6c513e';c.font='20px serif';c.textAlign='center';c.fillText('忍',x,y-h*.6);}
   if(e.type==='barracks'){for(const dx of [-1,1]){c.strokeStyle='#5d5140';c.lineWidth=4;c.beginPath();c.moveTo(x+dx*w*.9,y+20);c.lineTo(x+dx*w*.9,y-45);c.stroke();c.fillStyle=own?'#8fa86a':'#d2aa77';c.fillRect(x+dx*w*.9,y-45,22*dx,19);}}
  }
  c.restore();
  if(e.progress<1){const w=70;c.fillStyle='#101d18';c.fillRect(x-w/2,y+32,w,5);c.fillStyle='#d3b76b';c.fillRect(x-w/2,y+32,w*e.progress,5);c.fillStyle='#e9d9aa';c.textAlign='center';c.font='10px sans-serif';c.fillText('Строительство · '+Math.floor(e.progress*100)+'%',x,y+51);}
  else if(e.queue?.length){c.fillStyle='#182b21';c.fillRect(x-35,y+34,70,4);c.fillStyle='#d4c184';c.fillRect(x-35,y+34,70*(1-e.queue[0].left/e.queue[0].total),4);}
  if(selected||e.hp<e.maxHP*.95)this.bar(c,e,s*1.5,y-s*(e.type==='hq'?2.2:1.55));
 }
 bar(c,e,width,y){c.fillStyle='#12211dd9';c.fillRect(e.x-width/2-1,y-1,width+2,5);c.fillStyle=e.team===0?'#b8d58b':'#dba278';c.fillRect(e.x-width/2,y,width*Math.max(0,e.hp/e.maxHP),3);}
 ninja(c,e,selected,time){const kit=HEROES[e.hero],isHero=e.type==='hero',scale=isHero?1.35:1,walk=e.walking?Math.sin(time*12+e.id)*3:0,swing=e.swingUntil>time,cast=e.castUntil>time,face=e.facing|| (e.team?-1:1);const x=e.x,y=e.y;
  this.ellipse(c,x,y+3,11*scale,5*scale,'#10251e66');
  if(selected){c.strokeStyle=e.team===0?'#c5e68d':'#e9ab86';c.lineWidth=1.6;c.beginPath();c.ellipse(x,y+3,15*scale,7*scale,0,0,Math.PI*2);c.stroke();}
  c.save();c.translate(x,y);c.scale(scale,scale);if(e.clone)c.globalAlpha=.66;
  const color=kit?.color||(e.type==='medic'?'#b9c8a1':e.type==='worker'?'#949465':e.team?'#a78c68':'#789568');const hair=kit?.hair|| (e.team?'#6f4d37':'#2b3e31');
  // Separate sandals, leaning torso, arms, face and metal forehead protector.
  c.strokeStyle='#263a35';c.lineWidth=5;c.lineCap='round';c.beginPath();c.moveTo(-4,-11);c.lineTo(-5+walk,0);c.moveTo(4,-11);c.lineTo(5-walk,0);c.stroke();c.strokeStyle='#afb5a2';c.lineWidth=2;c.beginPath();c.moveTo(-7+walk,0);c.lineTo(-2+walk,0);c.moveTo(3-walk,0);c.lineTo(8-walk,0);c.stroke();
  c.fillStyle=color;c.beginPath();c.moveTo(-7,-26);c.lineTo(7,-26);c.lineTo(9,-11);c.lineTo(-8,-11);c.closePath();c.fill();c.fillStyle='#192c3977';c.fillRect(-8,-13,16,4);
  c.strokeStyle=color;c.lineWidth=5;c.beginPath();c.moveTo(-6,-23);c.lineTo(-11+(swing?-4:walk*.8),-13-(cast?12:0));c.moveTo(6,-23);c.lineTo(swing?face*19:11,swing?-23:-14-(cast?12:0));c.stroke();
  c.fillStyle='#e3bc92';this.ellipse(c,swing?face*19:11,swing?-23:-14-(cast?12:0),2.6,2.6,'#e3bc92');
  this.ellipse(c,0,-31,7,8,'#dfbb92');
  c.fillStyle=hair;c.beginPath();c.moveTo(-7,-32);c.lineTo(-9,-39);c.lineTo(-4,-38);c.lineTo(-3,-43);c.lineTo(1,-39);c.lineTo(5,-42);c.lineTo(6,-37);c.lineTo(10,-38);c.lineTo(7,-31);c.closePath();c.fill();
  c.fillStyle='#253b40';c.fillRect(-7,-34,14,4);c.fillStyle='#b6c3b9';c.fillRect(-4,-34,8,3);c.fillStyle='#385443';c.fillRect(-1,-33,2,1);c.fillStyle='#273433';c.fillRect(-4,-28,2,1);c.fillRect(3,-28,2,1);
  if(e.hero==='naruto'){c.fillStyle='#674c32';c.fillRect(-6,-25,3,1);c.fillRect(3,-25,3,1);}
  if(e.hero==='gaara'){c.fillStyle='#b09869';this.ellipse(c,-9,-21,5,9,'#b09869');c.strokeStyle='#694f37';c.lineWidth=2;c.beginPath();c.moveTo(-13,-25);c.lineTo(-5,-18);c.stroke();}
  if(e.hero==='sakura'){c.fillStyle=hair;c.fillRect(-8,-33,3,12);c.fillRect(6,-33,3,12);}
  if(e.type==='kunai'||swing){c.strokeStyle='#d6d9c0';c.lineWidth=2;c.beginPath();c.moveTo(swing?face*19:12,swing?-23:-16);c.lineTo(swing?face*27:18,swing?-30:-25);c.stroke();}
  if(e.type==='worker'){c.strokeStyle='#735940';c.lineWidth=2;c.beginPath();c.moveTo(12,-12);c.lineTo(15,-34);c.stroke();c.fillStyle='#b2b7a0';c.fillRect(10,-36,14,4);if(e.carry){c.fillStyle='#d1b36d';c.fillRect(-12,-20,7,8);}}
  if(e.type==='medic'){c.fillStyle='#efe7c4';c.fillRect(-3,-23,6,2);c.fillRect(-1,-25,2,6);}
  if(e.shieldUntil>time){c.strokeStyle='#a6d5da88';c.lineWidth=1.3;c.beginPath();c.ellipse(0,-22,18,27,0,0,Math.PI*2);c.stroke();}
  if(cast){c.strokeStyle='#b7e7ed99';c.lineWidth=2;c.beginPath();c.arc(0,-19,21,time*8,time*8+4.6);c.stroke();}
  c.restore();if(isHero||selected||e.hp<e.maxHP*.95)this.bar(c,e,isHero?39:26,y-(isHero?67:48));
  if(isHero&&!e.clone){c.font='bold 10px Manrope, sans-serif';c.textAlign='center';c.fillStyle=e.team?'#ecd2b0':'#e4ebcd';c.shadowColor='#14241d';c.shadowBlur=3;c.fillText(kit?.short+' · '+e.level,x,y-73);c.shadowBlur=0;}
 }
 node(c,n){const {x,y}=n;if(n.type==='gold'){this.ellipse(c,x,y+8,48,24,'#263c2a55');c.fillStyle='#6d7562';c.beginPath();c.moveTo(x-38,y+7);c.lineTo(x-29,y-33);c.lineTo(x+10,y-57);c.lineTo(x+41,y-17);c.lineTo(x+34,y+13);c.closePath();c.fill();c.fillStyle='#d9b66d';for(const [dx,dy]of [[-13,-15],[12,-32],[25,-8]]){c.beginPath();c.moveTo(x+dx,y+dy-9);c.lineTo(x+dx+7,y+dy);c.lineTo(x+dx,y+dy+6);c.lineTo(x+dx-6,y+dy);c.closePath();c.fill();}c.fillStyle='#273829';c.fillRect(x-17,y-2,31,22);c.strokeStyle='#b59d70';c.lineWidth=5;c.strokeRect(x-21,y-6,39,28);}else{for(let j=0;j<4;j++){c.fillStyle='#8a6b43';c.fillRect(x-33+j*13,y-17-j*3,13,33);this.ellipse(c,x-27+j*13,y+16-j*3,6,4,'#c7aa73');}c.strokeStyle='#443e2c';c.lineWidth=2;c.beginPath();c.moveTo(x-33,y+2);c.lineTo(x+22,y-10);c.stroke();}
  c.fillStyle='#d9dbad';c.font='9px Manrope, sans-serif';c.textAlign='center';c.fillText(n.type==='gold'?'ШАХТА РЁ':'ЛЕСОПИЛКА',x,y+40);
 }
 draw(selection=[],placement=null,mouse=null,drag=null,attackMove=false){const c=this.ctx,{x,y,zoom}=this.camera,w=this.width,h=this.height,time=this.game.time;c.setTransform(this.dpr,0,0,this.dpr,0,0);c.fillStyle='#263d2c';c.fillRect(0,0,w,h);c.save();c.translate(w/2-x*zoom,h/2-y*zoom);c.scale(zoom,zoom);c.drawImage(this.terrain,0,0);
  const seen=(e)=>e.x>x-w/zoom/2-120&&e.x<x+w/zoom/2+120&&e.y>y-h/zoom/2-130&&e.y<y+h/zoom/2+160;
  const drawables=[...this.decor.filter(seen).map(t=>({y:t.y,draw:()=>t.kind==='tree'?this.tree(c,t):this.rock(c,t)})),...this.game.nodes.filter(seen).map(n=>({y:n.y,draw:()=>this.node(c,n)})),...this.game.entities.filter(e=>e.alive&&seen(e)).map(e=>({y:e.y,draw:()=>e.kind==='building'?this.building(c,e,selection.includes(e.id)):this.ninja(c,e,selection.includes(e.id),time)}))].sort((a,b)=>a.y-b.y);for(const d of drawables)d.draw();
  for(const f of this.game.effects){const p=1-f.life/f.total;c.save();c.globalAlpha=Math.min(1,f.life*3);if(f.type==='projectile'){const px=f.x+(f.tx-f.x)*p,py=f.y+(f.ty-f.y)*p;c.strokeStyle=f.team?'#dfb57c':'#d6e4b2';c.lineWidth=2;c.beginPath();c.moveTo(px,py);c.lineTo(px-(f.tx-f.x)*.1,py-(f.ty-f.y)*.1);c.stroke();}else if(f.type==='blast'){c.strokeStyle=f.color;c.lineWidth=6*(1-p)+1;c.beginPath();c.ellipse(f.x,f.y-10,(f.radius||100)*p,(f.radius||100)*p*.63,0,0,Math.PI*2);c.stroke();for(let k=0;k<8;k++){const a=k*Math.PI/4+time*2;this.ellipse(c,f.x+Math.cos(a)*(f.radius||100)*p,f.y+Math.sin(a)*(f.radius||100)*p*.63-15,5,5,f.color);}}else if(f.type==='heal'){c.fillStyle='#c3e4b0';c.fillRect(f.x-6,f.y-30-p*28,12,3);c.fillRect(f.x-1.5,f.y-34-p*28,3,12);}else if(f.type==='death'){for(let k=0;k<5;k++)this.ellipse(c,f.x+Math.cos(k*1.3)*p*22,f.y-15-p*25+Math.sin(k*2)*7,8+p*9,6+p*7,'#d2d5bd');}else if(f.type==='level'){c.strokeStyle='#e7cf8a';c.lineWidth=2;c.beginPath();c.ellipse(f.x,f.y-12,35*p,55*p,0,0,Math.PI*2);c.stroke();}else if(f.type==='order'){c.strokeStyle=attackMove?'#e6a27f':'#dce9aa';c.lineWidth=2;c.beginPath();c.ellipse(f.x,f.y,12+20*p,6+10*p,0,0,Math.PI*2);c.stroke();}c.restore();}
  if(placement&&mouse){const valid=this.game.validPlacement(placement,mouse.x,mouse.y);c.save();c.globalAlpha=.7;this.building(c,{x:mouse.x,y:mouse.y,type:placement,team:0,progress:1,hp:1,maxHP:1},true,true);c.strokeStyle=valid?'#c4e69a':'#f48b78';c.lineWidth=3;c.setLineDash([6,6]);c.beginPath();c.ellipse(mouse.x,mouse.y+10,BUILDINGS[placement].size+20,(BUILDINGS[placement].size+20)*.65,0,0,Math.PI*2);c.stroke();c.restore();}
  c.restore();const vignette=c.createRadialGradient(w*.6,h*.45,h*.2,w*.5,h*.5,w*.75);vignette.addColorStop(0,'#102c1d00');vignette.addColorStop(1,'#07171088');c.fillStyle=vignette;c.fillRect(0,0,w,h);
  if(drag&&drag.active){c.fillStyle='#d7e9a815';c.strokeStyle='#d3e9ab';c.lineWidth=1;c.fillRect(drag.x,drag.y,drag.tx-drag.x,drag.ty-drag.y);c.strokeRect(drag.x,drag.y,drag.tx-drag.x,drag.ty-drag.y);}
 }
 minimap(canvas){const c=canvas.getContext('2d'),w=canvas.width,h=canvas.height;c.clearRect(0,0,w,h);c.drawImage(this.terrain,0,0,w,h);c.fillStyle='#14302055';c.fillRect(0,0,w,h);for(const e of this.game.entities){c.fillStyle=e.team?'#e0a87d':'#d0e0a2';const s=e.kind==='building'?5:e.type==='hero'?4:2;c.fillRect(e.x/WORLD.w*w-s/2,e.y/WORLD.h*h-s/2,s,s);}const {x,y,zoom}=this.camera;c.strokeStyle='#f7ecc9bb';c.lineWidth=1;c.strokeRect((x-this.width/zoom/2)/WORLD.w*w,(y-this.height/zoom/2)/WORLD.h*h,this.width/zoom/WORLD.w*w,this.height/zoom/WORLD.h*h);}
}
