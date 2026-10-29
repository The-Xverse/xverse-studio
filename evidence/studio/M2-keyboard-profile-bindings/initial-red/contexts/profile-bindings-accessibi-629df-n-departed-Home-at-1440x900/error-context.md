# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: profile-bindings-accessibility.spec.ts >> profile bindings: committed reply cannot announce success on departed Home at 1440x900
- Location: tests/e2e/profile-bindings-accessibility.spec.ts:181:7

# Error details

```
Error: expect(locator).toHaveCount(expected) failed

Locator:  locator('.alerts .notice:not(.busy)')
Expected: 0
Received: 1
Timeout:  10000ms

Call log:
  - Expect "soft toHaveCount" locator('.alerts .notice:not(.busy)') with timeout 10000ms
  - waiting for locator('.alerts .notice:not(.busy)')
    24 × locator resolved to 1 element
       - unexpected value "1"

```

```
Error: expect(received).toEqual(expected) // deep equality

- Expected  - 1
+ Received  + 1

@@ -9,8 +9,8 @@
            "schemaDigest": "sha256:43d97f8dcadfa1246450121be31fc8c333f617301d29cf9cee100d8a8365bb6b",
            "version": "1.0.0",
          },
        ],
      },
-     "ifMatch": "1",
+     "ifMatch": "\"1\"",
    },
  ]
```

# Page snapshot

