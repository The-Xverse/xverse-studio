# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: evidence-filters.spec.ts >> evidence filters: incompatible time resolution and numeric units remain table-only
- Location: tests/e2e/evidence-filters.spec.ts:580:5

# Error details

```
Error: expect(received).toBe(expected) // Object.is equality

Expected: "stopped"
Received: "running"

Call Log:
- Timeout 10000ms exceeded while waiting on the predicate
```

# Page snapshot

```yaml
- generic [ref=e3]:
  - link "Skip to workspace" [ref=e4] [cursor=pointer]:
    - /url: "#main-content"
  - banner [ref=e5]:
    - button "X-Verse Studio home" [ref=e6] [cursor=pointer]:
      - generic [ref=e7]: X
      - generic [ref=e8]: X-VERSE STUDIO
    - generic [ref=e10]: Local workspace
    - generic [ref=e12]: REFERENCE PREVIEW
    - button "Environment" [ref=e13] [cursor=pointer]
    - generic "Local operator" [ref=e20]: LO
  - generic [ref=e21]:
    - navigation "Main navigation" [ref=e22]:
      - button "Workspace" [ref=e23] [cursor=pointer]
      - button "Catalog" [ref=e30] [cursor=pointer]
      - button "Laboratory" [ref=e37] [cursor=pointer]:
        - generic [ref=e41]: Lab
      - button "Compatibility and environment" [ref=e42] [cursor=pointer]:
        - generic [ref=e48]: Settings
      - generic [ref=e49]: v0.1
    - main [ref=e50]:
      - generic [ref=e51]:
        - generic [ref=e52]:
          - generic [ref=e53]:
            - generic [ref=e54]: LOCAL WORKSPACE
            - heading "Build understanding. One System at a time." [level=1] [ref=e55]: Build understanding.One System at a time.
            - paragraph [ref=e56]: Model, connect, and explore cyber-physical systems.Keep every experiment connected to its evidence.
          - generic [ref=e57]:
            - button "New project" [ref=e58] [cursor=pointer]
            - button "Import project" [ref=e61] [cursor=pointer]
            - button "Import evidence" [ref=e64] [cursor=pointer]
            - button "Import evidence archive" [ref=e67]
            - button "Import project archive" [ref=e68]
        - generic [ref=e69]:
          - generic [ref=e70]:
            - generic [ref=e71]:
              - heading "Start with an example" [level=2] [ref=e72]
              - paragraph [ref=e73]: A guided path from a model to a recorded result.
            - generic [ref=e74]: OWNED REFERENCE PROVIDER
          - generic [ref=e75]:
            - 'button "fixture Process control reference Explore a normalized process response, tune the setpoint and compare measured reference observations. Guided example owned_reference Scope limit: Owned executable reference only; external CARLA, native X-COM, process equipment and physical devices are not integrated." [ref=e76] [cursor=pointer]':
              - generic [ref=e77]: fixture
              - generic [ref=e93]:
                - heading "Process control reference" [level=3] [ref=e94]
                - paragraph [ref=e97]: Explore a normalized process response, tune the setpoint and compare measured reference observations.
                - generic [ref=e98]:
                  - generic [ref=e99]: Guided example
                  - generic [ref=e100]: owned_reference
                - paragraph [ref=e101]: "Scope limit: Owned executable reference only; external CARLA, native X-COM, process equipment and physical devices are not integrated."
            - 'button "fixture Automotive reference Explore a normalized controller and plant response using the same reference model; no vehicle dynamics claim. Guided example owned_reference Scope limit: Owned executable reference only; external CARLA, native X-COM, process equipment and physical devices are not integrated." [ref=e102] [cursor=pointer]':
              - generic [ref=e103]: fixture
              - generic [ref=e119]:
                - heading "Automotive reference" [level=3] [ref=e120]
                - paragraph [ref=e123]: Explore a normalized controller and plant response using the same reference model; no vehicle dynamics claim.
                - generic [ref=e124]:
                  - generic [ref=e125]: Guided example
                  - generic [ref=e126]: owned_reference
                - paragraph [ref=e127]: "Scope limit: Owned executable reference only; external CARLA, native X-COM, process equipment and physical devices are not integrated."
            - 'button "fixture Process control feedback reference Declare the reference loop''s unit-delay feedback explicitly and observe the state through an explicit linear converter to percent. Guided example owned_reference Scope limit: Owned executable reference only; external CARLA, native X-COM, process equipment and physical devices are not integrated." [ref=e128] [cursor=pointer]':
              - generic [ref=e129]: fixture
              - generic [ref=e145]:
                - heading "Process control feedback reference" [level=3] [ref=e146]
                - paragraph [ref=e149]: Declare the reference loop's unit-delay feedback explicitly and observe the state through an explicit linear converter to percent.
                - generic [ref=e150]:
                  - generic [ref=e151]: Guided example
                  - generic [ref=e152]: owned_reference
                - paragraph [ref=e153]: "Scope limit: Owned executable reference only; external CARLA, native X-COM, process equipment and physical devices are not integrated."
          - paragraph [ref=e154]: Reference runs verify Studio workflows. Their results do not establish external simulator or physical-device integration.
        - generic [ref=e158]:
          - generic [ref=e159]:
            - generic [ref=e160]:
              - heading "Recent projects" [level=2] [ref=e161]
              - paragraph [ref=e162]: Continue from your last saved draft.
            - generic [ref=e163]: 59 projects
          - generic [ref=e164]:
            - generic [ref=e165]:
              - button "Sealed recorded evidence filtering fixture System workspace · rev 1 Local" [ref=e166] [cursor=pointer]:
                - generic [ref=e173]:
                  - strong [ref=e174]: Sealed recorded evidence filtering fixture
                  - generic [ref=e175]: System workspace · rev 1
                - generic [ref=e176]: Local
              - button "Review retention for project Sealed recorded evidence filtering fixture" [ref=e179] [cursor=pointer]: Retention
            - generic [ref=e180]:
              - button "Observation response isolation System workspace · rev 2 Local" [ref=e181] [cursor=pointer]:
                - generic [ref=e188]:
                  - strong [ref=e189]: Observation response isolation
                  - generic [ref=e190]: System workspace · rev 2
                - generic [ref=e191]: Local
              - button "Review retention for project Observation response isolation" [ref=e194] [cursor=pointer]: Retention
            - generic [ref=e195]:
              - button "Missing-time display contract System workspace · rev 2 Local" [ref=e196] [cursor=pointer]:
                - generic [ref=e203]:
                  - strong [ref=e204]: Missing-time display contract
                  - generic [ref=e205]: System workspace · rev 2
                - generic [ref=e206]: Local
              - button "Review retention for project Missing-time display contract" [ref=e209] [cursor=pointer]: Retention
            - generic [ref=e210]:
              - button "Evidence receipt and filters System workspace · rev 2 Local" [ref=e211] [cursor=pointer]:
                - generic [ref=e218]:
                  - strong [ref=e219]: Evidence receipt and filters
                  - generic [ref=e220]: System workspace · rev 2
                - generic [ref=e221]: Local
              - button "Review retention for project Evidence receipt and filters" [ref=e224] [cursor=pointer]: Retention
            - generic [ref=e225]:
              - button "Unreadable source recovery System workspace · rev 3 Local" [ref=e226] [cursor=pointer]:
                - generic [ref=e233]:
                  - strong [ref=e234]: Unreadable source recovery
                  - generic [ref=e235]: System workspace · rev 3
                - generic [ref=e236]: Local
              - button "Review retention for project Unreadable source recovery" [ref=e239] [cursor=pointer]: Retention
            - generic [ref=e240]:
              - button "Interleaved source save System workspace · rev 6 Local" [ref=e241] [cursor=pointer]:
                - generic [ref=e248]:
                  - strong [ref=e249]: Interleaved source save
                  - generic [ref=e250]: System workspace · rev 6
                - generic [ref=e251]: Local
              - button "Review retention for project Interleaved source save" [ref=e254] [cursor=pointer]: Retention
            - generic [ref=e255]:
              - button "External source recovery System workspace · rev 3 Local" [ref=e256] [cursor=pointer]:
                - generic [ref=e263]:
                  - strong [ref=e264]: External source recovery
                  - generic [ref=e265]: System workspace · rev 3
                - generic [ref=e266]: Local
              - button "Review retention for project External source recovery" [ref=e269] [cursor=pointer]: Retention
            - generic [ref=e270]:
              - button "Undo redo isolation System workspace · rev 8 Local" [ref=e271] [cursor=pointer]:
                - generic [ref=e278]:
                  - strong [ref=e279]: Undo redo isolation
                  - generic [ref=e280]: System workspace · rev 8
                - generic [ref=e281]: Local
              - button "Review retention for project Undo redo isolation" [ref=e284] [cursor=pointer]: Retention
            - generic [ref=e285]:
              - button "Diagnosis blocked preflight System workspace · rev 1 Local" [ref=e286] [cursor=pointer]:
                - generic [ref=e293]:
                  - strong [ref=e294]: Diagnosis blocked preflight
                  - generic [ref=e295]: System workspace · rev 1
                - generic [ref=e296]: Local
              - button "Review retention for project Diagnosis blocked preflight" [ref=e299] [cursor=pointer]: Retention
            - generic [ref=e300]:
              - button "Diagnosis completed run System workspace · rev 2 Local" [ref=e301] [cursor=pointer]:
                - generic [ref=e308]:
                  - strong [ref=e309]: Diagnosis completed run
                  - generic [ref=e310]: System workspace · rev 2
                - generic [ref=e311]: Local
              - button "Review retention for project Diagnosis completed run" [ref=e314] [cursor=pointer]: Retention
            - generic [ref=e315]:
              - button "Diagnosis recorded evidence System workspace · rev 1 Local" [ref=e316] [cursor=pointer]:
                - generic [ref=e323]:
                  - strong [ref=e324]: Diagnosis recorded evidence
                  - generic [ref=e325]: System workspace · rev 1
                - generic [ref=e326]: Local
              - button "Review retention for project Diagnosis recorded evidence" [ref=e329] [cursor=pointer]: Retention
            - generic [ref=e330]:
              - button "Stale plan diagnostic 1440 System workspace · rev 2 Local" [ref=e331] [cursor=pointer]:
                - generic [ref=e338]:
                  - strong [ref=e339]: Stale plan diagnostic 1440
                  - generic [ref=e340]: System workspace · rev 2
                - generic [ref=e341]: Local
              - button "Review retention for project Stale plan diagnostic 1440" [ref=e344] [cursor=pointer]: Retention
            - generic [ref=e345]:
              - button "Late preflight 1440 Workspace System workspace · rev 2 Local" [ref=e346] [cursor=pointer]:
                - generic [ref=e353]:
                  - strong [ref=e354]: Late preflight 1440 Workspace
                  - generic [ref=e355]: System workspace · rev 2
                - generic [ref=e356]: Local
              - button "Review retention for project Late preflight 1440 Workspace" [ref=e359] [cursor=pointer]: Retention
            - generic [ref=e360]:
              - button "Late preflight 1440 Home System workspace · rev 2 Local" [ref=e361] [cursor=pointer]:
                - generic [ref=e368]:
                  - strong [ref=e369]: Late preflight 1440 Home
                  - generic [ref=e370]: System workspace · rev 2
                - generic [ref=e371]: Local
              - button "Review retention for project Late preflight 1440 Home" [ref=e374] [cursor=pointer]: Retention
            - generic [ref=e375]:
              - button "Diagnostic presentation fixture 1440 System workspace · rev 1 Local" [ref=e376] [cursor=pointer]:
                - generic [ref=e383]:
                  - strong [ref=e384]: Diagnostic presentation fixture 1440
                  - generic [ref=e385]: System workspace · rev 1
                - generic [ref=e386]: Local
              - button "Review retention for project Diagnostic presentation fixture 1440" [ref=e389] [cursor=pointer]: Retention
            - generic [ref=e390]:
              - button "Keyboard diagnostic recovery 1440 System workspace · rev 3 Local" [ref=e391] [cursor=pointer]:
                - generic [ref=e398]:
                  - strong [ref=e399]: Keyboard diagnostic recovery 1440
                  - generic [ref=e400]: System workspace · rev 3
                - generic [ref=e401]: Local
              - button "Review retention for project Keyboard diagnostic recovery 1440" [ref=e404] [cursor=pointer]: Retention
            - generic [ref=e405]:
              - button "Stale plan diagnostic 1024 System workspace · rev 2 Local" [ref=e406] [cursor=pointer]:
                - generic [ref=e413]:
                  - strong [ref=e414]: Stale plan diagnostic 1024
                  - generic [ref=e415]: System workspace · rev 2
                - generic [ref=e416]: Local
              - button "Review retention for project Stale plan diagnostic 1024" [ref=e419] [cursor=pointer]: Retention
            - generic [ref=e420]:
              - button "Late preflight 1024 Workspace System workspace · rev 2 Local" [ref=e421] [cursor=pointer]:
                - generic [ref=e428]:
                  - strong [ref=e429]: Late preflight 1024 Workspace
                  - generic [ref=e430]: System workspace · rev 2
                - generic [ref=e431]: Local
              - button "Review retention for project Late preflight 1024 Workspace" [ref=e434] [cursor=pointer]: Retention
            - generic [ref=e435]:
              - button "Late preflight 1024 Home System workspace · rev 2 Local" [ref=e436] [cursor=pointer]:
                - generic [ref=e443]:
                  - strong [ref=e444]: Late preflight 1024 Home
                  - generic [ref=e445]: System workspace · rev 2
                - generic [ref=e446]: Local
              - button "Review retention for project Late preflight 1024 Home" [ref=e449] [cursor=pointer]: Retention
            - generic [ref=e450]:
              - button "Diagnostic presentation fixture 1024 System workspace · rev 1 Local" [ref=e451] [cursor=pointer]:
                - generic [ref=e458]:
                  - strong [ref=e459]: Diagnostic presentation fixture 1024
                  - generic [ref=e460]: System workspace · rev 1
                - generic [ref=e461]: Local
              - button "Review retention for project Diagnostic presentation fixture 1024" [ref=e464] [cursor=pointer]: Retention
            - generic [ref=e465]:
              - button "Keyboard diagnostic recovery 1024 System workspace · rev 3 Local" [ref=e466] [cursor=pointer]:
                - generic [ref=e473]:
                  - strong [ref=e474]: Keyboard diagnostic recovery 1024
                  - generic [ref=e475]: System workspace · rev 3
                - generic [ref=e476]: Local
              - button "Review retention for project Keyboard diagnostic recovery 1024" [ref=e479] [cursor=pointer]: Retention
            - generic [ref=e480]:
              - button "Realization classes System workspace · rev 1 Local" [ref=e481] [cursor=pointer]:
                - generic [ref=e488]:
                  - strong [ref=e489]: Realization classes
                  - generic [ref=e490]: System workspace · rev 1
                - generic [ref=e491]: Local
              - button "Review retention for project Realization classes" [ref=e494] [cursor=pointer]: Retention
            - generic [ref=e495]:
              - button "Deployment resolution System workspace · rev 10 Local" [ref=e496] [cursor=pointer]:
                - generic [ref=e503]:
                  - strong [ref=e504]: Deployment resolution
                  - generic [ref=e505]: System workspace · rev 10
                - generic [ref=e506]: Local
              - button "Review retention for project Deployment resolution" [ref=e509] [cursor=pointer]: Retention
            - generic [ref=e510]:
              - button "Deployment review newer readiness 1440 System workspace · rev 2 Local" [ref=e511] [cursor=pointer]:
                - generic [ref=e518]:
                  - strong [ref=e519]: Deployment review newer readiness 1440
                  - generic [ref=e520]: System workspace · rev 2
                - generic [ref=e521]: Local
              - button "Review retention for project Deployment review newer readiness 1440" [ref=e524] [cursor=pointer]: Retention
            - generic [ref=e525]:
              - button "Deployment review explicit clone loading 1440 System workspace · rev 4 Local" [ref=e526] [cursor=pointer]:
                - generic [ref=e533]:
                  - strong [ref=e534]: Deployment review explicit clone loading 1440
                  - generic [ref=e535]: System workspace · rev 4
                - generic [ref=e536]: Local
              - button "Review retention for project Deployment review explicit clone loading 1440" [ref=e539] [cursor=pointer]: Retention
            - generic [ref=e540]:
              - button "Deployment completion different variant 1440 System workspace · rev 5 Local" [ref=e541] [cursor=pointer]:
                - generic [ref=e548]:
                  - strong [ref=e549]: Deployment completion different variant 1440
                  - generic [ref=e550]: System workspace · rev 5
                - generic [ref=e551]: Local
              - button "Review retention for project Deployment completion different variant 1440" [ref=e554] [cursor=pointer]: Retention
            - generic [ref=e555]:
              - button "Deployment completion deliberate focus 1440 System workspace · rev 5 Local" [ref=e556] [cursor=pointer]:
                - generic [ref=e563]:
                  - strong [ref=e564]: Deployment completion deliberate focus 1440
                  - generic [ref=e565]: System workspace · rev 5
                - generic [ref=e566]: Local
              - button "Review retention for project Deployment completion deliberate focus 1440" [ref=e569] [cursor=pointer]: Retention
            - generic [ref=e570]:
              - button "Deployment completion newer reopened head 1440 System workspace · rev 5 Local" [ref=e571] [cursor=pointer]:
                - generic [ref=e578]:
                  - strong [ref=e579]: Deployment completion newer reopened head 1440
                  - generic [ref=e580]: System workspace · rev 5
                - generic [ref=e581]: Local
              - button "Review retention for project Deployment completion newer reopened head 1440" [ref=e584] [cursor=pointer]: Retention
            - generic [ref=e585]:
              - button "Late deployment mapping 1440 System workspace · rev 4 Local" [ref=e586] [cursor=pointer]:
                - generic [ref=e593]:
                  - strong [ref=e594]: Late deployment mapping 1440
                  - generic [ref=e595]: System workspace · rev 4
                - generic [ref=e596]: Local
              - button "Review retention for project Late deployment mapping 1440" [ref=e599] [cursor=pointer]: Retention
            - generic [ref=e600]:
              - button "Late deployment resource 1440 System workspace · rev 4 Local" [ref=e601] [cursor=pointer]:
                - generic [ref=e608]:
                  - strong [ref=e609]: Late deployment resource 1440
                  - generic [ref=e610]: System workspace · rev 4
                - generic [ref=e611]: Local
              - button "Review retention for project Late deployment resource 1440" [ref=e614] [cursor=pointer]: Retention
            - generic [ref=e615]:
              - button "Late deployment clone 1440 System workspace · rev 4 Local" [ref=e616] [cursor=pointer]:
                - generic [ref=e623]:
                  - strong [ref=e624]: Late deployment clone 1440
                  - generic [ref=e625]: System workspace · rev 4
                - generic [ref=e626]: Local
              - button "Review retention for project Late deployment clone 1440" [ref=e629] [cursor=pointer]: Retention
            - generic [ref=e630]:
              - button "Keyboard deployment 1440 System workspace · rev 7 Local" [ref=e631] [cursor=pointer]:
                - generic [ref=e638]:
                  - strong [ref=e639]: Keyboard deployment 1440
                  - generic [ref=e640]: System workspace · rev 7
                - generic [ref=e641]: Local
              - button "Review retention for project Keyboard deployment 1440" [ref=e644] [cursor=pointer]: Retention
            - generic [ref=e645]:
              - button "Deployment review newer readiness 1024 System workspace · rev 2 Local" [ref=e646] [cursor=pointer]:
                - generic [ref=e653]:
                  - strong [ref=e654]: Deployment review newer readiness 1024
                  - generic [ref=e655]: System workspace · rev 2
                - generic [ref=e656]: Local
              - button "Review retention for project Deployment review newer readiness 1024" [ref=e659] [cursor=pointer]: Retention
            - generic [ref=e660]:
              - button "Deployment review explicit clone loading 1024 System workspace · rev 4 Local" [ref=e661] [cursor=pointer]:
                - generic [ref=e668]:
                  - strong [ref=e669]: Deployment review explicit clone loading 1024
                  - generic [ref=e670]: System workspace · rev 4
                - generic [ref=e671]: Local
              - button "Review retention for project Deployment review explicit clone loading 1024" [ref=e674] [cursor=pointer]: Retention
            - generic [ref=e675]:
              - button "Deployment completion different variant 1024 System workspace · rev 5 Local" [ref=e676] [cursor=pointer]:
                - generic [ref=e683]:
                  - strong [ref=e684]: Deployment completion different variant 1024
                  - generic [ref=e685]: System workspace · rev 5
                - generic [ref=e686]: Local
              - button "Review retention for project Deployment completion different variant 1024" [ref=e689] [cursor=pointer]: Retention
            - generic [ref=e690]:
              - button "Deployment completion deliberate focus 1024 System workspace · rev 5 Local" [ref=e691] [cursor=pointer]:
                - generic [ref=e698]:
                  - strong [ref=e699]: Deployment completion deliberate focus 1024
                  - generic [ref=e700]: System workspace · rev 5
                - generic [ref=e701]: Local
              - button "Review retention for project Deployment completion deliberate focus 1024" [ref=e704] [cursor=pointer]: Retention
            - generic [ref=e705]:
              - button "Deployment completion newer reopened head 1024 System workspace · rev 5 Local" [ref=e706] [cursor=pointer]:
                - generic [ref=e713]:
                  - strong [ref=e714]: Deployment completion newer reopened head 1024
                  - generic [ref=e715]: System workspace · rev 5
                - generic [ref=e716]: Local
              - button "Review retention for project Deployment completion newer reopened head 1024" [ref=e719] [cursor=pointer]: Retention
            - generic [ref=e720]:
              - button "Late deployment mapping 1024 System workspace · rev 4 Local" [ref=e721] [cursor=pointer]:
                - generic [ref=e728]:
                  - strong [ref=e729]: Late deployment mapping 1024
                  - generic [ref=e730]: System workspace · rev 4
                - generic [ref=e731]: Local
              - button "Review retention for project Late deployment mapping 1024" [ref=e734] [cursor=pointer]: Retention
            - generic [ref=e735]:
              - button "Late deployment resource 1024 System workspace · rev 4 Local" [ref=e736] [cursor=pointer]:
                - generic [ref=e743]:
                  - strong [ref=e744]: Late deployment resource 1024
                  - generic [ref=e745]: System workspace · rev 4
                - generic [ref=e746]: Local
              - button "Review retention for project Late deployment resource 1024" [ref=e749] [cursor=pointer]: Retention
            - generic [ref=e750]:
              - button "Late deployment clone 1024 System workspace · rev 4 Local" [ref=e751] [cursor=pointer]:
                - generic [ref=e758]:
                  - strong [ref=e759]: Late deployment clone 1024
                  - generic [ref=e760]: System workspace · rev 4
                - generic [ref=e761]: Local
              - button "Review retention for project Late deployment clone 1024" [ref=e764] [cursor=pointer]: Retention
            - generic [ref=e765]:
              - button "Keyboard deployment 1024 System workspace · rev 7 Local" [ref=e766] [cursor=pointer]:
                - generic [ref=e773]:
                  - strong [ref=e774]: Keyboard deployment 1024
                  - generic [ref=e775]: System workspace · rev 7
                - generic [ref=e776]: Local
              - button "Review retention for project Keyboard deployment 1024" [ref=e779] [cursor=pointer]: Retention
            - generic [ref=e780]:
              - button "Live communication System workspace · rev 2 Local" [ref=e781] [cursor=pointer]:
                - generic [ref=e788]:
                  - strong [ref=e789]: Live communication
                  - generic [ref=e790]: System workspace · rev 2
                - generic [ref=e791]: Local
              - button "Review retention for project Live communication" [ref=e794] [cursor=pointer]: Retention
            - generic [ref=e795]:
              - button "Communication perspectives System workspace · rev 2 Local" [ref=e796] [cursor=pointer]:
                - generic [ref=e803]:
                  - strong [ref=e804]: Communication perspectives
                  - generic [ref=e805]: System workspace · rev 2
                - generic [ref=e806]: Local
              - button "Review retention for project Communication perspectives" [ref=e809] [cursor=pointer]: Retention
            - generic [ref=e810]:
              - button "Relation kinds System workspace · rev 3 Local" [ref=e811] [cursor=pointer]:
                - generic [ref=e818]:
                  - strong [ref=e819]: Relation kinds
                  - generic [ref=e820]: System workspace · rev 3
                - generic [ref=e821]: Local
              - button "Review retention for project Relation kinds" [ref=e824] [cursor=pointer]: Retention
            - generic [ref=e825]:
              - button "Feedback contracts System workspace · rev 1 Local" [ref=e826] [cursor=pointer]:
                - generic [ref=e833]:
                  - strong [ref=e834]: Feedback contracts
                  - generic [ref=e835]: System workspace · rev 1
                - generic [ref=e836]: Local
              - button "Review retention for project Feedback contracts" [ref=e839] [cursor=pointer]: Retention
            - generic [ref=e840]:
              - button "Explicit converter System workspace · rev 2 Local" [ref=e841] [cursor=pointer]:
                - generic [ref=e848]:
                  - strong [ref=e849]: Explicit converter
                  - generic [ref=e850]: System workspace · rev 2
                - generic [ref=e851]: Local
              - button "Review retention for project Explicit converter" [ref=e854] [cursor=pointer]: Retention
            - generic [ref=e855]:
              - button "Feedback cycle System workspace · rev 2 Local" [ref=e856] [cursor=pointer]:
                - generic [ref=e863]:
                  - strong [ref=e864]: Feedback cycle
                  - generic [ref=e865]: System workspace · rev 2
                - generic [ref=e866]: Local
              - button "Review retention for project Feedback cycle" [ref=e869] [cursor=pointer]: Retention
            - generic [ref=e870]:
              - button "Connection admission System workspace · rev 1 Local" [ref=e871] [cursor=pointer]:
                - generic [ref=e878]:
                  - strong [ref=e879]: Connection admission
                  - generic [ref=e880]: System workspace · rev 1
                - generic [ref=e881]: Local
              - button "Review retention for project Connection admission" [ref=e884] [cursor=pointer]: Retention
            - generic [ref=e885]:
              - button "Keyboard connection 1440 System workspace · rev 3 Local" [ref=e886] [cursor=pointer]:
                - generic [ref=e893]:
                  - strong [ref=e894]: Keyboard connection 1440
                  - generic [ref=e895]: System workspace · rev 3
                - generic [ref=e896]: Local
              - button "Review retention for project Keyboard connection 1440" [ref=e899] [cursor=pointer]: Retention
            - generic [ref=e900]:
              - button "Keyboard connection 1024 System workspace · rev 3 Local" [ref=e901] [cursor=pointer]:
                - generic [ref=e908]:
                  - strong [ref=e909]: Keyboard connection 1024
                  - generic [ref=e910]: System workspace · rev 3
                - generic [ref=e911]: Local
              - button "Review retention for project Keyboard connection 1024" [ref=e914] [cursor=pointer]: Retention
            - generic [ref=e915]:
              - button "Catalog fixture (unsupported) System workspace · rev 1 Local" [ref=e916] [cursor=pointer]:
                - generic [ref=e923]:
                  - strong [ref=e924]: Catalog fixture (unsupported)
                  - generic [ref=e925]: System workspace · rev 1
                - generic [ref=e926]: Local
              - button "Review retention for project Catalog fixture (unsupported)" [ref=e929] [cursor=pointer]: Retention
            - generic [ref=e930]:
              - button "Catalog fixture (service) System workspace · rev 3 Local" [ref=e931] [cursor=pointer]:
                - generic [ref=e938]:
                  - strong [ref=e939]: Catalog fixture (service)
                  - generic [ref=e940]: System workspace · rev 3
                - generic [ref=e941]: Local
              - button "Review retention for project Catalog fixture (service)" [ref=e944] [cursor=pointer]: Retention
            - generic [ref=e945]:
              - button "Configurable instance System workspace · rev 3 Local" [ref=e946] [cursor=pointer]:
                - generic [ref=e953]:
                  - strong [ref=e954]: Configurable instance
                  - generic [ref=e955]: System workspace · rev 3
                - generic [ref=e956]: Local
              - button "Review retention for project Configurable instance" [ref=e959] [cursor=pointer]: Retention
            - generic [ref=e960]:
              - button "Instance wizard System workspace · rev 2 Local" [ref=e961] [cursor=pointer]:
                - generic [ref=e968]:
                  - strong [ref=e969]: Instance wizard
                  - generic [ref=e970]: System workspace · rev 2
                - generic [ref=e971]: Local
              - button "Review retention for project Instance wizard" [ref=e974] [cursor=pointer]: Retention
            - generic [ref=e975]:
              - button "Process control reference System workspace · rev 1 Local" [ref=e976] [cursor=pointer]:
                - generic [ref=e983]:
                  - strong [ref=e984]: Process control reference
                  - generic [ref=e985]: System workspace · rev 1
                - generic [ref=e986]: Local
              - button "Review retention for project Process control reference" [ref=e989] [cursor=pointer]: Retention
            - generic [ref=e990]:
              - button "Neutral asset authoring System workspace · rev 6 Local" [ref=e991] [cursor=pointer]:
                - generic [ref=e998]:
                  - strong [ref=e999]: Neutral asset authoring
                  - generic [ref=e1000]: System workspace · rev 6
                - generic [ref=e1001]: Local
              - button "Review retention for project Neutral asset authoring" [ref=e1004] [cursor=pointer]: Retention
            - generic [ref=e1005]:
              - button "Annotation context reference System workspace · rev 2 Local" [ref=e1006] [cursor=pointer]:
                - generic [ref=e1013]:
                  - strong [ref=e1014]: Annotation context reference
                  - generic [ref=e1015]: System workspace · rev 2
                - generic [ref=e1016]: Local
              - button "Review retention for project Annotation context reference" [ref=e1019] [cursor=pointer]: Retention
            - generic [ref=e1020]:
              - button "Process control reference System workspace · rev 2 Local" [ref=e1021] [cursor=pointer]:
                - generic [ref=e1028]:
                  - strong [ref=e1029]: Process control reference
                  - generic [ref=e1030]: System workspace · rev 2
                - generic [ref=e1031]: Local
              - button "Review retention for project Process control reference" [ref=e1034] [cursor=pointer]: Retention
            - generic [ref=e1035]:
              - button "Process control reference System workspace · rev 2 Local" [ref=e1036] [cursor=pointer]:
                - generic [ref=e1043]:
                  - strong [ref=e1044]: Process control reference
                  - generic [ref=e1045]: System workspace · rev 2
                - generic [ref=e1046]: Local
              - button "Review retention for project Process control reference" [ref=e1049] [cursor=pointer]: Retention
```

