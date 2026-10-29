const fs=require('fs'),path=require('path'),crypto=require('crypto'),assert=require('assert');
const ts=require(path.join(process.cwd(),'node_modules/typescript'));
const base=path.join(process.cwd(),'.studio-local/scenario-timeline/readiness-fixture-repair');
const printer=ts.createPrinter({removeComments:true,newLine:ts.NewLineKind.LineFeed});
function rooted(n){if(ts.isIdentifier(n))return n.text==='expect';if(ts.isPropertyAccessExpression(n)||ts.isElementAccessExpression(n))return rooted(n.expression);if(ts.isCallExpression(n))return rooted(n.expression);return false;}
function calls(file){const source=ts.createSourceFile(file,fs.readFileSync(file,'utf8'),ts.ScriptTarget.Latest,true,ts.ScriptKind.TS),result=[];function visit(n){if(ts.isCallExpression(n)&&rooted(n.expression)&&!ts.isPropertyAccessExpression(n.parent)&&!ts.isCallExpression(n.parent))result.push(printer.printNode(ts.EmitHint.Unspecified,n,source));ts.forEachChild(n,visit);}visit(source);return result;}
const before=calls(path.join(base,'before.ts.txt')),after=calls(path.join(base,'after.ts.txt'));
const remaining=[...after];for(const expression of before){const i=remaining.indexOf(expression);assert(i>=0,'Removed or altered assertion: '+expression);remaining.splice(i,1);}
assert.equal(remaining.length,2);assert(remaining.every(x=>x.endsWith('.toBeEnabled()')));
const evidence={typescriptVersion:ts.version,beforeAssertionCount:before.length,afterAssertionCount:after.length,allOriginalAssertionExpressionsUnchanged:true,additionalAssertions:remaining,beforeSha256:crypto.createHash('sha256').update(fs.readFileSync(path.join(base,'before.ts.txt'))).digest('hex'),afterSha256:crypto.createHash('sha256').update(fs.readFileSync(path.join(base,'after.ts.txt'))).digest('hex')};
fs.writeFileSync(path.join(base,'assertion-preservation.json'),JSON.stringify(evidence,null,2)+'\n');process.stdout.write(JSON.stringify(evidence)+'\n');
