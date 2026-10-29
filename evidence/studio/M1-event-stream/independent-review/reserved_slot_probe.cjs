// Finite actual-parser boundary checks. Synthetic framing, not execution evidence.
const fs=require('node:fs'),path=require('node:path'),Module=require('node:module'),crypto=require('node:crypto');
const root=path.resolve(__dirname,'../../../..'),relative='apps/studio-web/src/features/runs/sessionProtocol.ts',file=path.join(root,relative);
const sha=s=>crypto.createHash('sha256').update(s).digest('hex'),source=fs.readFileSync(file,'utf8');
const compiled=require(path.join(root,'node_modules/esbuild')).transformSync(source,{loader:'ts',format:'cjs'}).code;
const target=new Module(file,module);target.filename=file;target.paths=module.paths;target._compile(compiled,file);
const {SseParser}=target.exports,encoder=new TextEncoder();
const record=n=>`id: synthetic-${n}\nevent: log.appended\ndata: ${JSON.stringify({schemaVersion:'1.0',runId:'new-fixture',snapshotId:'fixture-snapshot',sequence:String(n),eventId:'fixture-event-'+n,type:'log.appended',payload:{message:'Public synthetic transport boundary'},digest:'a'.repeat(64),previousDigest:'b'.repeat(64)})}\n\n`;
const control='event: studio.stream_control\ndata: '+JSON.stringify({streamVersion:'1.1',type:'stream.gap',runId:'new-fixture',snapshotId:'fixture-snapshot',reason:'SLOW_CONSUMER',firstMissingSequence:'1',lastMissingSequence:'1015',missingCount:1015,integrity:'valid'})+'\n\n';
const records=Array.from({length:200},(_,i)=>record(i+1)).join('');
const cases=[];
for(const [name,input,expected] of [['control_then_200_data',control+records,true],['200_data_then_control',records+control,true],['200_data_only',records,true],['201_data',records+record(201),false],['two_control_slots',control+control,false],['200_data_two_controls',control+records+control,false]]){
 let accepted=false,frames=[],error=null;
 try{frames=new SseParser().feed(encoder.encode(input));accepted=true;}catch(e){error=e.message;}
 if(accepted!==expected)throw Error(name+' unexpected outcome '+JSON.stringify({accepted,error}));
 cases.push({name,inputBytes:encoder.encode(input).byteLength,accepted,frames:frames.length,error});
}
console.log(JSON.stringify({sourceBefore:{[relative]:sha(source)},sourceAfter:{[relative]:sha(fs.readFileSync(file,'utf8'))},cases,scope:'Production SseParser transformed in memory; six finite synthetic framing/count cases only, no browser/server/native runtime launched.'},null,2));