```yaml
- generic [ref=f1e3]:
  - link "Skip to workspace" [ref=f1e4] [cursor=pointer]:
    - /url: "#main-content"
  - banner [ref=f1e5]:
    - button "X-Verse Studio home" [active] [ref=f1e6] [cursor=pointer]:
      - generic [ref=f1e7]: X
      - generic [ref=f1e8]: X-VERSE STUDIO
    - generic [ref=f1e10]: Local workspace
    - generic [ref=f1e12]: REFERENCE PREVIEW
    - button "Environment" [ref=f1e13] [cursor=pointer]
    - generic "Local operator" [ref=f1e20]: LO
  - generic [ref=f1e21]:
    - navigation "Main navigation" [ref=f1e22]:
      - button "Workspace" [ref=f1e23] [cursor=pointer]
      - button "Catalog" [ref=f1e30] [cursor=pointer]
      - button "Laboratory" [ref=f1e37] [cursor=pointer]:
        - generic [ref=f1e41]: Lab
      - button "Compatibility and environment" [ref=f1e42] [cursor=pointer]:
        - generic [ref=f1e48]: Settings
      - generic [ref=f1e49]: v0.1
    - main [ref=f1e50]:
      - generic [ref=f1e52]:
        - text: Profile locks saved with exact schema and presentation identities.
        - button "Dismiss notice" [ref=f1e56] [cursor=pointer]
      - generic [ref=f1e59]:
        - generic [ref=f1e60]:
          - generic [ref=f1e61]:
            - generic [ref=f1e62]: LOCAL WORKSPACE
            - heading "Build understanding. One System at a time." [level=1] [ref=f1e63]: Build understanding.One System at a time.
            - paragraph [ref=f1e64]: Model, connect, and explore cyber-physical systems.Keep every experiment connected to its evidence.
          - generic [ref=f1e65]:
            - button "New project" [ref=f1e66] [cursor=pointer]
            - button "Import project" [ref=f1e69] [cursor=pointer]
            - button "Import evidence" [ref=f1e72] [cursor=pointer]
            - button "Import evidence archive" [ref=f1e75]
            - button "Import project archive" [ref=f1e76]
        - generic [ref=f1e77]:
          - generic [ref=f1e78]:
            - generic [ref=f1e79]:
              - heading "Start with an example" [level=2] [ref=f1e80]
              - paragraph [ref=f1e81]: A guided path from a model to a recorded result.
            - generic [ref=f1e82]: OWNED REFERENCE PROVIDER
          - generic [ref=f1e83]:
            - 'button "fixture Process control reference Explore a normalized process response, tune the setpoint and compare measured reference observations. Guided example owned_reference Scope limit: Owned executable reference only; external CARLA, native X-COM, process equipment and physical devices are not integrated." [ref=f1e84] [cursor=pointer]':
              - generic [ref=f1e85]: fixture
              - generic [ref=f1e101]:
                - heading "Process control reference" [level=3] [ref=f1e102]
                - paragraph [ref=f1e105]: Explore a normalized process response, tune the setpoint and compare measured reference observations.
                - generic [ref=f1e106]:
                  - generic [ref=f1e107]: Guided example
                  - generic [ref=f1e108]: owned_reference
                - paragraph [ref=f1e109]: "Scope limit: Owned executable reference only; external CARLA, native X-COM, process equipment and physical devices are not integrated."
            - 'button "fixture Automotive reference Explore a normalized controller and plant response using the same reference model; no vehicle dynamics claim. Guided example owned_reference Scope limit: Owned executable reference only; external CARLA, native X-COM, process equipment and physical devices are not integrated." [ref=f1e110] [cursor=pointer]':
              - generic [ref=f1e111]: fixture
              - generic [ref=f1e127]:
                - heading "Automotive reference" [level=3] [ref=f1e128]
                - paragraph [ref=f1e131]: Explore a normalized controller and plant response using the same reference model; no vehicle dynamics claim.
                - generic [ref=f1e132]:
                  - generic [ref=f1e133]: Guided example
                  - generic [ref=f1e134]: owned_reference
                - paragraph [ref=f1e135]: "Scope limit: Owned executable reference only; external CARLA, native X-COM, process equipment and physical devices are not integrated."
            - 'button "fixture Process control feedback reference Declare the reference loop''s unit-delay feedback explicitly and observe the state through an explicit linear converter to percent. Guided example owned_reference Scope limit: Owned executable reference only; external CARLA, native X-COM, process equipment and physical devices are not integrated." [ref=f1e136] [cursor=pointer]':
              - generic [ref=f1e137]: fixture
              - generic [ref=f1e153]:
                - heading "Process control feedback reference" [level=3] [ref=f1e154]
                - paragraph [ref=f1e157]: Declare the reference loop's unit-delay feedback explicitly and observe the state through an explicit linear converter to percent.
                - generic [ref=f1e158]:
                  - generic [ref=f1e159]: Guided example
                  - generic [ref=f1e160]: owned_reference
                - paragraph [ref=f1e161]: "Scope limit: Owned executable reference only; external CARLA, native X-COM, process equipment and physical devices are not integrated."
          - paragraph [ref=f1e162]: Reference runs verify Studio workflows. Their results do not establish external simulator or physical-device integration.
        - generic [ref=f1e166]:
          - generic [ref=f1e167]:
            - generic [ref=f1e168]:
              - heading "Recent projects" [level=2] [ref=f1e169]
              - paragraph [ref=f1e170]: Continue from your last saved draft.
            - generic [ref=f1e171]: 4 projects
          - generic [ref=f1e172]:
            - generic [ref=f1e173]:
              - button "Profile binding departure 1440 System workspace · rev 1 Local" [ref=f1e174] [cursor=pointer]:
                - generic [ref=f1e181]:
                  - strong [ref=f1e182]: Profile binding departure 1440
                  - generic [ref=f1e183]: System workspace · rev 1
                - generic [ref=f1e184]: Local
              - button "Review retention for project Profile binding departure 1440" [ref=f1e187] [cursor=pointer]: Retention
            - generic [ref=f1e188]:
              - button "Profile discovery 1440 System workspace · rev 1 Local" [ref=f1e189] [cursor=pointer]:
                - generic [ref=f1e196]:
                  - strong [ref=f1e197]: Profile discovery 1440
                  - generic [ref=f1e198]: System workspace · rev 1
                - generic [ref=f1e199]: Local
              - button "Review retention for project Profile discovery 1440" [ref=f1e202] [cursor=pointer]: Retention
            - generic [ref=f1e203]:
              - button "Profile binding departure 1024 System workspace · rev 2 Local" [ref=f1e204] [cursor=pointer]:
                - generic [ref=f1e211]:
                  - strong [ref=f1e212]: Profile binding departure 1024
                  - generic [ref=f1e213]: System workspace · rev 2
                - generic [ref=f1e214]: Local
              - button "Review retention for project Profile binding departure 1024" [ref=f1e217] [cursor=pointer]: Retention
            - generic [ref=f1e218]:
              - button "Profile discovery 1024 System workspace · rev 1 Local" [ref=f1e219] [cursor=pointer]:
                - generic [ref=f1e226]:
                  - strong [ref=f1e227]: Profile discovery 1024
                  - generic [ref=f1e228]: System workspace · rev 1
                - generic [ref=f1e229]: Local
              - button "Review retention for project Profile discovery 1024" [ref=f1e232] [cursor=pointer]: Retention
```

