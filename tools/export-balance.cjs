// Machine-readable native object snapshot. Supports build/map or a published MPQ.
const fs=require('node:fs'),path=require('node:path');
const root=path.resolve(__dirname,'..'),M=require('mdx-m3-viewer/dist/cjs/parsers/w3x/map').default;
const input=process.argv[2]||'build/map',output=process.argv[3]||'build/balance-current.json';
let archive=null;if(input.endsWith('.w3x')){archive=new M();archive.load(new Uint8Array(fs.readFileSync(path.resolve(root,input))),true);}
const read=n=>archive?Buffer.from(archive.get(n).bytes()):fs.readFileSync(path.resolve(root,input,n));
const result={abilities:{},units:{},items:{},research:{},misc:read('war3mapMisc.txt').toString(),hybrid:Object.fromEntries([...read('war3map.j').toString().matchAll(/set HybridPower\[(\d+)\] = ([0-9.]+)/g)].map(m=>[m[1],Number(m[2])]))};
for(const[kind,n,P]of [['abilities','war3map.w3a','w3d'],['units','war3map.w3u','w3u'],['items','war3map.w3t','w3u'],['research','war3map.w3q','w3d']]){
 const Parser=require('mdx-m3-viewer/dist/cjs/parsers/w3x/'+P+'/file').default,p=new Parser();p.load(new Uint8Array(read(n)));
 for(const o of [...p.originalTable.objects,...p.customTable.objects]){const id=o.newId==='\0\0\0\0'?o.oldId:o.newId;
  const fields={};for(const m of o.modifications)(fields[m.id]||={})[m.levelOrVariation||0]=m.value;
  result[kind][id]={base:o.oldId,fields};
 }
}
fs.writeFileSync(path.resolve(root,output),JSON.stringify(result));console.log('Exported '+input+' -> '+output);
