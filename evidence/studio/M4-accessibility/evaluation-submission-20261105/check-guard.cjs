const fs=require('node:fs'),crypto=require('node:crypto');
const ts=require('[MAIN_CHECKOUT]/node_modules/typescript');
const root=process.cwd(),base=root+'/.studio-local/t097-evaluation-keyboard-20261105';
function guard(path){const input=fs.readFileSync(path,'utf8');const file=ts.createSourceFile(path,input,ts.ScriptTarget.Latest,true,ts.ScriptKind.TSX);const node=file.statements.find(n=>ts.isFunctionDeclaration(n)&&n.name?.text==='assessmentReport');if(!node)throw Error('Missing identity/schema guard');return node.getText(file);}
const before=guard(base+'/before-submit-focus.private.tsx'),after=guard(root+'/apps/studio-web/src/features/experiments/FrozenAssessments.tsx');
if(before!==after)throw Error('Assessment identity/schema guard changed');
fs.writeFileSync(base+'/checks/guard-preservation.json',JSON.stringify({function:'assessmentReport',bodyUnchanged:true,sha256:crypto.createHash('sha256').update(after).digest('hex')},null,2)+'\n');
