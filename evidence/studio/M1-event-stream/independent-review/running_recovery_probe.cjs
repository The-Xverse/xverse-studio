// Transform current TypeScript without writing app/build/test sources.
const fs=require('node:fs'),path=require('node:path'),Module=require('node:module');
const root=path.resolve(__dirname,'../../../..');
const file=path.join(root,'apps/studio-web/src/features/runs/sessionProtocol.ts');
const source=fs.readFileSync(file,'utf8');
const compiled=require(path.join(root,'node_modules/esbuild')).transformSync(source,{loader:'ts',format:'cjs'}).code;
const target=new Module(file,module);target.filename=file;target.paths=module.paths;target._compile(compiled,file);
const input=JSON.parse(fs.readFileSync(0,'utf8'));
input.frontendGateSourceSha256=require('node:crypto').createHash('sha256').update(source).digest('hex');
input.probeNode=process.version;
try { const accepted=target.exports.recoveryValue(input.response,input.response.runId,input.response.snapshotId);input.clientResult={accepted:true,integrity:accepted.history.integrity}; }
catch(error){input.clientResult={accepted:false,error:error.message};}
input.integrityGateChecks=[];
for(const integrity of ['valid','verified_prefix','invalid','unavailable']) {
  const candidate=JSON.parse(JSON.stringify(input.response));candidate.history.integrity=integrity;
  try {target.exports.recoveryValue(candidate,candidate.runId,candidate.snapshotId);input.integrityGateChecks.push({integrity,accepted:true});}
  catch(error){input.integrityGateChecks.push({integrity,accepted:false,error:error.message});}
}
console.log(JSON.stringify(input,null,2));
