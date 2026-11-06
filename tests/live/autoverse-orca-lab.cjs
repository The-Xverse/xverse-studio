const tools=require('./autoverse-orca-tools.cjs')(process.argv[2]);
const {chromium,expect,fs,path,out,c,pause,key,snapshot,spoken,speechText,focus}=tools;
(async()=>{
 const browser=await chromium.launch({headless:false,args:['--disable-gpu','--disable-gpu-rasterization','--force-renderer-accessibility=complete','--password-store=basic']});
 try {
  const context=await browser.newContext({baseURL:c.url,viewport:{width:c.width,height:c.width===1024?768:900},storageState:JSON.parse(fs.readFileSync(path.join(out,'browser-session.private.json')))});
  const page=await context.newPage(),writes=[],reads=[];
  page.on('request',request=>{const url=new URL(request.url());if(request.method()!=='GET') writes.push(url.pathname);if(url.pathname==='/api/v1/assets')reads.push(url.search);});
  await page.goto('/');await expect(page.getByRole('button',{name:'X-Verse Studio home',exact:true})).toBeVisible();
  await page.bringToFront();await spoken('Page has');await pause(300);
  const laboratory=page.getByRole('button',{name:'Laboratory',exact:true});
  await focus(page,laboratory,'Laboratory','laboratory-button');
  const first=page.waitForResponse(r=>new URL(r.url()).pathname==='/api/v1/assets');await key('Return');
  const response=await first;expect(response.status()).toBe(200);const observed=await response.json();
  expect(observed.items).toEqual([]);expect(observed.complete).toBe(true);
  const lab=page.locator('.lab-page'),inventory=page.getByRole('region',{name:'Inventory observation',exact:true});
  await expect(lab.getByRole('heading',{name:'No physical provider admitted',exact:true})).toBeVisible();
  await expect(inventory.getByRole('status')).toHaveText('Provider inventory observation is complete.');
  await expect(inventory).toContainText('No assets were returned on this page.');
  const tree=await snapshot('actual-empty-inventory');
  expect(tree.rows.some(r=>r.name==='No physical provider admitted'&&r.role==='heading')).toBe(true);
  expect(tree.rows.some(r=>r.name.includes('No assets were returned on this page.'))).toBe(true);
  const refresh=lab.getByRole('button',{name:'Refresh inventory',exact:true});
  await expect(refresh).toHaveAccessibleDescription(/new observation at the first page/);
  await focus(page,refresh,'Refresh inventory','inventory-refresh');
  const offset=speechText().length;
  const refreshed=page.waitForResponse(r=>new URL(r.url()).pathname==='/api/v1/assets');
  await key('Return');expect((await refreshed).status()).toBe(200);
  const heading=inventory.getByRole('heading',{name:'Inventory observation',exact:true});
  await expect(heading).toBeFocused();await spoken('Inventory observation',offset);
  const completed=await snapshot('inventory-completion');
  expect(completed.lastFocusEvent?.name).toBe('Inventory observation');expect(completed.lastFocusEvent?.role).toBe('heading');
  const measured=await heading.evaluate(n=>{const r=n.getBoundingClientRect(),s=getComputedStyle(n);return {box:r.toJSON(),outlineStyle:s.outlineStyle,outlineWidth:parseFloat(s.outlineWidth),viewport:{width:innerWidth,height:innerHeight}};});
  fs.writeFileSync(path.join(out,'lab-focus-measurement.json'),JSON.stringify(measured,null,2));
  // Match the existing native inventory test's completion-heading criterion.
  expect(measured.box.left>=0&&measured.box.top>=0&&measured.box.right<=measured.viewport.width+1&&measured.box.bottom<=measured.viewport.height+1&&measured.outlineStyle!=='none'&&measured.outlineWidth>0).toBe(true);
  await expect(lab.getByRole('button',{name:'Next inventory page',exact:true})).toBeDisabled();
  await expect(lab.getByRole('button',{name:'Previous inventory page',exact:true})).toBeDisabled();
  expect(reads).toHaveLength(2);expect(writes).toEqual([]);
  expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+1)).toBe(true);
  fs.writeFileSync(path.join(out,'browser-result.json'),JSON.stringify({suite:c.suite,version:browser.version(),width:c.width,commands:tools.keyCount,reads,writes,observed,actualEmptyRegistry:true,noPhysicalProviderAdmitted:true,completionFocus:completed.lastFocusEvent,scope:'Actual unregistered empty inventory and native refresh; no fixture response or device operation'},null,2));
 } finally {await browser.close();}
})().catch(error=>{console.error(error);process.exitCode=1;});
