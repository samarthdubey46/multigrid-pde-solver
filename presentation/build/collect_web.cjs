const fs=require('fs'),vm=require('vm');
const html=fs.readFileSync('web/index.html','utf8');
const scripts=[...html.matchAll(/<script(?:\s[^>]*)?>([\s\S]*?)<\/script>/g)].map(m=>m[1]);
const data=JSON.parse(scripts[0]),ctx=vm.createContext({});vm.runInContext(scripts[1],ctx);
const runs={};
for(const init of ['zero','linear','random']){
 const s=new ctx.PhotonicSolver.Solver(data,init), snapshots=[], flights=[];
 while(!s.finished){const o=s.next();if(!o.done){const e=o.value;
  if(e.scope==='outer'&&e.node==='check') snapshots.push({x:[...s.x],relative:s.lastRelative,outer:s.outer});
  if(e.scope==='smooth'&&e.node==='update'&&flights.length<4) flights.push(JSON.parse(JSON.stringify(s.flight)));
 }}
 runs[init]={...s.result(),snapshots,flights};
}
fs.writeFileSync('presentation/research/web-data.json',JSON.stringify({data,runs},null,2));
console.log(Object.fromEntries(Object.entries(runs).map(([k,r])=>[k,{residual:r.relativeResidual,counts:r.counts}])));
