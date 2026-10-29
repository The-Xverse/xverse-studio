"""Evidence-linked diagnostic explanations; no cause is stated unless evidence reports it.

Every finding separates observed facts (each with evidence references), consequences
inferred only from those facts, unconfirmed hypotheses, explicit unknowns and next
actions from a closed registry. Explanations are derived projections: they never
change runs, operations, preflights or original evidence.
"""

import time

EXPLANATION_VERSION = "1.0"
MAX_FINDINGS = 64
MAX_REFS = 8

# Closed class registry: NFR-011 classes plus the FR-019/AC-011 run cases.
CLASSES = (
    "invalid_model",
    "unsupported_capability",
    "missing_artifact",
    "stale_plan",
    "incompatible_time_mapping",
    "resource_limit",
    "authority_unavailable",
    "readiness_unknown",
    "process_exit",
    "lost_connection",
    "failed_cleanup",
    "unavailable_evidence",
    "telemetry_gap",
    "observation_conflict",
    "command_failure",
    "no_traffic",
    "liveness_only",
)

# Closed next-action registry; the browser offers only those it can perform.
ACTIONS = {
    "recheck_preflight": "Recheck readiness to freeze a fresh plan.",
    "open_source_diagnostics": "Open the authoritative source diagnostics.",
    "select_admitted_provider": "Select an admitted compatible provider or template.",
    "register_artifact_identity": "Supply admitted exact artifact identities.",
    "declare_clock_mapping": "Declare an admitted clock or mapping before execution.",
    "wait_for_capacity": "Wait for an active run to finish, or reduce the requested budget.",
    "inspect_events": "Inspect the referenced retained events and logs.",
    "reconcile_ownership": "Reconcile ownership from the verified backend record.",
    "follow_recovery_guide": "Follow the recovery guide's native shutdown procedure.",
    "refresh_evidence": "Refresh the evidence read; do not treat it as a new run.",
    "review_observer_configuration": "Review the observer's declared source and expected interval.",
}

READINESS_CLASSES = {
    "model": ("invalid_model", "MODEL_INVALID", ["open_source_diagnostics"]),
    "provider": (
        "unsupported_capability",
        "PROVIDER_UNAVAILABLE",
        ["select_admitted_provider"],
    ),
    "capabilities": (
        "unsupported_capability",
        "CAPABILITY_UNSUPPORTED",
        ["select_admitted_provider"],
    ),
    "artifacts": (
        "missing_artifact",
        "ARTIFACT_UNAVAILABLE",
        ["register_artifact_identity", "recheck_preflight"],
    ),
    "clocks": (
        "incompatible_time_mapping",
        "CLOCK_MAPPING_UNAVAILABLE",
        ["declare_clock_mapping", "recheck_preflight"],
    ),
    "resources": (
        "resource_limit",
        "LIMIT_EXCEEDED",
        ["wait_for_capacity", "recheck_preflight"],
    ),
    "authority": (
        "authority_unavailable",
        "AUTHORITY_UNAVAILABLE",
        ["recheck_preflight"],
    ),
}
POSITIVE = {"available", "valid", "compatible", "ready", "not_required"}
# Codes that report a missing fact rather than a found problem.
UNESTABLISHED_CODES = {"LIMITS_UNKNOWN"}


