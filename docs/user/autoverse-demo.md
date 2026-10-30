# Run the Autoverse demo from Studio

Studio can load the complete Autoverse System, start its existing Linux components,
and open the original Pygame **Vehicle Manual Control** window on the Studio host desktop. The installed provider is a
prototype. Its Linux driving workflow has been exercised with real CARLA, Zenoh,
SOME/IP, S-CORE and Android; this does not close the product's broader acceptance gates.

The provider requires an existing working Autoverse installation, its three prepared
Docker containers and built S-CORE artifacts, the matching CARLA Python API/server,
Zenoh, ADB, an available graphical session and the existing Cuttlefish environment.
It does not download images, compile companion projects or reset Android data.
These dependencies belong to this Linux provider. Studio's ordinary reference and
authoring workflows remain independent of them. Native Windows demo execution is unavailable.

Start the native Studio launcher with an explicitly selected installation:

```text
xverse-studio --autoverse-root /path/to/autoverse --data-dir /path/to/private/studio-data --port 8878 --static-dir /path/to/studio-web/dist
```

Use a new private data directory for an initial test. The launcher enrolls exact
existing files, SDKs, container IDs, images and mounted build artifacts. All demo
components must be stopped for enrollment and preflight. Start Docker through your
normal host administration if it is stopped. Running the launcher without
`--autoverse-root` keeps the demo example inspectable and execution unavailable.

1. Open the launcher URL and sign in with the one-use token in its private
   `bootstrap.json` file. Select **Autoverse complete demo** from the example cards.
2. Choose **Preflight & run**, review the selected provider and frozen inputs,
   then select **Start frozen snapshot**. Component preparation appears in Results.
   Android boot can take several minutes. Stop and Cancel also work during preparation.
3. After Android finishes starting, the original **Vehicle Manual Control** Pygame
   window opens on the computer running Studio, alongside the vehicle camera.
   Focus **Vehicle Manual Control** to drive. W/Up accelerates, S/Down brakes,
   and A/D or Left/Right steers.
4. Release the accelerator and press C to toggle cruise control. Z decreases its
   target by 5 km/h; X increases it by 5 km/h. Q toggles reverse. These are the
   original demo's keyboard controls and controller behavior.
5. Select **Stop** in Studio to stop the complete owned stack. Closing the Pygame
   control window or pressing Escape also stops the demo. Browser refresh or loss
   does not release native keyboard input or stop the run; this mode uses the
   original manual controller rather than the browser's 0.75-second driver lease.

Check the selected project: an older project can still request browser controls.
The input mode is recorded in its Scenario, and refreshing Studio loads any newly
saved project revision. New examples select `native-pygame` in their canonical Scenario. Historical
`studio-browser` projects keep their recorded mode and browser controls. Create a
new example to select Pygame; existing run snapshots are never silently rewritten.
The Pygame process initializes display, fonts and keyboard only. Physical steering
wheel/joystick access is excluded. Studio's telemetry connection is observe-only
and publishes no driving commands, including during shutdown.

The **Android digital cluster** link opens Cuttlefish's existing local HTTPS viewer.
Its local certificate may require the normal browser exception. If the app uses a
different router, use its gear/settings screen to select **client (router)** and the
existing emulator's host gateway on port 7447, then Save and restart the app. The
provider opens Zenoh on loopback and that existing emulator gateway, rather than
all network interfaces. Existing Android preferences are preserved.

Studio lifecycle commands are capability checked in the backend. Browser driving
requests are rejected for native-window runs. Pygame retains the original manual
controller behavior; its requests remain separate from observed vehicle effects.
Studio displays missing or stale telemetry explicitly. Simulation timing
is owned by the existing vehicle client's public synchronous option with a fixed
0.05-second step. The reported clock signal is elapsed seconds; its installed metadata
incorrectly describes frame-delta milliseconds, and Studio retains that conflict.
The classic provider does not claim mapping to host time, deterministic replay,
native X-COM, physical effects or Argus admission. The separately enrolled platform
provider below supplies the actual Maestro/native-X-COM/Argus integration.

A changed installation, occupied port, active container, conflicting driver lease or
unrecognized middleware working directory blocks operation with a diagnostic. Restore
the admitted installation or resolve its reported conflict, then preflight again.
Studio stops only the processes and exact container instances it started. Middleware
scratch is retained and can be reinitialized by the next run only while its recorded
ownership and contents still match. Unknown resources are reported rather than killed.

## Follow one run across the X-Verse platform

Use the separately verified native bridge build and the admitted platform SDK:

```text
xverse-studio --autoverse-root /path/to/autoverse --autoverse-native-bridge /path/to/verified-native-build --data-dir /path/to/private/studio-data --port 8881 --static-dir /path/to/studio-web/dist
```

Choose **Autoverse with X-Verse platform**, then **Preflight & run** and **Start
frozen snapshot**. The same original Pygame window provides driving and cruise
controls. In **Results**, the three linked views show actual platform records:

| View | What to inspect |
|---|---|
| **Orchestration** | Maestro's per-binding prepare, start, readiness, Stop and reverse cleanup facts. |
| **Communications** | Native C++ X-COM ingress, sampled observations, route identities and original clocks. |
| **Evidence** | Argus's original records, recorded/assessed verdicts, integrity diagnostics and causal links. |

Use **Original cause**, **Correlated orchestration** and **Correlated communications**
to follow the selected record between views. **Shared run, plan and evidence identities**
shows their common binding. All three views use one immutable capture; **Refresh
all platform views** obtains a new capture, including after Stop. Paging and
selection refer to that capture rather than mixing changing live records.

While a run is active, enable **Follow live** for automatic updates with newest
records first. It reads a new shared capture2seconds after the previous read
finishes, pauses off-tab or when the browser is hidden, and retains the last capture
through read failures. The original capture time remains visible. Inspecting a record,
paging or using a causal link pauses following and pins that displayed capture.
After Stop it obtains the final capture and stops polling. Native evidence is
batched independently (at least2.5seconds in this provider), so updates have delay
and may coalesce samples; this is not a hard-real-time or every-message trace.

Eleven VCU boundary routes use the native bridge; three routes are sampled for
observability. Sample coalescing remains visible and can make Argus's verdict
**incomplete** even after successful Stop and released cleanup. Native counters,
transport gaps, clock mappings and external vehicle effects are separate facts.
Unknown upstream causes and absent simulator-clock mappings stay unknown.
The Evidence view exposes admitted Argus trace records; private provider stdout
is not relabelled as Argus evidence or exported into browser logs.

The platform owner survives successive runs in one backend. After owner loss,
claims remain fenced until the admitted host procedure in [platform recovery](platform-recovery.md)
verifies and explicitly retires eligible predecessors. Restarting does not recreate
old process handles, remove claims or upgrade an incomplete evidence verdict.

Classic browser-input projects also support the versioned, bounded
[driver-input-loss scenario](scenario-authoring.md#autoverse-browser-input-loss).
This is a bridge publication-lease fault; it is separate from Pygame controls and
from the platform provider's Maestro/native-X-COM/Argus integration.
