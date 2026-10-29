# ADR-0033: Complete Autoverse integration through an owned native adapter

Status: implementation in progress. The user requested loading, starting/stopping
the complete Autoverse demo and browser driving/cruise controls. No complete-stack
or vehicle-control acceptance is claimed from the current control/transport checks.
This applies the existing provider, XDL and lifecycle contracts without regenerating
the plan or changing task IDs. Previous unrelated implementation work is preserved.

The inspected Autoverse supervisor selects CARLA, the Zenoh VCU, the Zenoh–SOME/IP
bridge, S-CORE cruise control, manual inputs, the virtual vehicle and Android
Cuttlefish. The separately required Zenoh router is a support service. The supplied
`run_autoverse.py` explains the demo; it does not require Studio to execute global
cleanup. That runner and `automate.py` terminate processes by patterns or ports and
the latter reads wheel devices. Studio instead needs an ownership-aware wrapper
around existing public component commands and exact registered container IDs.
No Autoverse/companion source, production algorithm or configuration is modified.

The logical vehicle, VCU and communication gateway are native System Devices,
realized respectively as simulated/virtual assets. S-CORE, the cluster application
and browser input are software ComponentInstances. Role, realization and placement
remain separate. All communication routes stay in canonical XDL; graph-library
layout is not an executable definition. The compiler's component dependency order
is a startup plan, not a solver or a reason to invent a unit delay in this real
asynchronous communication system. The external-runtime declaration records that
the actual provider owns its feedback behavior. Native X-COM integration, physical
coupling and a coupled solver are not claimed by these Zenoh/SOME/IP routes.

The packaged integration-contract JSON is an actual content-addressed configuration
artifact. It is not a substitute identity for a CARLA binary, container image or
application source. Those require separately pinned native installation identities,
fresh preflight and independent effective-input checks before launch. The generic
`io.xverse.studio.native-runtime` Profile declares that boundary and a bounded session
duration. Installing or selecting its schema confers no runtime authority. The
experiment-lite plan remains declared intent; its fixed seed explicitly supplies
no external-runtime determinism claim. Edits outside the exact supported mapping
must block execution instead of being silently ignored.

Studio replaces the manual input publisher with a browser input surface using the
existing public signal topics, types and bounds. It does not run a second publisher
that would overwrite browser inputs. Throttle/brake/steer are a full bounded analog
state; cruise/reverse are explicit desired requests, and speed increments are
one-shot requests. Sequence retry cannot renew a lease or repeat a delta request.
The driver lease is 750ms. Expiry requests zero throttle/steering, braking and cruise
disengagement, preserving gear selection. These are requests to a virtual controller,
not physical safety guarantees or acknowledgements of vehicle application.

The native SDK adapter uses the already provisioned component interpreter and the
public Eclipse Zenoh API. Only a fixed loopback endpoint and closed stdio protocol
are supported. Input lines, output buffers and latest telemetry are bounded;
nonblocking output preserves watchdog progress with a slow consumer. Publication
receipts remain distinct from observed VCU/controller/vehicle state. Commands are
not arbitrary project strings. Missing or stale observations remain unknown/stale;
VCU command topics are labelled commands rather than applied actuator effects.
The installed vehicle clock publisher supplies elapsed seconds despite conflicting
frame-delta metadata; Studio retains that conflict and supplies no absolute clock mapping.
Host receipt age never manufactures simulation time or synchronized source ticks.

The public connection timeout and discovery configuration follows the official
[Zenoh configuration](https://github.com/eclipse-zenoh/zenoh/blob/main/DEFAULT_CONFIG.json5)
and [timeout documentation](https://zenoh.io/blog/2024-04-30-zenoh-electrode/).
Actual native verification uses the installed SDK and router; documentation alone
does not prove compatibility. Its observer-generated telemetry is explicitly a
fixture over real transport, not actual CARLA or S-CORE observations.

The native installation/preflight, exact process/container ownership, complete startup
and shutdown, authenticated backend controls, fenced browser driver ownership and
browser verification of real vehicle and cruise responses are implemented and have
passed the scoped Linux workflow. Broader milestone and cross-host acceptance remain open. Docker/VM/GPU requirements belong to this Linux
provider, never to Studio core operation. Native Windows remains independently held.
The existing user preview remains isolated while implementation continues.

Native verification amendment: complete startup and orderly stop have executed on
Linux. The first two browser driving attempts failed: published throttle and the
VCU command changed, but reported speed remained zero. A subsequent independent
CARLA client could not obtain a fresh world tick. Retain these failures; startup
and bus publication do not establish actual driving. The provider will use the
existing vehicle client's documented `--sync` option so that this owned client
explicitly advances the simulator at its public fixed 0.05-second step. This is an
explicit native execution choice, not a clock mapping, coupling solver or added
unit delay. No production source is changed. The default traffic-manager port is
also checked before starting that public option.

The installed clock publisher actually emits CARLA elapsed seconds, and the
SOME/IP mapping scales those seconds to milliseconds. Its signal metadata says
frame-delta milliseconds. Preserve that conflict and label the observed raw
interface `reportedElapsedSeconds`; no absolute mapping to host time is inferred.
The earlier description of this interface as a measured frame delta was incorrect.