class _Finding:
    def __init__(self, code, cls, severity, title, element_refs=()):
        assert cls in CLASSES
        self.body = {
            "code": code,
            "class": cls,
            "severity": severity,
            "title": title,
            "elementRefs": list(element_refs)[:MAX_REFS],
            "facts": [],
            "consequences": [],
            "hypotheses": [],
            "unknowns": [],
            "nextActions": [],
        }

    def fact(self, statement, evidence):
        fid = "f%d" % (len(self.body["facts"]) + 1)
        self.body["facts"].append(
            {
                "id": fid,
                "statement": statement,
                "evidence": list(evidence)[:MAX_REFS],
                "evidenceOmitted": max(0, len(evidence) - MAX_REFS),
            }
        )
        return fid

    def consequence(self, statement, basis):
        # Inference is admissible only from facts recorded in this finding.
        assert basis and all(b in {f["id"] for f in self.body["facts"]} for b in basis)
        self.body["consequences"].append({"statement": statement, "basis": basis})

    def hypothesis(self, statement, basis=()):
        self.body["hypotheses"].append(
            {"statement": statement, "status": "unconfirmed", "basis": list(basis)}
        )

    def unknown(self, statement):
        self.body["unknowns"].append(statement)

    def actions(self, *names):
        for name in names:
            self.body["nextActions"].append({"action": name, "label": ACTIONS[name]})


def _event_ref(record):
    return {
        "kind": "event",
        "eventId": record.get("eventId"),
        "sequence": record.get("sequence"),
        "type": record.get("type"),
    }


def _run_ref(run, field):
    return {
        "kind": "run",
        "runId": run.get("runId"),
        "field": field,
        "value": run.get(field),
    }


def _explanation(subject, findings, evaluated, **extra):
    complete = len(findings) <= MAX_FINDINGS
    return {
        "explanationVersion": EXPLANATION_VERSION,
        "subject": subject,
        "rootCause": "not_inferred",
        "evaluatedClasses": list(evaluated),
        "findings": [f.body for f in findings[:MAX_FINDINGS]],
        "findingCount": len(findings),
        "findingsComplete": complete,
        **extra,
    }


def _invalid_model(preflight, record, status, evidence):
    finding = _Finding(
        (record.get("diagnosticCodes") or ["MODEL_INVALID"])[0],
        "invalid_model",
        "error",
        record.get("message") or "The model did not validate.",
        record.get("elementRefs") or [],
    )
    fid = finding.fact(f"Preflight recorded model readiness as {status}.", [evidence])
    sources = []
    for d in preflight.get("diagnostics") or []:
        location = d.get("location") if isinstance(d.get("location"), dict) else {}
        if d.get("severity") == "error" and (location or d.get("pointer")):
            sources.append(
                {
                    "kind": "source_diagnostic",
                    "code": d.get("code"),
                    "documentId": location.get("documentId"),
                    "line": location.get("line"),
                    "column": location.get("column"),
                    "pointer": d.get("pointer"),
                    "elementRef": d.get("elementRef"),
                }
            )
    basis = [fid]
    if sources:
        basis.append(
            finding.fact("The authoritative validator reported source errors.", sources)
        )
    else:
        finding.unknown("The validator reported no source location for this failure.")
    finding.consequence(
        "Start is blocked: no executable plan exists for invalid source.", basis
    )
    finding.actions("open_source_diagnostics", "recheck_preflight")
    return finding


