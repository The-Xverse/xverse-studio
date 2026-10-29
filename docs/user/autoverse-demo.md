# Run the Autoverse demo from Studio

Studio can load the complete Autoverse System, start its existing Linux components,
and drive the simulated vehicle from the browser. The installed provider is a
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
3. In Results, select **Enable browser driver**. Raising Throttle releases Brake.
   Use the sliders, or focus the keyboard pad for W/S/A/D and Space. The simulator
   camera opens as a native window. Keep the browser focused while driving.
4. Use **Coast / release pedals**, then **Engage cruise** once observed speed is at
   least 10 km/h and forward mode is observed. Use the cruise speed buttons and
   inspect the separately reported target speed and controller engagement.
5. **Release driver and brake** relinquishes input. Lost browser input expires the
   0.75-second lease and requests zero throttle, braking and cruise disengagement.
   These requests are separate from the observed vehicle response. Browser loss
   does not stop the demo lifecycle. Select **Stop** to release the whole owned stack.

The **Android digital cluster** link opens Cuttlefish's existing local HTTPS viewer.
Its local certificate may require the normal browser exception. If the app uses a
different router, use its gear/settings screen to select **client (router)** and the
existing emulator's host gateway on port 7447, then Save and restart the app. The
provider opens Zenoh on loopback and that existing emulator gateway, rather than
all network interfaces. Existing Android preferences are preserved.

Commands are capability checked in the backend. Cruise/reverse requests require
fresh compatible observations. The browser displays unknown or stale data explicitly;
acceptance of an input is not an acknowledgement from the vehicle. Simulation timing
is owned by the existing vehicle client's public synchronous option with a fixed
0.05-second step. The reported clock signal is elapsed seconds; its installed metadata
incorrectly describes frame-delta milliseconds, and Studio retains that conflict.
No mapping to host time, deterministic replay, native X-COM, physical effects or
Argus admission is claimed.

A changed installation, occupied port, active container, conflicting driver lease or
unrecognized middleware working directory blocks operation with a diagnostic. Restore
the admitted installation or resolve its reported conflict, then preflight again.
Studio stops only the processes and exact container instances it started. Middleware
scratch is retained and can be reinitialized by the next run only while its recorded
ownership and contents still match. Unknown resources are reported rather than killed.