# Test source

```ts
  494 |     await apply();
  495 |     await expect(page.locator("[data-observation-id]")).toHaveCount(2);
  496 |     await expect(
  497 |       page.locator(`[data-observation-id="${fixture.events.hugeBefore}"]`),
  498 |     ).toContainText("2026-01-01T00:00:00.250000Z");
  499 |     await expect(
  500 |       page.locator(`[data-observation-id="${fixture.events.hugeInside}"]`),
  501 |     ).toBeVisible();
  502 |     const numericReceipt = page.locator(
  503 |       `[data-observation-id="${fixture.events.hugeBefore}"]`,
  504 |     );
  505 |     await numericReceipt.getByText("Original receipt", { exact: true }).click();
  506 |     await expect(numericReceipt.locator("pre")).toContainText("1767225600.25");
  507 |     await numericReceipt.getByText("Original receipt", { exact: true }).click();
  508 |     const tableRegion = page.getByRole("region", {
  509 |       name: "Exact observation table scroll region",
  510 |       exact: true,
  511 |     });
  512 |     await tableRegion.focus();
  513 |     await expect(tableRegion).toBeFocused();
  514 |     const scrollSize = await tableRegion.evaluate((el) => ({
  515 |       width: el.clientWidth,
  516 |       content: el.scrollWidth,
  517 |     }));
  518 |     if (scrollSize.content > scrollSize.width) {
  519 |       await page.keyboard.press("ArrowRight");
  520 |       await expect
  521 |         .poll(() => tableRegion.evaluate((el) => el.scrollLeft))
  522 |         .toBeGreaterThan(0);
  523 |     }
  524 |     await testInfo.attach(`table-keyboard-${width}`, {
  525 |       body: JSON.stringify({
  526 |         viewport: width,
  527 |         ...scrollSize,
  528 |         focused: true,
  529 |         scrollLeft: await tableRegion.evaluate((el) => el.scrollLeft),
  530 |       }),
  531 |       contentType: "application/json",
  532 |     });
  533 |     await page.screenshot({
  534 |       path: testInfo.outputPath(`recorded-filter-${width}.png`),
  535 |       fullPage: true,
  536 |     });
  537 |     await reset();
  538 |     await page
  539 |       .getByRole("tab", { name: "Events & logs", exact: false })
  540 |       .click();
  541 |     await expect(page.locator(".event-row")).toHaveCount(200);
  542 |     await expect(
  543 |       page.locator(`[data-event-id="${fixture.events.hugeBefore}"] time`),
  544 |     ).toHaveAttribute("datetime", "2026-01-01T00:00:00.250000Z");
  545 |     await expect(
  546 |       page.locator(`[data-event-id="${fixture.events.unknownReceipt}"] time`),
  547 |     ).not.toHaveAttribute("datetime");
  548 |     await expect(
  549 |       page.locator(`[data-event-id="${fixture.events.unknownReceipt}"] time`),
  550 |     ).toContainText("Receipt time unavailable");
  551 |     await page
  552 |       .getByLabel("Emitter provider", { exact: true })
  553 |       .selectOption("fixture.late");
  554 |     await page.getByLabel("Severity", { exact: true }).selectOption("error");
  555 |     await apply();
  556 |     await expect(page.locator(".event-row")).toHaveCount(1);
  557 |     await expect(
  558 |       page.locator(`[data-event-id="${fixture.events.lateLog}"]`),
  559 |     ).toBeVisible();
  560 |     await page.getByLabel("Severity", { exact: true }).selectOption("");
  561 |     await reset();
  562 |     await expect(page.locator(".event-row")).toHaveCount(200);
  563 |     await page.getByRole("tab", { name: "Observations", exact: false }).click();
  564 |     if (
  565 |       await page.getByRole("button", { name: "Plot view", exact: true }).count()
  566 |     )
  567 |       await page
  568 |         .getByRole("button", { name: "Plot view", exact: true })
  569 |         .click();
  570 |   }
  571 |   expect(writes).toEqual([]);
  572 |   const detail = await page.evaluate(
  573 |     async (id) => fetch(`/api/v1/runs/${id}`).then((r) => r.json()),
  574 |     fixture.runId,
  575 |   );
  576 |   expect(detail.evidenceScope).toBe("recorded_fixture");
  577 |   expect(detail.capabilities).toEqual([]);
  578 | });
  579 |
  580 | test("evidence filters: incompatible time resolution and numeric units remain table-only", async ({
  581 |   page,
  582 | }, testInfo) => {
  583 |   test.setTimeout(90000);
  584 |   await connectStudio(page, testInfo);
  585 |   const made = await ownedRun(page, "Incompatible display metadata fixture");
  586 |   await expect
  587 |     .poll(async () =>
  588 |       page.evaluate(
  589 |         async (id) =>
  590 |           (await fetch(`/api/v1/runs/${id}`).then((r) => r.json())).state,
  591 |         made.runId,
  592 |       ),
  593 |     )
> 594 |     .toBe("stopped");
      |      ^ Error: expect(received).toBe(expected) // Object.is equality
  595 |   let mismatch: "resolution" | "units" = "resolution";
  596 |   await page.route(
  597 |     `**/api/v1/runs/${made.runId}/observations*`,
  598 |     async (route) => {
  599 |       const response = await route.fetch();
  600 |       await route.fulfill({
  601 |         response,
  602 |         json: {
  603 |           projectionVersion: "1.0",
  604 |           integrity: "fixture",
  605 |           evidenceScope: "browser_response_fixture",
  606 |           facets: { clockDomains: ["fixture-clock"] },
  607 |           items: [
  608 |             {
  609 |               eventId: "fixture-a",
  610 |               sourceTime: {
  611 |                 tick: "1",
  612 |                 clockDomain: "fixture-clock",
  613 |                 resolution: "nanosecond",
  614 |               },
  615 |               values: { value: 0 },
  616 |               units: { value: "V" },
  617 |             },
  618 |             {
  619 |               eventId: "fixture-b",
  620 |               sourceTime: {
  621 |                 tick: "2",
  622 |                 clockDomain: "fixture-clock",
  623 |                 resolution:
  624 |                   mismatch === "resolution" ? "microsecond" : "nanosecond",
  625 |               },
  626 |               values: { value: 1 },
  627 |               units: { value: mismatch === "units" ? "mV" : "V" },
  628 |             },
  629 |           ],
  630 |           gaps: [],
  631 |         },
  632 |       });
  633 |     },
  634 |   );
  635 |   await showRun(page, made.project.projectId, made.runId);
  636 |   await expect(
  637 |     page.getByText(
  638 |       "Original source resolutions differ; no alignment is assumed",
  639 |       { exact: true },
  640 |     ),
  641 |   ).toBeVisible();
  642 |   await expect(
  643 |     page.getByRole("img", { name: /Recorded observation chart/ }),
  644 |   ).toHaveCount(0);
  645 |   await expect(page.locator("[data-observation-id]")).toHaveCount(2);
  646 |   mismatch = "units";
  647 |   await page.getByRole("button", { name: "Refresh", exact: true }).click();
  648 |   await expect(
  649 |     page.getByText("Numeric quantity units differ; use the exact table", {
  650 |       exact: true,
  651 |     }),
  652 |   ).toBeVisible();
  653 |   await expect(
  654 |     page.getByRole("img", { name: /Recorded observation chart/ }),
  655 |   ).toHaveCount(0);
  656 |   await expect(page.locator("[data-observation-id]")).toHaveCount(2);
  657 | });
  658 |
  659 | test("evidence filters: live buffer remains filterable after an aborted retained read", async ({
  660 |   page,
  661 | }, testInfo) => {
  662 |   test.setTimeout(90000);
  663 |   await connectStudio(page, testInfo);
  664 |   const made = await ownedRun(page, "Live delivery read isolation");
  665 |   await expect
  666 |     .poll(async () =>
  667 |       page.evaluate(
  668 |         async (id) =>
  669 |           (await fetch(`/api/v1/runs/${id}`).then((r) => r.json())).state,
  670 |         made.runId,
  671 |       ),
  672 |     )
  673 |     .toBe("stopped");
  674 |   let release!: () => void, reached!: () => void;
  675 |   const gate = new Promise<void>((r) => (release = r)),
  676 |     waiting = new Promise<void>((r) => (reached = r));
  677 |   await page.route(`**/api/v1/runs/${made.runId}/history*`, async (route) => {
  678 |     const response = await route.fetch();
  679 |     reached();
  680 |     await gate;
  681 |     try {
  682 |       await route.fulfill({ response });
  683 |     } catch {
  684 |       /* cancelled obsolete retained read */
  685 |     }
  686 |   });
  687 |   await showRun(page, made.project.projectId, made.runId);
  688 |   await page.getByRole("tab", { name: "Events & logs", exact: false }).click();
  689 |   await waiting;
  690 |   await page
  691 |     .getByRole("button", { name: "Live buffer · at most 200", exact: true })
  692 |     .click();
  693 |   try {
  694 |     await expect(
```