def explain_preflight(preflight, *, current_revision, capability_digest, now=None):
    """Explain why a frozen preflight cannot start, from its recorded readiness."""
    now = time.time() if now is None else now
    pid = preflight.get("preflightId")
    readiness = preflight.get("readiness") or {}
    findings = []
    unestablished = []
    model_invalid = (readiness.get("model") or {}).get("status") == "invalid"
    derived_target = None
    for name, record in readiness.items():
        if not isinstance(record, dict) or record.get("status") in POSITIVE:
            continue
        status = record.get("status")
        codes = record.get("diagnosticCodes") or []
        evidence = {
            "kind": "preflight",
            "preflightId": pid,
            "dimension": name,
            "status": status,
            "diagnosticCodes": codes,
        }
        if name == "target":
            # Target readiness is derived from the other dimensions.
            derived_target = (name, status, record, evidence)
            continue
        if name == "model":
            findings.append(_invalid_model(preflight, record, status, evidence))
            continue
        # A specific class needs its own diagnostic and a compiled plan to evaluate;
        # codeless or downstream-of-invalid-model facts are unestablished.
        if (
            model_invalid
            or not codes
            or name not in READINESS_CLASSES
            or codes[0] in UNESTABLISHED_CODES
        ):
            unestablished.append((name, status, record, evidence))
            continue
        cls, _, actions = READINESS_CLASSES[name]
        finding = _Finding(
            codes[0],
            cls,
            "warning" if status == "unknown" else "error",
            record.get("message") or f"{name} readiness is {status}.",
            record.get("elementRefs") or [],
        )
        fid = finding.fact(
            f"Preflight recorded {name} readiness as {status}.", [evidence]
        )
        finding.consequence(
            "Start is blocked: this snapshot lacks positive admission for this dimension.",
            [fid],
        )
        if status == "unknown":
            finding.unknown(
                "The fact is not established; unknown is neither failure nor admission."
            )
        finding.actions(*actions)
        findings.append(finding)
    if derived_target and not findings and not unestablished:
        unestablished.append(derived_target)
    if unestablished:
        finding = _Finding(
            "READINESS_UNESTABLISHED",
            "readiness_unknown",
            "warning",
            "Some readiness facts were not established.",
        )
        ids = [
            finding.fact(
                f"Preflight recorded {name} readiness as {status}"
                + (f": {record['message']}" if record.get("message") else "."),
                [evidence],
            )
            for name, status, record, evidence in unestablished
        ]
        finding.consequence(
            "Start is blocked until these facts are positively established.", ids
        )
        if model_invalid:
            finding.unknown(
                "These dimensions depend on a compiled plan, which the invalid model did not produce."
            )
        finding.unknown(
            "The actual state of each unestablished dimension; unknown is not failure."
        )
        finding.actions("recheck_preflight")
        findings.append(finding)
    stale = []
    expires = preflight.get("expiresAt")
    if not isinstance(expires, (int, float)):
        stale.append(("The preflight reported no usable expiry.", "expiresAt", expires))
    elif expires <= now:
        stale.append(("The frozen preflight has expired.", "expiresAt", expires))
    if preflight.get("revision") != current_revision:
        stale.append(
            (
                "The project revision changed after this preflight froze its inputs.",
                "revision",
                {"frozen": preflight.get("revision"), "current": current_revision},
            )
        )
    if preflight.get("capabilityDigest") != capability_digest:
        stale.append(
            (
                "Provider capabilities changed after this preflight.",
                "capabilityDigest",
                {
                    "frozen": preflight.get("capabilityDigest"),
                    "current": capability_digest,
                },
            )
        )
    if stale:
        finding = _Finding(
            "PLAN_STALE",
            "stale_plan",
            "error",
            "The frozen plan no longer describes current inputs.",
        )
        ids = [
            finding.fact(
                statement,
                [
                    {
                        "kind": "preflight",
                        "preflightId": pid,
                        "field": field,
                        "value": value,
                    }
                ],
            )
            for statement, field, value in stale
        ]
        finding.consequence(
            "Start would reject this preflight; a fresh preflight is required.", ids
        )
        finding.actions("recheck_preflight")
        findings.append(finding)
    return _explanation(
        {
            "kind": "preflight",
            "preflightId": pid,
            "snapshotId": preflight.get("snapshotId"),
            "status": preflight.get("status"),
        },
        findings,
        [
            "invalid_model",
            "unsupported_capability",
            "missing_artifact",
            "incompatible_time_mapping",
            "resource_limit",
            "authority_unavailable",
            "readiness_unknown",
            "stale_plan",
        ],
    )


def _source_clock(record):
    source_time = record.get("sourceTime")
    if not isinstance(source_time, dict):
        return None, "missing"
    domain, tick = source_time.get("clockDomain"), source_time.get("tick")
    if not isinstance(domain, str) or not isinstance(tick, str):
        return None, "malformed"
    return domain, "known"