# Test source

```ts
  157 |       expect(writes).toBe(0);
  158 |       expect(
  159 |         (await request(page, `/projects/${project.projectId}`)).documents,
  160 |       ).toEqual(project.documents);
  161 |       expect(await runs(page, project.projectId)).toEqual(beforeRuns);
  162 |       await info.attach("profile-discovery.json", {
  163 |         body: JSON.stringify({
  164 |           viewport,
  165 |           controlledInitialStatus: 503,
  166 |           retryStatus: 200,
  167 |           actualRegistryRetried: true,
  168 |           observationsStayUnknownOnFailure: true,
  169 |           bindingWrites: writes,
  170 |           noStart: true,
  171 |           scope:
  172 |             "Labelled discovery transport failure then actual admitted registry; no provider installation or execution authority",
  173 |         }),
  174 |         contentType: "application/json",
  175 |       });
  176 |     } finally {
  177 |       await page.unroute(pattern);
  178 |     }
  179 |   });
  180 |
  181 |   test(`profile bindings: committed reply cannot announce success on departed Home at ${viewport.width}x${viewport.height}`, async ({
  182 |     page,
  183 |   }, info) => {
  184 |     test.setTimeout(90000);
  185 |     await page.setViewportSize(viewport);
  186 |     await connectStudio(page, info);
  187 |     const project = await create(
  188 |         page,
  189 |         `Profile binding departure ${viewport.width}`,
  190 |       ),
  191 |       beforeRuns = await runs(page, project.projectId),
  192 |       beforeProviders = await request(page, "/providers"),
  193 |       beforePlan = await request(
  194 |         page,
  195 |         `/projects/${project.projectId}/compilations`,
  196 |         { revision: project.revision },
  197 |       ),
  198 |       entries = (await request(page, "/profiles")).items,
  199 |       selected = entries.find(
  200 |         (p: any) => p.namespace === "io.xverse.studio.domain.automotive",
  201 |       );
  202 |     expect(selected.presentation.name).toBe("Automotive terminology");
  203 |     expect(selected.executionAllowed).toBe(false);
  204 |     await environment(page);
  205 |     const checkbox = panel(page).getByRole("checkbox", {
  206 |       name: "Select profile Automotive terminology",
  207 |       exact: true,
  208 |     });
  209 |     await tabTo(page, checkbox);
  210 |     await page.keyboard.press("Space");
  211 |     await expect(checkbox).toBeChecked();
  212 |     let release!: () => void,
  213 |       finish!: () => void,
  214 |       ready = false,
  215 |       committed: any;
  216 |     const gate = new Promise<void>((r) => (release = r)),
  217 |       finished = new Promise<void>((r) => (finish = r)),
  218 |       pattern = `**/api/v1/projects/${project.projectId}/profile-bindings`;
  219 |     const writes: { ifMatch?: string; body: any }[] = [];
  220 |     await page.route(pattern, async (route) => {
  221 |       try {
  222 |         expect(route.request().method()).toBe("POST");
  223 |         writes.push({
  224 |           ifMatch: route.request().headers()["if-match"],
  225 |           body: route.request().postDataJSON(),
  226 |         });
  227 |         const response = await route.fetch();
  228 |         expect(response.status()).toBe(200);
  229 |         committed = await response.json();
  230 |         ready = true;
  231 |         await gate;
  232 |         await route.fulfill({ response });
  233 |       } finally {
  234 |         finish();
  235 |       }
  236 |     });
  237 |     try {
  238 |       await activate(page, bind(page));
  239 |       await expect.poll(() => ready).toBe(true);
  240 |       expect(committed.projectId).toBe(project.projectId);
  241 |       expect(committed.revision).toBe(project.revision + 1);
  242 |       await activate(
  243 |         page,
  244 |         page.getByRole("button", { name: "X-Verse Studio home", exact: true }),
  245 |       );
  246 |       await expect(
  247 |         page.getByRole("heading", { name: "Recent projects", exact: true }),
  248 |       ).toBeVisible();
  249 |       release();
  250 |       await finished;
  251 |       await settle(page);
  252 |       await expect.soft(page.locator(".project-header")).toHaveCount(0);
  253 |       await expect
  254 |         .soft(page.locator(".alerts .notice:not(.busy)"))
  255 |         .toHaveCount(0);
  256 |       const saved = await request(page, `/projects/${project.projectId}`);
> 257 |       expect(writes).toEqual([
      |                      ^ Error: expect(received).toEqual(expected) // deep equality
  258 |         {
  259 |           ifMatch: String(project.revision),
  260 |           body: {
  261 |             baseRevision: project.revision,
  262 |             profiles: [
  263 |               {
  264 |                 profileId: selected.profileId,
  265 |                 version: selected.version,
  266 |                 schemaDigest: selected.schemaDigest,
  267 |                 presentationDigest: selected.presentationDigest,
  268 |               },
  269 |             ],
  270 |           },
  271 |         },
  272 |       ]);
  273 |       expect(saved.revision).toBe(project.revision + 1);
  274 |       for (const [id, document] of Object.entries<any>(project.documents))
  275 |         expect(saved.documents[id]).toEqual(document);
  276 |       for (const [name, content] of Object.entries(project.supportingFiles))
  277 |         expect(saved.supportingFiles[name]).toBe(content);
  278 |       const added = Object.keys(saved.documents).filter(
  279 |         (id) => !(id in project.documents),
  280 |       );
  281 |       expect(added).toHaveLength(1);
  282 |       const resource = parse(saved.documents[added[0]].content);
  283 |       expect(resource.kind).toBe("Profile");
  284 |       expect(resource.spec.extensionNamespace).toBe(selected.namespace);
  285 |       expect(resource.metadata.version).toBe(selected.version);
  286 |       const lock = saved.manifest.profiles.find(
  287 |         (p: any) => p.namespace === selected.namespace,
  288 |       );
  289 |       expect(lock).toMatchObject({
  290 |         namespace: selected.namespace,
  291 |         version: selected.version,
  292 |         schemaDigest: selected.schemaDigest,
  293 |         presentationDigest: selected.presentationDigest,
  294 |       });
  295 |       expect(digest(saved.supportingFiles[lock.schemaPath])).toBe(
  296 |         lock.schemaDigest,
  297 |       );
  298 |       expect(digest(saved.supportingFiles[lock.presentationPath])).toBe(
  299 |         lock.presentationDigest,
  300 |       );
  301 |       for (const previous of project.manifest.profiles)
  302 |         expect(saved.manifest.profiles).toContainEqual(previous);
  303 |       expect(saved.manifest.profiles).toHaveLength(
  304 |         project.manifest.profiles.length + 1,
  305 |       );
  306 |       expect(
  307 |         (
  308 |           await request(page, `/projects/${project.projectId}/validations`, {
  309 |             revision: saved.revision,
  310 |           })
  311 |         ).valid,
  312 |       ).toBe(true);
  313 |       expect(
  314 |         (
  315 |           await request(page, `/projects/${project.projectId}/compilations`, {
  316 |             revision: saved.revision,
  317 |           })
  318 |         ).planDigest,
  319 |       ).toBe(beforePlan.planDigest);
  320 |       expect(await request(page, "/providers")).toEqual(beforeProviders);
  321 |       expect(await runs(page, project.projectId)).toEqual(beforeRuns);
  322 |       await info.attach("profile-binding-departure.json", {
  323 |         body: JSON.stringify({
  324 |           viewport,
  325 |           projectId: project.projectId,
  326 |           profileId: selected.profileId,
  327 |           committedRevision: saved.revision,
  328 |           originalDocumentsPreserved: true,
  329 |           additiveLocksPreserved: true,
  330 |           exactSidecarDigests: true,
  331 |           authoritativeValidation: true,
  332 |           executablePlanUnchanged: true,
  333 |           providerDiscoveryUnchanged: true,
  334 |           noStart: true,
  335 |           scope:
  336 |             "Actual additive presentation-only lock transaction held after commit; departed workspace must not display stale success",
  337 |         }),
  338 |         contentType: "application/json",
  339 |       });
  340 |     } finally {
  341 |       release();
  342 |       await finished;
  343 |       await page.unroute(pattern);
  344 |     }
  345 |   });
  346 | }
  347 |
```
