import {byId} from './roster.js';
export function ninja(c,id,x,y,scale=1,pose='idle',time=0,face=1,extra={}){
 const d=byId(id),swing=pose==='attack'||pose==='heavy',cast=pose==='cast'||pose==='rush',walk=pose==='walk',jump=pose==='jump',guard=pose==='guard',hit=pose==='hit',t=extra.anim||0,phase=Math.sin(time*11),bob=walk?Math.abs(phase)*3:Math.sin(time*2.3)*1.5;
 c.save();c.translate(x,y-bob);c.scale(scale*face,scale);c.lineJoin='round';c.lineCap='round';
 const outline='#212737',skin='#efc3a0',shade='#c28e78',color=d.color;
 const polygon=(points,fill,stroke=outline,width=2)=>{c.beginPath();points.forEach(([x,y],i)=>i?c.lineTo(x,y):c.moveTo(x,y));c.closePath();c.fillStyle=fill;c.fill();if(stroke){c.strokeStyle=stroke;c.lineWidth=width;c.stroke();}};
 const oval=(x,y,rx,ry,fill,stroke=false)=>{c.beginPath();c.ellipse(x,y,rx,ry,0,0,Math.PI*2);c.fillStyle=fill;c.fill();if(stroke){c.strokeStyle=outline;c.lineWidth=1.6;c.stroke();}};
 const bone=(x1,y1,x2,y2,w,col)=>{c.strokeStyle=outline;c.lineWidth=w+3;c.beginPath();c.moveTo(x1,y1);c.lineTo(x2,y2);c.stroke();c.strokeStyle=col;c.lineWidth=w;c.stroke();};
 // Long hair, gourds, scrolls and signature tools behind the body.
 if(['neji','hinata','itachi','orochimaru','jiraiya'].includes(id))polygon([[-20,-159],[-29,-112],[-37,-77],[-14,-97],[16,-103],[25,-144]],d.hair);
 if(id==='gaara'){oval(-28,-96,23,36,'#b39a68',true);oval(-27,-129,15,20,'#c4ad7c',true);bone(-45,-110,-10,-91,4,'#68513f');bone(-44,-86,-10,-111,4,'#68513f');}
 if(id==='tenten')for(const yy of [-111,-82]){polygon([[-35,yy-11],[-32,yy+17],[-9,yy+13],[-12,yy-14]],'#d1c49e');bone(-33,yy-10,-12,yy-13,5,'#914d4e');}
 if(id==='kankuro'){polygon([[-34,-128],[-55,-101],[-45,-52],[-17,-65]],'#887655');bone(-48,-107,-35,-57,5,'#b69a6f');}
 if(id==='temari'){
  c.save();c.translate(-22,-96);c.rotate((cast||swing?-.65:-.3));polygon([[0,43],[-73,-84],[58,-97],[27,43]],'#ddd3ba');for(let k=0;k<6;k++)bone(8,41,-65+k*24,-84-Math.sin(k)*8,1,'#938777');for(const [px,py]of [[-42,-54],[-5,-68],[31,-60]])oval(px,py,11,14,'#78608e');c.restore();
 }
 const kick=swing&&['kick','claw'].includes(d.style),stride=walk?phase*22:0;
 let kneeL=[-18-stride,-35],footL=[-27-stride,0],kneeR=[21+stride,-34],footR=[35+stride,0];
 if(jump){kneeL=[-34,-47];footL=[-16,-25];kneeR=[28,-24];footR=[45,-40];}
 if(kick){kneeR=[54,-84];footR=[103,-104];}
 const pants=id==='lee'?'#51785d':id==='sasuke'?'#d6d9d7':id==='naruto'?'#d98637':id==='neji'?'#aca797':id==='hinata'?'#626b92':'#424657';
 bone(-12,-75,...kneeL,18,pants);bone(...kneeL,...footL,15,pants);bone(13,-75,...kneeR,18,pants);bone(...kneeR,...footR,15,pants);
 if(id==='lee'){bone(kneeL[0],kneeL[1]+6,footL[0],footL[1]-8,18,'#d1945b');bone(kneeR[0],kneeR[1]+6,footR[0],footR[1]-8,18,'#d1945b');}
 for(const foot of [footL,footR]){bone(foot[0]-5,foot[1],foot[0]+10,foot[1],9,'#313b4a');bone(foot[0]+4,foot[1]-2,foot[0]+9,foot[1]-2,3,skin);}
 let torso=[[-22,-126],[20,-128],[25,-78],[9,-69],[-25,-76]];
 if(id==='itachi')torso=[[-30,-132],[26,-131],[35,-49],[-34,-50]];
 polygon(torso,color);polygon([[6,-126],[20,-128],[25,-78],[9,-69]],'#151a3029',null);
 if(['kakashi','shikamaru'].includes(id)){polygon([[-21,-124],[21,-123],[21,-81],[-22,-81]],'#6e815c');for(const xx of [-14,6]){polygon([[xx,-115],[xx+10,-115],[xx+10,-97],[xx,-97]],'#8a9a70');}}
 if(id==='naruto'){polygon([[-23,-125],[-8,-127],[-8,-106],[-22,-99]],'#343c46');bone(0,-124,0,-77,2,'#dbceac');oval(10,-106,7,7,'#cfbba1');}
 if(id==='sakura')bone(0,-123,0,-78,2,'#ead3c6');
 if(id==='sasuke'){bone(-24,-77,24,-77,8,'#a9a0b1');oval(24,-76,9,7,'#b8aabb',true);}
 if(id==='itachi'){for(const [xx,yy]of [[-10,-105],[14,-67]]){oval(xx,yy,12,7,'#ac4356',true);oval(xx+6,yy-4,8,6,'#ac4356');}polygon([[-10,-133],[7,-135],[19,-113],[-2,-113]],'#4d3b4c');}
 if(id==='orochimaru'){bone(-26,-81,24,-81,7,'#9e7eae');oval(-3,-78,10,7,'#aa90bd');}
 if(id==='jiraiya'){polygon([[-24,-127],[-13,-127],[-13,-78],[-32,-62]],'#a65e55');polygon([[15,-127],[25,-126],[34,-64],[16,-78]],'#a65e55');}
 // Arms use distinct attack silhouettes: palm, kick, sword, fan and fist.
 const arm=guard?[[24,-139],[37,-114]]:swing&&!kick?[[54,-119],[92,-115]]:cast?[[40,-114],[62,-128]]:[[33,-104+(walk?stride*.2:0)],[29,-84+(walk?stride*.3:0)]];
 bone(-18,-121,-34,-99-(guard?15:0),14,color);bone(-34,-99-(guard?15:0),-25,-78-(guard?38:0),11,skin);
 bone(19,-122,...arm[0],14,color);bone(...arm[0],...arm[1],11,skin);
 if(id==='lee'){bone(arm[0][0],arm[0][1],arm[1][0],arm[1][1],11,'#d8d2b9');for(let n=0;n<4;n++)bone(arm[1][0]-7,arm[1][1]+n*3-5,arm[1][0]+3,arm[1][1]+n*3-5,1,'#a8ac9b');}
 oval(arm[1][0]+2,arm[1][1]-1,7,6,skin,true);
 if(d.style==='sword'&&(swing||cast)){bone(arm[1][0],arm[1][1],arm[1][0]+56,arm[1][1]-67,5,'#cad9e3');bone(arm[1][0]-7,arm[1][1]-3,arm[1][0]+9,arm[1][1]+7,3,'#8a889c');}
 if(['weapon','tactical','crow'].includes(d.style)&&swing)polygon([[92,-115],[110,-135],[114,-129],[102,-111]],'#dce1df');
 if(['palm'].includes(d.style)&&swing){bone(91,-118,100,-128,4,skin);bone(95,-117,105,-124,3,skin);}
 // Head, ears, shaded jaw and readable anime eyes.
 bone(-2,-133,-2,-142,13,skin);oval(-2,-160,22,25,skin,true);polygon([[8,-178],[19,-166],[18,-148],[4,-137],[-2,-137],[8,-152]],shade,null);
 oval(-23,-158,4,7,skin,true);
 if(id==='lee')polygon([[-25,-161],[-24,-179],[-12,-189],[10,-189],[21,-177],[21,-163],[13,-167],[-15,-167]],d.hair);
 else if(['neji','hinata','itachi','orochimaru'].includes(id))polygon([[-24,-160],[-26,-178],[-15,-190],[10,-191],[23,-178],[24,-143],[15,-153],[9,-175],[-3,-181],[-10,-164]],d.hair);
 else if(id==='tenten'){oval(-20,-183,12,11,d.hair,true);oval(17,-183,12,11,d.hair,true);polygon([[-23,-161],[-25,-174],[-12,-187],[10,-186],[23,-174],[20,-160],[9,-175],[-5,-173]],d.hair);}
 else if(id==='temari'){for(const [xx,yy]of [[-24,-182],[23,-183],[-28,-160],[27,-160]])polygon([[xx,yy],[xx-13,yy-14],[xx+4,yy-20],[xx+8,yy+5]],d.hair);polygon([[-22,-162],[-25,-178],[-8,-193],[10,-187],[24,-178],[20,-159],[10,-178],[-5,-172]],d.hair);}
 else if(id==='shikamaru'){polygon([[-15,-181],[-29,-218],[-10,-209],[0,-225],[10,-210],[24,-212],[18,-181]],d.hair);oval(-2,-174,24,17,d.hair,true);}
 else if(id==='kankuro'){polygon([[-27,-150],[-30,-185],[-17,-200],[-8,-190],[13,-195],[27,-184],[25,-148],[16,-164],[11,-182],[-17,-181],[-18,-154]],d.hair);}
 else{polygon([[-25,-163],[-32,-178],[-20,-178],[-23,-194],[-9,-188],[-7,-205],[4,-192],[17,-202],[15,-184],[30,-189],[24,-174],[31,-172],[19,-160],[10,-177],[-2,-171],[-15,-174]],d.hair);}
 if(id==='sakura'){polygon([[-25,-162],[-28,-140],[-20,-137],[-17,-161]],d.hair);}
 if(id!=='gaara'&&id!=='jiraiya'){bone(-22,-171,19,-171,6,'#394152');polygon([[-15,-175],[12,-175],[12,-168],[-15,-168]],'#bec9cf',outline,1);c.strokeStyle='#657481';c.lineWidth=1;c.beginPath();c.arc(-3,-171,2,0,5);c.stroke();}
 if(id==='jiraiya'){polygon([[-21,-178],[17,-178],[17,-165],[-21,-165]],'#b8bfba');c.fillStyle='#5e665f';c.font='10px serif';c.fillText('油',-11,-168);}
 const eye=['hinata','neji'].includes(id)?'#e0d9ee':id==='sasuke'||id==='itachi'?'#a94c5e':id==='naruto'?'#6eacbf':'#505367';
 polygon([[-14,-160],[-5,-158],[-9,-154],[-15,-155]],'#f4e9d9',outline,1);polygon([[3,-158],[14,-161],[15,-156],[7,-153]],'#f4e9d9',outline,1);oval(-10,-157,2,2.4,eye);oval(10,-157,2,2.5,eye);bone(-15,-164,-5,-162,1.7,d.hair);bone(4,-162,15,-165,1.7,d.hair);
 if(id==='kakashi'){polygon([[-21,-153],[17,-152],[10,-139],[-4,-134],[-20,-142]],'#394554');bone(-17,-174,2,-174,7,'#bdc7ca');}
 else{bone(3,-146,10,-147,1,'#915e59');}
 if(id==='naruto')for(const [xx,yy]of [[-17,-149],[-17,-145],[12,-149],[12,-145]])bone(xx,yy,xx+4,yy,1,'#a77764');
 if(id==='kiba'){polygon([[-15,-151],[-9,-147],[-13,-139]],'#b95650',null);polygon([[11,-151],[17,-149],[13,-140]],'#b95650',null);}
 if(id==='jiraiya')for(const xx of [-12,12])bone(xx,-154,xx,-140,3,'#ab5f58');
 if(id==='kankuro'){bone(-11,-152,-3,-148,3,'#8970a6');bone(4,-150,12,-146,3,'#8970a6');}
 if(id==='gaara'){c.fillStyle='#8e443b';c.font='10px serif';c.fillText('愛',6,-179);}
 if(cast){c.shadowBlur=18;c.shadowColor=extra.color||'#a4ddf1';oval(64,-126,13+Math.sin(time*25)*2,13,extra.color||'#a4ddf1');c.shadowBlur=0;}
 if(extra.buff){c.strokeStyle=extra.buff.color+'88';c.lineWidth=2;for(let k=0;k<3;k++){c.beginPath();c.arc(0,-99,62+k*15,time*3+k,time*3+k+1.5);c.stroke();}}
 if(hit){c.globalAlpha=.22;polygon([[-24,-193],[23,-190],[30,-70],[-25,-70]],'#fff',null);}
 c.restore();
}
export class Art{
 constructor(canvas){this.c=canvas.getContext('2d');this.canvas=canvas;this.background=document.createElement('canvas');this.background.width=1280;this.background.height=720;this.landscape();}
 landscape(){const c=this.background.getContext('2d');const sky=c.createLinearGradient(0,0,0,550);sky.addColorStop(0,'#3c556e');sky.addColorStop(.5,'#99a9a7');sky.addColorStop(1,'#e3c8a0');c.fillStyle=sky;c.fillRect(0,0,1280,720);
  const sun=c.createRadialGradient(920,130,5,920,130,210);sun.addColorStop(0,'#ffe2a8bb');sun.addColorStop(1,'#ffe2a800');c.fillStyle=sun;c.fillRect(650,0,560,430);c.fillStyle='#f5ddad';c.beginPath();c.arc(920,135,47,0,Math.PI*2);c.fill();
  const poly=(p,col)=>{c.beginPath();p.forEach(([x,y],i)=>i?c.lineTo(x,y):c.moveTo(x,y));c.closePath();c.fillStyle=col;c.fill();};
  poly([[0,240],[85,170],[210,194],[340,106],[470,185],[610,119],[810,200],[980,169],[1180,241],[1280,180],[1280,510],[0,510]],'#67797f');
  poly([[0,340],[90,270],[180,286],[300,228],[520,253],[660,228],[810,266],[970,242],[1100,285],[1280,245],[1280,520],[0,520]],'#8c9790');
  // Four carved silhouettes on the village cliff.
  c.fillStyle='#b4b19a';c.fillRect(330,215,510,108);for(let k=0;k<4;k++){const x=390+k*115;c.fillStyle='#aaa997';c.beginPath();c.ellipse(x,238,34,43,0,0,Math.PI*2);c.fill();c.strokeStyle='#7b877f';c.lineWidth=3;c.beginPath();c.moveTo(x-21,220);c.lineTo(x-6,223);c.moveTo(x+4,223);c.lineTo(x+21,220);c.moveTo(x-4,230);c.lineTo(x-9,245);c.lineTo(x+3,246);c.moveTo(x-11,258);c.lineTo(x+12,258);c.stroke();c.fillStyle='#909b90';c.fillRect(x-32,204,64,8);}
  poly([[0,373],[100,321],[220,351],[330,309],[440,352],[580,304],[720,346],[830,305],[1000,340],[1150,308],[1280,357],[1280,560],[0,560]],'#657d6e');
  for(let k=0;k<18;k++){const x=k*84-30,y=340+(k%3)*20,w=60+(k%4)*15;c.fillStyle='#9da18b';c.fillRect(x,y,w,110);poly([[x-13,y],[x+w/2,y-30],[x+w+13,y],[x+w,y+8],[x,y+8]],k%2?'#846e65':'#927c68');c.fillStyle='#64766c';for(let j=0;j<3;j++)c.fillRect(x+9+j*18,y+28,9,17);}
  const tree=(x,y,s)=>{c.fillStyle='#4d5e50';c.fillRect(x-s*.1,y-s*.6,s*.2,s);for(let k=0;k<5;k++){c.fillStyle=['#445f52','#54745c','#648268'][k%3];c.beginPath();c.ellipse(x+Math.sin(k*2)*s*.5,y-s*.65-Math.cos(k*2)*s*.3,s*.65,s*.45,0,0,Math.PI*2);c.fill();}};
  for(let k=0;k<11;k++){tree(k*125-20,450+(k%3)*7,64+(k%4)*7);}tree(37,455,140);tree(1235,460,140);
  c.fillStyle='#9d9c7c';c.fillRect(0,480,1280,80);c.fillStyle='#c1b28c';c.fillRect(0,488,1280,12);c.fillStyle='#65765e';for(let k=0;k<22;k++){c.fillRect(k*64,500,3,52);c.fillRect(k*64,538,64,3);}
  // Training arena: warm stone planes, painted concentric combat seals.
  const floor=c.createLinearGradient(0,545,0,720);floor.addColorStop(0,'#b7b197');floor.addColorStop(1,'#777b70');c.fillStyle=floor;c.fillRect(0,550,1280,170);
  c.strokeStyle='#5d6e6640';c.lineWidth=1;for(let y=557;y<720;y+=26){c.beginPath();c.moveTo(0,y);c.lineTo(1280,y);c.stroke();}for(let x=-500;x<1900;x+=120){c.beginPath();c.moveTo(640+(x-640)*.6,550);c.lineTo(x,720);c.stroke();}
  c.strokeStyle='#ded3ae55';c.lineWidth=3;for(const r of [150,170,260]){c.beginPath();c.ellipse(640,590,r,r*.16,0,0,Math.PI*2);c.stroke();}
  c.fillStyle='#d3c9a465';c.font='56px serif';c.textAlign='center';c.fillText('忍',640,601);
  for(const [x,y]of [[115,510],[1145,510]]){c.fillStyle='#5e6257';c.fillRect(x-7,y-145,14,145);c.fillStyle='#a88b71';c.fillRect(x-14,y-140,28,24);c.fillStyle='#8b514f';c.fillRect(x-36,y-135,73,9);c.fillStyle='#dab67c';c.fillRect(x-13,y-122,29,46);c.fillStyle='#785943';c.fillRect(x-16,y-77,35,6);c.fillStyle='#5c5d50';c.font='22px serif';c.fillText('火',x+1,y-92);}
 }
 draw(fight,realTime){const c=this.c;c.clearRect(0,0,1280,720);c.drawImage(this.background,0,0);const time=fight?.time||realTime;
  // Continuous drifting leaves, independent of combat objects.
  for(let k=0;k<18;k++){const x=(k*151+realTime*(12+k%5))%1360-40,y=180+(k*73)%350+Math.sin(realTime+k)*20;c.save();c.translate(x,y);c.rotate(realTime+k);c.fillStyle=k%2?'#d6c68a88':'#b8ce9d66';c.beginPath();c.ellipse(0,0,6,2,0,0,Math.PI*2);c.fill();c.restore();}
  if(!fight)return;
  for(const f of fight.fighters){c.fillStyle='#263a414a';c.beginPath();c.ellipse(f.x,555,48,9,0,0,Math.PI*2);c.fill();}
  for(const t of fight.traps){c.save();c.translate(t.x,548);c.fillStyle='#e1ceaa';c.fillRect(-20,-8,40,7);c.strokeStyle=t.color;c.lineWidth=2;c.strokeRect(-17,-14,34,12);c.fillStyle='#715d52';c.font='12px serif';c.textAlign='center';c.fillText('爆',0,-4);c.restore();}
  for(const s of fight.summons){c.save();c.globalAlpha=Math.min(1,s.life);if(s.pet==='clone')ninja(c,fight.fighters[s.owner].id,s.x,550,.8,'walk',time,s.facing,{anim:time});else this.pet(c,s,time);c.restore();}
  for(const f of fight.fighters)ninja(c,f.id,f.x,f.y,1,f.state,time,f.facing,{buff:f.buff,anim:f.stateTime,color:byId(f.id).skills.find(s=>s.name===f.moveName)?.color});
  for(const p of fight.shots){if(p.delay>0)continue;c.save();c.translate(p.x,p.y);c.shadowColor=p.color;c.shadowBlur=20;if(p.style==='fan'){c.strokeStyle=p.color;c.lineWidth=5;for(let k=0;k<3;k++){c.beginPath();c.arc(0,0,p.r+k*8,Math.PI*.65,Math.PI*1.5);c.stroke();}}else if(p.r<20){c.rotate(time*17);c.fillStyle=p.color;for(let k=0;k<4;k++){c.rotate(Math.PI/2);c.beginPath();c.moveTo(0,0);c.lineTo(-5,-p.r);c.lineTo(5,-p.r*.65);c.closePath();c.fill();}}else{const g=c.createRadialGradient(0,0,2,0,0,p.r);g.addColorStop(0,'#fff4d7');g.addColorStop(.35,p.color);g.addColorStop(1,p.color+'00');c.fillStyle=g;c.beginPath();c.arc(0,0,p.r,0,Math.PI*2);c.fill();c.strokeStyle=p.color;c.lineWidth=3;c.beginPath();c.moveTo(-Math.sign(p.v)*p.r,0);c.lineTo(-Math.sign(p.v)*(p.r+55),Math.sin(time*25)*7);c.stroke();}c.restore();}
  for(const f of fight.effects){const p=1-f.life/f.total;c.save();c.translate(f.x,f.y);c.globalAlpha=Math.min(1,f.life*5);c.strokeStyle=f.color||'#ffe4b7';c.fillStyle=f.color||'#ffe4b7';c.lineWidth=3;
   if(f.type==='hit'||f.type==='guard'){for(let k=0;k<8;k++){const a=k*Math.PI/4;c.beginPath();c.moveTo(Math.cos(a)*8,Math.sin(a)*8);c.lineTo(Math.cos(a)*(12+p*45),Math.sin(a)*(12+p*45));c.stroke();}if(f.type==='guard'){c.beginPath();c.arc(0,0,25+p*15,0,Math.PI*2);c.stroke();}}
   else if(f.type==='slash'){c.scale(f.face||1,1);c.lineWidth=2+(1-p)*3;c.beginPath();c.arc(-30,0,40+p*30,-1.2,1.1);c.stroke();if(f.style==='sand'||f.style==='puppet'){for(let k=0;k<8;k++)c.fillRect(k*9-30,p*25-20+Math.sin(k)*12,4,4);}}
   else if(f.type==='shadow'){c.fillStyle='#202b3cb8';c.beginPath();c.ellipse((f.tx-f.x)/2,0,Math.abs(f.tx-f.x)/2,9+Math.sin(time*20)*2,0,0,Math.PI*2);c.fill();for(let k=0;k<4;k++){c.beginPath();c.moveTo(f.tx-f.x,0);c.quadraticCurveTo(f.tx-f.x-40+k*20,-90,f.tx-f.x+(k-2)*20,-160+p*20);c.stroke();}}
   else if(f.type==='ring'){for(let k=0;k<3;k++){c.beginPath();c.ellipse(0,30,(f.radius||120)*p,(f.radius||120)*p*.35+k*13,0,0,Math.PI*2);c.stroke();}for(let k=0;k<12;k++){const a=k*Math.PI/6;c.fillRect(Math.cos(a)*(f.radius||120)*p,Math.sin(a)*50*p,3,14*(1-p));}}
   else if(f.type==='heal'){for(let k=0;k<5;k++){const x=Math.sin(k*4)*35,y=-p*100+k*13;c.fillRect(x-7,y,14,3);c.fillRect(x-1.5,y-5,3,13);}}
   else if(f.type==='fall'){for(let k=0;k<3;k++){c.beginPath();c.moveTo((k-1)*25,-100+p*120);c.lineTo((k-1)*25-20,100+p*170);c.stroke();}}
   else if(f.type==='palm'){c.beginPath();c.arc(0,0,20+p*45,0,Math.PI*2);c.stroke();}
   else if(f.type==='smoke'){for(let k=0;k<6;k++){c.beginPath();c.ellipse(Math.sin(k*3)*p*45,-p*50+k*7,15+p*15,18+p*12,0,0,Math.PI*2);c.fill();}}
   else{for(let k=0;k<3;k++){c.beginPath();c.ellipse(0,0,35+p*80+k*12,65+p*50,0,time*3+k,time*3+k+3);c.stroke();}}
   c.restore();}
  const vig=c.createRadialGradient(640,340,200,640,360,800);vig.addColorStop(0,'#151d3000');vig.addColorStop(1,'#101a3b88');c.fillStyle=vig;c.fillRect(0,0,1280,720);
 }
 pet(c,s,time){c.save();c.translate(s.x,550);c.scale(s.facing||1,1);const oval=(x,y,rx,ry,col)=>{c.fillStyle=col;c.beginPath();c.ellipse(x,y,rx,ry,0,0,Math.PI*2);c.fill();};
  if(s.pet==='dog'){oval(0,-25,30,15,'#e1dfc9');oval(27,-39,14,13,'#e5e5ce');c.strokeStyle='#dedcc5';c.lineWidth=8;for(const xx of [-18,15]){c.beginPath();c.moveTo(xx,-22);c.lineTo(xx+Math.sin(time*18+xx)*8,-3);c.stroke();}c.beginPath();c.moveTo(-26,-29);c.quadraticCurveTo(-55,-62,-41,-67);c.stroke();c.fillStyle='#505866';c.fillRect(26,-45,13,4);c.fillRect(35,-37,4,3);}
  else if(s.pet==='crow'){c.translate(0,-100+Math.sin(time*4)*20);c.fillStyle='#303248';c.beginPath();c.moveTo(-8,0);c.lineTo(-45,-20+Math.sin(time*22)*25);c.lineTo(-15,-3);c.lineTo(3,-15);c.lineTo(11,-3);c.lineTo(40,-30+Math.sin(time*22)*25);c.lineTo(16,5);c.lineTo(-2,9);c.closePath();c.fill();}
  else if(s.pet==='frog'){oval(0,-28,38,25,'#9cab73');oval(26,-15,22,12,'#aab483');oval(-26,-15,22,12,'#aab483');for(const xx of [-18,18]){oval(xx,-54,13,12,'#c3ce9b');oval(xx,-54,5,8,'#3b4d4b');}}
  else{c.strokeStyle='#d8d5d35c';c.lineWidth=1;c.beginPath();c.moveTo(-70,-130);c.lineTo(-15,-60);c.moveTo(-60,-125);c.lineTo(15,-60);c.stroke();c.fillStyle='#977e59';c.fillRect(-17,-68,34,46);oval(0,-83,20,16,'#b49a70');c.strokeStyle='#5b5052';c.lineWidth=6;for(const v of [-1,1]){c.beginPath();c.moveTo(v*15,-57);c.lineTo(v*40,-33);c.lineTo(v*46,-65);c.moveTo(v*10,-25);c.lineTo(v*24,-4);c.stroke();}c.fillStyle='#75536a';c.fillRect(-12,-87,8,4);c.fillRect(5,-87,8,4);}
 c.restore();}
}