# No model workload start was established; a provider process may have rejected it.
NOT_STARTED = {"PREPARATION_FAILED", "EVIDENCE_OPEN_FAILED", "LAUNCH_FAILED", "EFFECTIVE_INPUT_MISMATCH"}
ACTIVE_STATES = {"requested", "preparing", "running", "stopping"}


def explain_run(
    run,
    records,
    integrity,
    *,
    expected_observers=(),
    operations=(),
    element_refs=(),
):
    """Explain a run's lifecycle, evidence and observations from retained evidence only."""
    findings = []
    state = run.get("state")
    reason = run.get("reason")
    refs = list(element_refs) or run.get("elementRefs") or []
    not_started = state == "failed" and reason in NOT_STARTED and not records
    last = records[-1] if records else None
    errors = [
        r
        for r in records
        if r.get("type") == "log.appended"
        and (r.get("payload") or {}).get("severity") == "error"
    ]
    if not_started:
        finding = _Finding(
            reason,
            "process_exit",
            "error",
            "The owned workload did not start.",
            refs,
        )
        f1 = finding.fact(
            "The run failed before execution and retained no events.",
            [_run_ref(run, "state"), _run_ref(run, "reason")],
        )
        finding.consequence("No execution took place, so no results exist.", [f1])
        if reason == "EFFECTIVE_INPUT_MISMATCH":
            finding.fact(
                "The workload reported that its effective inputs did not match the frozen snapshot.",
                [_run_ref(run, "reason")],
            )
        elif reason == "EVIDENCE_OPEN_FAILED":
            finding.fact(
                "The provider could not create its canonical journal before starting the workload.",
                [_run_ref(run, "reason")],
            )
            finding.unknown("The storage or access condition that prevented journal creation.")
            finding.actions("follow_recovery_guide")
        elif reason == "PREPARATION_FAILED":
            finding.fact(
                "The backend reported a preparation I/O failure before attempting native launch.",
                [_run_ref(run, "reason")],
            )
            finding.unknown("The storage or access condition that caused preparation to fail.")
            finding.actions("follow_recovery_guide")
        else:
            finding.unknown("Why the launch failed is not established.")
        finding.actions("recheck_preflight")
        findings.append(finding)
    # Process exit: the outcome is observed; its cause is not inferred.
    elif state == "failed":
        finding = _Finding(
            reason or "PROCESS_EXIT_UNEXPLAINED",
            "process_exit",
            "error",
            "The owned workload ended in failure.",
            refs,
        )
        f1 = finding.fact(
            "The run's recorded lifecycle state is failed.",
            [_run_ref(run, "state"), _run_ref(run, "reason")],
        )
        basis = [f1]
        if errors:
            basis.append(
                finding.fact(
                    "The workload recorded error log entries.",
                    [_event_ref(r) for r in errors],
                )
            )
        if last:
            basis.append(finding.fact("The last retained event.", [_event_ref(last)]))
        finding.consequence(
            "Execution ended before its declared completion; nothing after the last retained event was recorded.",
            basis,
        )
        finding.unknown("The root cause is not established by the retained evidence.")
        finding.actions("inspect_events")
        findings.append(finding)
    # Lost ownership: whether the workload still executes is unknown.
    if state == "unknown":
        finding = _Finding(
            reason or "OWNERSHIP_UNKNOWN",
            "lost_connection",
            "warning",
            "Studio lost verified ownership of the workload.",
            refs,
        )
        f1 = finding.fact(
            "The backend could not confirm the recorded owned process.",
            [_run_ref(run, "state"), _run_ref(run, "reason")],
        )
        basis = [f1]
        if last:
            basis.append(finding.fact("The last retained event.", [_event_ref(last)]))
        finding.consequence(
            "Controls are withheld and no result after the last retained event is available.",
            basis,
        )
        finding.hypothesis("The workload may have exited.", [f1])
        finding.hypothesis(
            "The workload may still be executing without an ownership proof.", [f1]
        )
        finding.unknown("Whether the workload is still executing.")
        finding.unknown("The cleanup outcome of owned resources.")
        finding.actions(
            "reconcile_ownership", "follow_recovery_guide", "inspect_events"
        )
        findings.append(finding)
    cleanup = run.get("cleanup")
    cleanup = cleanup.get("status") if isinstance(cleanup, dict) else cleanup
    if cleanup in ("failed", "partial", "unknown") and state in (
        "stopped",
        "failed",
        "unknown",
    ):
        finding = _Finding(
            "CLEANUP_" + cleanup.upper(),
            "failed_cleanup",
            "error" if cleanup == "failed" else "warning",
            f"Owned-resource cleanup is {cleanup}.",
            refs,
        )
        evidence = [_run_ref(run, "cleanup")] + [
            _event_ref(r) for r in records if r.get("type") == "cleanup.updated"
        ]
        f1 = finding.fact(f"The recorded cleanup outcome is {cleanup}.", evidence)
        resources = run.get("cleanupResources")
        if isinstance(resources, list):
            for resource in resources[:1]:
                if isinstance(resource, dict) and resource.get("kind") == "temporary-directory":
                    finding.fact(
                        "The worker could not confirm release of its temporary directory: " + str(resource.get("resourceId", "unavailable")),
                        [_run_ref(run, "cleanupResources")],
                    )
        finding.consequence(
            "Owned resources may remain allocated; a replacement run could contend for them.",
            [f1],
        )
        if cleanup != "failed":
            finding.unknown("Whether every owned resource was released.")
        finding.actions("reconcile_ownership", "follow_recovery_guide")
        findings.append(finding)
    # Evidence integrity and completeness are independent of the lifecycle outcome.
    evidence_status = run.get("evidence")
    if not_started:
        finding = _Finding(
            "EVIDENCE_NOT_PRODUCED",
            "unavailable_evidence",
            "info",
            "No evidence was produced because the workload did not start.",
        )
        f1 = finding.fact(
            "No evidence journal exists for this run.",
            [
                {"kind": "projection", "name": "readerIntegrity", "value": integrity},
                _run_ref(run, "evidence"),
            ],
        )
        finding.consequence("There are no observations to assess.", [f1])
        findings.append(finding)
    elif state in ACTIVE_STATES and integrity == "unavailable":
        # An active journal may not exist yet or may be mid-append; that is not loss.
        finding = _Finding(
            "EVIDENCE_NOT_YET_READABLE",
            "unavailable_evidence",
            "info",
            "The active run's evidence could not be read at this moment.",
        )
        finding.fact(
            f"Reader integrity is unavailable while the run is {state}.",
            [
                {"kind": "projection", "name": "readerIntegrity", "value": integrity},
                _run_ref(run, "state"),
            ],
        )
        finding.unknown("The current evidence content; this is not evidence loss.")
        finding.actions("refresh_evidence")
        findings.append(finding)
    elif integrity in ("unavailable", "invalid") or evidence_status in (
        "partial",
        "unavailable",
        "invalid",
    ):
        code = (
            "EVIDENCE_INVALID"
            if "invalid" in (integrity, evidence_status)
            else "EVIDENCE_UNAVAILABLE"
            if "unavailable" in (integrity, evidence_status)
            else "EVIDENCE_PARTIAL"
        )
        finding = _Finding(
            code,
            "unavailable_evidence",
            "error" if code != "EVIDENCE_PARTIAL" else "warning",
            "The retained evidence is not complete and valid.",
        )
        f1 = finding.fact(
            f"Reader integrity is {integrity}; recorded evidence status is {evidence_status}.",
            [
                {"kind": "projection", "name": "readerIntegrity", "value": integrity},
                _run_ref(run, "evidence"),
            ],
        )
        if run.get("evidenceFailure") == "EVIDENCE_FINALIZATION_FAILED":
            finding.fact(
                "The worker reported an evidence finalization failure after its workload stopped.",
                [_run_ref(run, "evidenceFailure"), _run_ref(run, "cleanup")],
            )
        finding.consequence(
            "Assessments over this run cannot claim complete coverage.", [f1]
        )
        if integrity == "unavailable":
            finding.unknown(
                "The current evidence content; the source could not be acquired."
            )
            finding.actions("refresh_evidence")
        finding.actions("inspect_events")
        findings.append(finding)
    observations = [r for r in records if r.get("type") == "observation.available"]
    domains, missing, malformed = {}, [], []
    for record in observations:
        domain, status = _source_clock(record)
        if status == "known":
            domains.setdefault(domain, []).append(record)
        else:
            (missing if status == "missing" else malformed).append(record)
    if len(domains) > 1 or missing or malformed:
        finding = _Finding(
            "TIME_MAPPING_INCOMPATIBLE",
            "incompatible_time_mapping",
            "warning",
            "Observations cannot be placed on one admitted time axis.",
        )
        basis = []
        if len(domains) > 1:
            basis.append(
                finding.fact(
                    "Observations use %d clock domains: %s."
                    % (len(domains), ", ".join(sorted(domains))),
                    [_event_ref(rows[0]) for _, rows in sorted(domains.items())],
                )
            )
        if missing:
            basis.append(
                finding.fact(
                    "%d observation(s) carry no source time." % len(missing),
                    [_event_ref(r) for r in missing],
                )
            )
        if malformed:
            basis.append(
                finding.fact(
                    "%d observation(s) carry malformed source time." % len(malformed),
                    [_event_ref(r) for r in malformed],
                )
            )
        finding.consequence(
            "Records from different or unknown clocks are not ordered, aligned or compared by latency.",
            basis,
        )
        if len(domains) > 1:
            finding.unknown("The mapping between these clock domains.")
        finding.actions("declare_clock_mapping", "inspect_events")
        findings.append(finding)
    gaps = [r for r in records if r.get("type") == "observation.gap"]
    if gaps:
        finding = _Finding(
            "OBSERVATION_GAP",
            "telemetry_gap",
            "warning",
            "Collection declared missing observation intervals.",
        )
        f1 = finding.fact(
            "%d declared collection gap(s) were recorded." % len(gaps),
            [_event_ref(r) for r in gaps],
        )
        finding.consequence(
            "No continuous signal is drawn across a gap, and metrics over it are incomplete.",
            [f1],
        )
        finding.unknown("The values that were not collected during each gap.")
        finding.actions("inspect_events")
        findings.append(finding)
    faults = [r for r in records if r.get("type") == "fault.activation_observed"]
    if faults:
        finding = _Finding(
            "OBSERVATION_FAULT_OBSERVED",
            "observation_conflict",
            "warning",
            "The workload reported an observed fault activation.",
        )
        requested = [
            r for r in records if r.get("type") == "fault.activation_requested"
        ]
        if requested:
            # Context only: a request is not evidence that a fault occurred.
            finding.fact(
                "A fault activation was requested.",
                [_event_ref(r) for r in requested],
            )
        observed = finding.fact(
            "The workload reported an observed fault activation.",
            [_event_ref(r) for r in faults],
        )
        first = int(faults[0].get("sequence") or 0)
        diverged = [
            r
            for r in observations
            if int(r.get("sequence") or 0) > first
            and isinstance((r.get("payload") or {}).get("values"), dict)
            and "measured" in r["payload"]["values"]
            and r["payload"]["values"].get("measured")
            != r["payload"]["values"].get("value")
        ]
        if diverged:
            divergence = finding.fact(
                "%d later observation(s) report a measured value different from the model value."
                % len(diverged),
                [_event_ref(r) for r in diverged],
            )
            finding.consequence(
                "Those measurements do not reflect the modelled state.",
                [observed, divergence],
            )
        else:
            finding.unknown(
                "Whether any measurement was affected; no later observation diverges."
            )
        finding.actions("inspect_events")
        findings.append(finding)
    failed_commands = [r for r in records if r.get("type") == "command.failed"]
    unsettled = [
        op
        for op in operations
        if op.get("kind") in ("stop", "cancel")
        and op.get("status") in ("failed", "unknown")
        and op.get("operationId")
        not in {(r.get("payload") or {}).get("operationId") for r in failed_commands}
    ]
    if failed_commands or unsettled:
        finding = _Finding(
            "COMMAND_NOT_APPLIED",
            "command_failure",
            "warning",
            "An accepted control request did not demonstrably take effect.",
        )
        basis = []
        if failed_commands:
            basis.append(
                finding.fact(
                    "The workload recorded command.failed.",
                    [_event_ref(r) for r in failed_commands],
                )
            )
        for op in unsettled:
            basis.append(
                finding.fact(
                    f"Operation {op['operationId']} ({op.get('kind')}) is {op.get('status')}.",
                    [
                        {
                            "kind": "operation",
                            "operationId": op["operationId"],
                            "status": op.get("status"),
                            "code": op.get("code"),
                        }
                    ],
                )
            )
            if op.get("status") == "unknown":
                finding.unknown(f"Whether operation {op['operationId']} took effect.")
        finding.consequence(
            "Command acceptance is not execution; the lifecycle outcome is reported separately.",
            basis,
        )
        finding.actions("inspect_events")
        findings.append(finding)
    # Absence of traffic is ambiguous: it is reported as unobserved, never as failure.
    seen = {(r.get("payload") or {}).get("observerRef") for r in observations}
    for observer in expected_observers:
        if observer in seen or integrity in ("unavailable", "invalid"):
            continue
        finding = _Finding(
            "OBSERVER_UNOBSERVED",
            "no_traffic",
            "info",
            f"No observations were recorded for {observer}.",
        )
        f1 = finding.fact(
            f"The retained evidence contains no observation from {observer}.",
            [
                {
                    "kind": "projection",
                    "name": "observationsByObserver",
                    "observerRef": observer,
                    "value": 0,
                    "recordsExamined": len(records),
                }
            ],
        )
        finding.hypothesis("The observer may not be connected or producing data.", [f1])
        finding.hypothesis("No data may have been due in the recorded interval.", [f1])
        finding.unknown(
            "Whether traffic was expected; absence of traffic alone is not a failure."
        )
        finding.actions("review_observer_configuration", "inspect_events")
        findings.append(finding)
    # Liveness is not functional health.
    if (
        state in ("running", "stopping")
        and integrity not in ("unavailable", "invalid")
        and not observations
    ):
        finding = _Finding(
            "LIVENESS_ONLY",
            "liveness_only",
            "info",
            "The workload is live, but no functional observation has been recorded.",
            refs,
        )
        f1 = finding.fact(
            f"The owned process is reported {state}.", [_run_ref(run, "state")]
        )
        f2 = finding.fact(
            "No observation.available record is retained yet.",
            [
                {
                    "kind": "projection",
                    "name": "observationCount",
                    "value": 0,
                    "recordsExamined": len(records),
                }
            ],
        )
        finding.consequence(
            "Only liveness is established; functional health is not observed.", [f1, f2]
        )
        finding.unknown("Whether the workload is producing correct outputs.")
        finding.actions("refresh_evidence")
        findings.append(finding)
    return _explanation(
        {
            "kind": "run",
            "runId": run.get("runId"),
            "snapshotId": run.get("snapshotId"),
            "state": state,
            "stateVersion": run.get("stateVersion"),
        },
        findings,
        [
            "process_exit",
            "lost_connection",
            "failed_cleanup",
            "unavailable_evidence",
            "incompatible_time_mapping",
            "telemetry_gap",
            "observation_conflict",
            "command_failure",
            "no_traffic",
            "liveness_only",
        ],
        evidenceScope=run.get("evidenceScope", "unknown"),
        integrity=integrity,
        recordsExamined=len(records),
    )
