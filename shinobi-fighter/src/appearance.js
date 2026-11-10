// First outfit pass from the16 user-supplied reference images (11 November).
// Procedural, articulated costume details; no edited/cropped reference pictures.
export const LOOKS={
 naruto:{top:'#ec9638',pants:'#e79135',hair:'#f1ce38',shoe:'#163c52',skin:'#eec49e'},
 sasuke:{top:'#173b70',pants:'#e4e3db',hair:'#202c3c',shoe:'#153756',skin:'#eed0b6',shortSleeve:true},
 sakura:{top:'#a22c4e',pants:'#25434a',hair:'#e79dae',shoe:'#173c5e',skin:'#f0cab7',sleeveless:true},
 kiba:{top:'#9a9e93',pants:'#64634d',hair:'#343b30',shoe:'#214453',skin:'#ddbf9d'},
 shikamaru:{top:'#a7aaa2',pants:'#57514b',hair:'#303730',shoe:'#234a68',skin:'#e8c5a8',shortSleeve:true},
 hinata:{top:'#d3c7bd',pants:'#444d6a',hair:'#333852',shoe:'#153953',skin:'#f0d2ba'},
 neji:{top:'#c9bea3',pants:'#56564d',hair:'#4b4635',shoe:'#17414c',skin:'#e7cfb3',shortSleeve:true},
 tenten:{top:'#dfb2c0',pants:'#25403d',hair:'#4a332b',shoe:'#173a53',skin:'#e7c6ad',sleeveless:true},
 kankuro:{top:'#343827',pants:'#343827',hair:'#2f3525',shoe:'#343b2b',skin:'#d7bc8e'},
 lee:{top:'#256e59',pants:'#256e59',hair:'#22372e',shoe:'#1c3a46',skin:'#e3c49a'},
 kakashi:{top:'#6c7d5d',pants:'#303b4e',hair:'#c2c9ca',shoe:'#263843',skin:'#e1c3ab'},
 orochimaru:{top:'#c5bf9d',pants:'#5b6251',hair:'#23252c',shoe:'#444d33',skin:'#e6d9c2'},
 jiraiya:{top:'#7e8163',pants:'#787c5c',hair:'#dedfd4',shoe:'#9a4d3d',skin:'#dab18b'},
 itachi:{top:'#292e3b',pants:'#313746',hair:'#242831',shoe:'#2d3541',skin:'#dec5b0'},
 gaara:{top:'#44362f',pants:'#3c342e',hair:'#863d3a',shoe:'#303536',skin:'#e5c7ae',shortSleeve:true},
 temari:{top:'#cfc0ca',pants:'#cfb7ac',hair:'#dcc76a',shoe:'#29353e',skin:'#edd0b7',shortSleeve:true}
};
function polygon(c,p,fill,stroke='#29313c',width=1.4){c.beginPath();p.forEach(([x,y],i)=>i?c.lineTo(x,y):c.moveTo(x,y));c.closePath();c.fillStyle=fill;c.fill();if(stroke){c.strokeStyle=stroke;c.lineWidth=width;c.stroke();}}
function ellipse(c,x,y,rx,ry,fill){c.beginPath();c.ellipse(x,y,rx,ry,0,0,Math.PI*2);c.fillStyle=fill;c.fill();}
function segment(c,a,b,width,color){c.strokeStyle='#29313c';c.lineWidth=width+2;c.lineCap='round';c.beginPath();c.moveTo(...a);c.lineTo(...b);c.stroke();c.strokeStyle=color;c.lineWidth=width;c.stroke();}
function mesh(c,p,base='#939b8d'){c.save();polygon(c,p,base,null);c.clip();c.strokeStyle='#3f4848a8';c.lineWidth=.7;for(let k=-180;k<180;k+=8){c.beginPath();c.moveTo(k,-180);c.lineTo(k+180,0);c.moveTo(k,-180);c.lineTo(k-180,0);c.stroke();}c.restore();}
function fur(c,a,b,color='#eeeae1',size=5){const dx=b[0]-a[0],dy=b[1]-a[1],l=Math.hypot(dx,dy)||1;c.strokeStyle=color;c.lineWidth=5;c.beginPath();c.moveTo(...a);c.lineTo(...b);c.stroke();for(let t=0;t<=1;t+=.09){const x=a[0]+dx*t,y=a[1]+dy*t;c.strokeStyle=t% .18<.08?color:'#bfc0b4';c.lineWidth=2;c.beginPath();c.moveTo(x-dy/l*size,y+dx/l*size);c.lineTo(x+dy/l*size*.6+dx/l*3,y-dx/l*size*.6+dy/l*3);c.stroke();}}
function wrap(c,a,b,width=15,color='#dadbd1'){segment(c,a,b,width,color);const dx=b[0]-a[0],dy=b[1]-a[1],l=Math.hypot(dx,dy)||1;c.strokeStyle='#7b8c8f88';c.lineWidth=.8;for(let t=.08;t<.96;t+=.17){const x=a[0]+dx*t,y=a[1]+dy*t;c.beginPath();c.moveTo(x-dy/l*width*.45,y+dx/l*width*.45);c.lineTo(x+dy/l*width*.45,y-dx/l*width*.45);c.stroke();}}
const lerp=(a,b,t)=>[a[0]+(b[0]-a[0])*t,a[1]+(b[1]-a[1])*t];
export function outfitBack(c,id,time){
 if(id==='sakura'){polygon(c,[[-20,-175],[-35,-148],[-39,-99],[-25,-112],[-28,-83],[-12,-101],[10,-93],[29,-108],[34,-135],[20,-179]],LOOKS[id].hair);}
 if(id==='jiraiya'){
  polygon(c,[[-20,-177],[-37,-191],[-37,-168],[-55,-149],[-46,-146],[-67,-109],[-52,-112],[-70,-65],[-54,-71],[-67,-36],[-24,-65],[24,-80],[31,-160]],'#dadfd8');
  polygon(c,[[-50,-103],[-38,-66],[14,-78],[5,-115]],'#858763');ellipse(c,-44,-84,12,24,'#a6a17b');ellipse(c,-43,-84,8,20,'#6a6d53');
 }
 if(id==='kankuro'){polygon(c,[[-26,-166],[-37,-145],[-39,-121],[-17,-130],[23,-126],[38,-147],[27,-167]],'#313624');}
}
export function outfitLegs(c,id,kneeL,footL,kneeR,footR){
 const l=LOOKS[id],calves=[[kneeL,footL],[kneeR,footR]];
 if(['sakura','temari'].includes(id)){for(let i=0;i<2;i++){const knee=calves[i][0],foot=calves[i][1],hip=[i?13:-13,-75];segment(c,lerp(hip,knee,.55),knee,16,l.skin);segment(c,knee,foot,14,l.skin);}if(id==='temari')mesh(c,[[-22,-70],[-3,-71],[-8,-36],[-25,-36]],'#b9a5a0');}
 if(['kiba','shikamaru','tenten','hinata'].includes(id))for(const [k,f]of calves)segment(c,lerp(k,f,.6),f,14,l.skin);
 if(id==='neji'){wrap(c,kneeL,lerp(kneeL,footL,.88),16);segment(c,kneeR,footR,14,l.skin);}
 if(id==='sasuke')for(const [k,f]of calves)wrap(c,lerp(k,f,.1),f,15,'#dcded8');
 if(['kakashi','itachi','orochimaru'].includes(id))for(const [k,f]of calves)wrap(c,lerp(k,f,.4),f,15);
 if(id==='jiraiya')for(const [k,f]of calves)mesh(c,[[k[0]-7,k[1]+4],[k[0]+7,k[1]+4],[f[0]+7,f[1]-5],[f[0]-7,f[1]-5]],'#8b9787');
 for(const [k,f]of calves){segment(c,lerp(k,f,.82),f,16,l.shoe);segment(c,[f[0]-5,f[1]],[f[0]+11,f[1]],9,l.shoe);segment(c,[f[0]+5,f[1]-1],[f[0]+11,f[1]-1],3,l.skin);}
 if(id==='jiraiya')for(const [,f]of calves){polygon(c,[[f[0]-9,f[1]+1],[f[0]+14,f[1]+1],[f[0]+14,f[1]+8],[f[0]-9,f[1]+8]],'#7e4032');}
}
export function outfitBody(c,id,time){
 const top=LOOKS[id].top;
 if(id==='naruto'){
  polygon(c,[[-23,-126],[-8,-128],[-8,-109],[-22,-105]],'#193d4c');polygon(c,[[6,-128],[21,-127],[23,-106],[8,-109]],'#193d4c');
  polygon(c,[[-19,-143],[19,-143],[20,-127],[-19,-126]],'#e7e5d2');for(let i=-15;i<18;i+=4)segment(c,[i,-141],[i+1,-128],.8,'#b8bdad');segment(c,[0,-126],[0,-76],2,'#e5d6b6');segment(c,[-24,-77],[24,-77],4,'#254151');
 }
 if(id==='sasuke'){polygon(c,[[-23,-148],[23,-150],[21,-125],[-17,-116]],'#1b4074');segment(c,[-24,-78],[24,-78],3,'#2c4053');for(let y=-56;y<=-40;y+=8)segment(c,[-24,y],[-10,y],4,y===-48?'#d5d4ca':'#383e42');}
 if(id==='sakura'){
  polygon(c,[[-24,-100],[25,-100],[31,-43],[4,-40],[-3,-54],[-24,-42]],top);segment(c,[0,-126],[1,-43],1.7,'#e4b0a8');
  c.strokeStyle='#ebe7d8';c.lineWidth=3;c.beginPath();c.ellipse(15,-66,9,12,0,-1,4);c.stroke();c.beginPath();c.ellipse(-18,-121,8,6,0,0,Math.PI*2);c.stroke();
 }
 if(id==='kiba'){polygon(c,[[-22,-132],[-15,-143],[16,-143],[23,-130],[13,-123],[-12,-124]],'#b4b8ab');fur(c,[-23,-130],[-10,-140],'#4a5041',4);fur(c,[11,-140],[23,-130],'#4a5041',4);segment(c,[0,-126],[0,-75],1.3,'#515c55');for(const x of [-18,7])polygon(c,[[x,-91],[x+10,-92],[x+10,-84],[x,-84]],'#a7ac9f');}
 if(id==='shikamaru'){
  mesh(c,[[-16,-127],[16,-127],[19,-78],[-19,-78]],'#9b9f8d');polygon(c,[[-23,-129],[-13,-127],[-16,-102],[-10,-86],[-27,-87]],top);polygon(c,[[15,-128],[23,-128],[26,-87],[11,-89],[15,-106]],top);segment(c,[-13,-128],[-17,-90],3,'#74866b');segment(c,[15,-128],[16,-90],3,'#74866b');segment(c,[-22,-78],[23,-78],4,'#4a4a43');
 }
 if(id==='hinata'){
  polygon(c,[[-24,-130],[-17,-144],[14,-144],[25,-131],[14,-119],[-12,-119]],'#cec3b8');segment(c,[0,-127],[0,-76],1.5,'#8d918a');fur(c,[-24,-76],[25,-76]);
  polygon(c,[[-16,-138],[16,-138],[15,-131],[-14,-131]],'#253d54');polygon(c,[[-10,-138],[10,-138],[10,-132],[-10,-132]],'#c1cbd0');for(const x of [-11,11]){segment(c,[x,-131],[x+3,-111],1,'#87867b');ellipse(c,x+3,-109,3,2,'#b4ae9f');}
 }
 if(id==='neji'){polygon(c,[[-18,-140],[17,-140],[20,-125],[-20,-125]],'#d6ccaf');segment(c,[-1,-133],[-1,-76],1,'#9e9c87');for(let y=-119;y<-82;y+=12){polygon(c,[[-7,y],[7,y],[7,y+3],[-7,y+3]],'#d8ceb5','#9e9c86',.8);}segment(c,[-23,-77],[24,-77],2,'#888d7d');}
 if(id==='tenten'){polygon(c,[[-11,-137],[10,-137],[14,-126],[-15,-126]],'#d39aa9');segment(c,[3,-133],[3,-76],1,'#a87f8e');for(let y=-123;y<-85;y+=13){segment(c,[-3,y],[9,y+1],2,'#955c74');ellipse(c,9,y+1,1.5,1.5,'#eee0d9');}}
 if(id==='kankuro'){polygon(c,[[-20,-135],[20,-136],[26,-114],[-24,-114]],'#343826');segment(c,[2,-118],[2,-78],1,'#49503b');}
 if(id==='kakashi'){polygon(c,[[-20,-131],[19,-132],[23,-80],[-23,-80]],'#697c5b');for(const x of [-17,4])for(const y of [-123,-107])polygon(c,[[x,y],[x+12,y],[x+12,y+13],[x,y+13]],'#7e8e69');segment(c,[0,-129],[0,-80],2,'#455d4d');segment(c,[-24,-78],[25,-78],3,'#343e47');}
 if(id==='orochimaru'){
  polygon(c,[[-22,-98],[23,-98],[30,-39],[4,-40],[0,-58],[-26,-39]],top);segment(c,[-18,-130],[-3,-108],3,'#384539');segment(c,[18,-130],[-3,-108],3,'#384539');
  for(let k=0;k<9;k++)ellipse(c,-24+k*6,-79+Math.sin(k*2)*2,5,5,'#a693ba');ellipse(c,3,-73,10,7,'#b2a0c2');
 }
 if(id==='jiraiya'){
  polygon(c,[[-26,-133],[-14,-131],[-13,-79],[-17,-29],[-39,-37]],'#a84b3b');polygon(c,[[16,-132],[27,-131],[41,-36],[19,-28],[15,-81]],'#a84b3b');ellipse(c,-22,-114,4,5,'#cdb573');ellipse(c,24,-114,4,5,'#cdb573');segment(c,[-14,-77],[14,-77],4,'#4e5c43');
 }
 if(id==='itachi'){
  polygon(c,[[-29,-130],[28,-130],[33,-19],[8,-11],[-6,-32],[-31,-18]],'#292f3c');polygon(c,[[-24,-147],[-4,-147],[4,-124],[-18,-124]],'#333b49');polygon(c,[[6,-147],[24,-148],[19,-118],[6,-121]],'#333b49');segment(c,[2,-140],[6,-23],1.5,'#a95260');
  for(const [x,y]of [[-15,-88],[17,-47]]){for(const [dx,dy,rx,ry]of [[0,0,12,7],[9,-4,7,6],[-6,-6,6,5]]){ellipse(c,x+dx,y+dy,rx+1.4,ry+1.4,'#cebbbd');ellipse(c,x+dx,y+dy,rx,ry,'#a74658');}}
 }
 if(id==='gaara'){
  polygon(c,[[-25,-133],[-15,-136],[25,-81],[21,-73]],'#e4e2d4');polygon(c,[[-20,-105],[-12,-105],[-15,-19],[-23,-16]],'#dad9cf');polygon(c,[[6,-75],[14,-75],[17,-19],[10,-14]],'#e6e2d4');segment(c,[-23,-77],[25,-77],2,'#292d31');
 }
 if(id==='temari'){
  polygon(c,[[-23,-130],[23,-131],[32,-77],[43,-49],[7,-47],[-32,-50],[-23,-81]],top);segment(c,[-21,-129],[4,-95],2,'#f0e2d9');polygon(c,[[-26,-89],[27,-88],[29,-75],[-27,-76]],'#765267');polygon(c,[[22,-82],[42,-74],[32,-65],[20,-76]],'#7e5571');
 }
 // Small fabric folds follow the torso rather than being painted over the screen.
 c.strokeStyle='#28343e44';c.lineWidth=1;for(const [x,y,dx]of [[-18,-91,9],[10,-113,6],[12,-87,7]]){c.beginPath();c.moveTo(x,y);c.quadraticCurveTo(x+dx*.4,y+3,x+dx,y+5);c.stroke();}
}
export function outfitArms(c,id,arm){
 const look=LOOKS[id];
 if(['sasuke','neji'].includes(id))wrap(c,arm[0],arm[1],11);
 if(id==='kiba'){fur(c,[arm[1][0]-5,arm[1][1]+2],[arm[1][0]+5,arm[1][1]+2],'#46503d',4);}
 if(id==='hinata')fur(c,[arm[1][0]-5,arm[1][1]+1],[arm[1][0]+5,arm[1][1]+1]);
 if(['kankuro','kakashi'].includes(id)){segment(c,arm[1],[arm[1][0]+2,arm[1][1]-1],9,id==='kakashi'?'#313c4c':'#303729');}
 if(id==='shikamaru'){segment(c,[-31,-111],[-22,-117],7,'#233b54');polygon(c,[[-32,-116],[-23,-119],[-20,-112],[-29,-108]],'#bdc8cc');}
 if(id==='jiraiya')mesh(c,[[arm[0][0]-4,arm[0][1]],[arm[0][0]+5,arm[0][1]],[arm[1][0]+5,arm[1][1]],[arm[1][0]-5,arm[1][1]]],'#a0aa94');
}
export function outfitHead(c,id,hasDog){
 if(id==='sasuke'){polygon(c,[[-23,-175],[-13,-179],[-16,-143],[-23,-136]],LOOKS[id].hair);polygon(c,[[14,-180],[23,-177],[25,-140],[17,-148]],LOOKS[id].hair);}
 if(id==='kakashi'){polygon(c,[[-24,-178],[-3,-173],[-7,-151],[-23,-154]],'#334052');polygon(c,[[-19,-176],[-5,-173],[-8,-162],[-22,-165]],'#b7c4ca');}
 if(id==='kankuro'){polygon(c,[[-15,-151],[-7,-147],[-13,-142]],'#895d79',null);polygon(c,[[8,-148],[17,-152],[13,-142]],'#895d79',null);polygon(c,[[-5,-139],[4,-138],[0,-133]],'#9a708c',null);}
 if(id==='gaara'){c.strokeStyle='#3c3037';c.lineWidth=2;c.beginPath();c.moveTo(-16,-157);c.lineTo(-7,-153);c.moveTo(4,-153);c.lineTo(15,-158);c.stroke();}
 if(id==='kiba'&&!hasDog){ellipse(c,-1,-211,16,11,'#e4e4d6');ellipse(c,8,-216,10,9,'#f1efe0');polygon(c,[[0,-220],[3,-229],[8,-219]],'#eee9d8');polygon(c,[[11,-221],[18,-227],[17,-216]],'#eee9d8');ellipse(c,13,-214,2,2,'#4b4b43');ellipse(c,20,-212,2,2,'#4b4b43');}
}
