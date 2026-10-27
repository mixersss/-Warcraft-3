const fs=require('fs');
const source=fs.readFileSync(__dirname+'/verify-invasion20.cjs','utf8');
new Function('require','__dirname',source+`
const cfg50=JSON.parse(fs.readFileSync(path.join(root,'src/endless50.json')));
assert.deepEqual([cfg50.guardians[0].x,cfg50.guardians[0].y],nav['12'].target,'Preserve exact arena-side Hokage position');
assert.deepEqual(nav['31'],nav['12'],'Same village boundaries and routes');
const distances50=new Int32Array(w*w);distances50.fill(-1);let head50=0,tail50=0;const queue50=new Int32Array(w*w),start50=cell(cfg50.guardians[0].x,cfg50.guardians[0].y);queue50[tail50++]=start50;distances50[start50]=0;
while(head50<tail50){const a50=queue50[head50++];for(const b50 of[a50-1,a50+1,a50-w,a50+w])if(b50>=0&&b50<w*w&&!blocked[b50]&&distances50[b50]<0){distances50[b50]=distances50[a50]+32;queue50[tail50++]=b50;}}
for(let j50=0;j50<cfg50.guardians.length;j50++){
 const p50=cfg50.guardians[j50],c50=cell(p50.x,p50.y);assert(!blocked[c50]&&connected[c50]&&distances50[c50]>=0&&distances50[c50]<=1024,'Guardian is nearby along actual clear ground: '+j50);
 for(let k50=0;k50<j50;k50++){const q50=cfg50.guardians[k50];assert(Math.hypot(p50.x-q50.x,p50.y-q50.y)>=160,'Conservative spacing');}
 assert.equal(values('Endless50Kind')[j50],p50.kind);assert.equal(values('Endless50X')[j50],p50.x);assert.equal(values('Endless50Y')[j50],p50.y);
}
assert.equal(cfg50.guardians.length,17);
assert.equal(cfg50.heroSpawns.length,12,'All twelve slots need explicit village arrivals');
for(let j=0;j<12;j++){
 const p=cfg50.heroSpawns[j];assert.equal(values('Endless50SpawnX')[j],p[0]);assert.equal(values('Endless50SpawnY')[j],p[1]);
 assert(!blocked[cell(...p)]&&connected[cell(...p)],'All twelve arrivals have clear connected ground: '+j);
 assert((p[0]-16128)**2+(p[1]+15744)**2<800**2,'Inside village near fountain: '+j);
 for(let k=0;k<j;k++)assert(Math.hypot(p[0]-cfg50.heroSpawns[k][0],p[1]-cfg50.heroSpawns[k][1])>=96,'Separate hero arrivals');
}
console.log('PASS: all12 explicit endless-defense spawns inside village on connected ground, including Sand slots9/10/11.');
console.log('PASS:17 non-overlapping guardians within1024 ground travel of unchanged arena-side Sarutobi, all source invasion routes and hero arrivals remain connected (dynamic native collision untested).');
`)(require,__dirname);
