# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: probe.spec.ts >> parameter presentation: real regrouping preserves Apply focus at 1440
- Location: .studio-local/parameter-presentation-focus/probe.spec.ts:6:37

# Error details

```
Error: expect(locator).toBeFocused() failed

Locator:  getByLabel('Duration').locator('xpath=ancestor::form').getByRole('button', { name: 'Apply', exact: true })
Expected: focused
Received: inactive
Timeout:  10000ms

Call log:
  - Expect "toBeFocused" getByLabel('Duration').locator('xpath=ancestor::form').getByRole('button', { name: 'Apply', exact: true }) with timeout 10000ms
  - waiting for getByLabel('Duration').locator('xpath=ancestor::form').getByRole('button', { name: 'Apply', exact: true })
    24 × locator resolved to <button class="small-button">Apply</button>
       - unexpected value "inactive"

```

```yaml
- button "Apply"
```

# Test source

```ts
  1  | import {test,expect,type Locator,type Page} from '@playwright/test';
  2  | import {connectStudio} from '../../tests/e2e/connect-studio';
  3  | import {traceApi} from '../../tests/e2e/trace-claims-flow';
  4  |
  5  | async function tabTo(page:Page,target:Locator){await expect(target).toBeVisible();for(let i=0;i<160;i++){if(await target.evaluate(node=>document.activeElement===node))return;await page.keyboard.press('Tab');}throw Error('Owned parameter control was not reachable by native Tab.');}
  6  | for(const width of [1024,1440]) test(`parameter presentation: real regrouping preserves Apply focus at ${width}`,async({page},info)=>{
  7  |  await page.setViewportSize({width,height:width===1024?768:900});await connectStudio(page,info);
  8  |  const project=(await traceApi(page,'/projects','POST',{name:'Late presentation keyboard control '+width})).body;
  9  |  await page.evaluate(id=>localStorage.setItem('studio.projectId',id),project.projectId);
  10 |  let release!:()=>void,ready!:()=>void,finish!:()=>void;const held=new Promise<void>(r=>release=r),actual=new Promise<void>(r=>ready=r),delivered=new Promise<void>(r=>finish=r);let presentation:any;
  11 |  const pattern=`**/api/v1/projects/${project.projectId}/presentation`;
  12 |  await page.route(pattern,async route=>{const response=await route.fetch();expect(response.status()).toBe(200);const text=await response.text();presentation=JSON.parse(text);const headers={...response.headers()};delete headers['content-length'];ready();await held;try{await route.fulfill({status:200,headers,body:text});}finally{finish();}});
  13 |  const edits:any[]=[];page.on('request',request=>{if(request.method()==='POST'&&request.url().endsWith(`/projects/${project.projectId}/edits`))edits.push(request.postDataJSON());});
  14 |  try{
  15 |   await page.reload();await actual;await expect(page.getByRole('heading',{name:project.name,exact:true})).toBeVisible();
  16 |   const field=page.getByLabel('Duration'),button=field.locator('xpath=ancestor::form').getByRole('button',{name:'Apply',exact:true});
  17 |   await tabTo(page,field);await page.keyboard.press('ControlOrMeta+A');await page.keyboard.insertText('7');await expect(field).toHaveValue('7');await tabTo(page,button);await expect(button).toBeFocused();
  18 |   expect(presentation.formGroups.length).toBeGreaterThan(0);release();await delivered;await expect(page.getByRole('group',{name:'Run horizon',exact:true})).toBeVisible();
  19 |   const beforeEnter=await button.evaluate(node=>({focused:document.activeElement===node,activeTag:document.activeElement?.tagName,value:(node.closest('form')?.querySelector('input') as HTMLInputElement)?.value}));
  20 |   await info.attach('native-presentation-focus',{contentType:'application/json',body:JSON.stringify({scope:'Actual owned presentation HTTP200 held; no DTO mutation. Native Tab reached Apply before actual metadata regrouped its form.',width,projectId:project.projectId,beforeEnter,edits})});
> 21 |   await expect(button).toBeFocused();await page.keyboard.press('Enter');await expect(page.locator('.alerts')).toContainText('Draft saved');
     |                        ^ Error: expect(locator).toBeFocused() failed
  22 |   expect(edits).toHaveLength(1);expect(edits[0].edits).toContainEqual(expect.objectContaining({kind:'set_parameter',parameterId:'duration',value:7}));
  23 |   const saved=(await traceApi(page,'/projects/'+project.projectId)).body;expect(saved.revision).toBe(project.revision+1);await expect(field).toHaveValue('7');
  24 |  }finally{release();await page.unroute(pattern);}
  25 | });
  26 |
```
