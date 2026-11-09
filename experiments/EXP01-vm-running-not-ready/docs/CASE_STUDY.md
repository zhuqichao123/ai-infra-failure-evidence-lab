# EXP01 — VM Running Does Not Mean Service Ready

**Technical failure case | Public, sanitized narrative | Release source v1.3**

**Evidence window:** November 2026; two recorded local runs.

**Evidence class:** controlled `SYNTHETIC` fault + `LOCAL-REPRODUCED` observations.

**Evidence availability:** Private originals preserved separately. **All bundled JSON examples are synthetic and were authored for public replay.**

## Executive summary

A Windows Hyper-V guest continued to report **Running**, SSH remained usable, and its systemd unit remained **Active**, while the application could not be reached at the client's expected HTTP endpoint (`TCP 8080 /readyz`). The operator had deliberately moved the test listener to TCP 8081; successful responses at that alternate port, combined with configuration and socket evidence, supported a specific **listener/expected-endpoint mismatch**. Returning the listener to 8080 restored external access. The behavior was recorded in a manual run (RUN-001) and a subsequent Ansible diagnostic run (RUN-002).

The practical lesson is that a chain of observations matters: VM power state → OS access → systemd process state → configured port → actual listening socket → local HTTP response → **external client HTTP transaction**. Each check answers a different question. The application used here was a dependency-free teaching service; its `/readyz` handler reports `ready=true` whenever the handler responds. This experiment therefore tested expected-endpoint availability, **not production-grade readiness semantics**.

## 1. Engineering question

Do `VM Running`, successful SSH access and `systemd Active` prove that an application is reachable at the endpoint required by its clients? **No, not in the controlled failure state examined here.**

## 2. Evidence class

The wrong-port change was intentionally injected: **`SYNTHETIC`**. System, socket and HTTP behavior was observed in a disposable local lab: **`LOCAL-REPRODUCED`**. The underlying observed raw runs and integrity manifests are retained privately, not republished here. The files in `fixtures/` are standalone synthetic test examples, not anonymized evidence exports.

## 3. Environment and versions

The recorded setup was Windows 11 Pro with Hyper-V hosting a disposable Rocky Linux 9.8 target. A separate Rocky Linux 9.8 controller used Ansible Core 2.14.18 and Python 3.9.25 to collect and interpret state. The application was a minimal Python 3 HTTP service managed by `failurelab-exp01.service`. The Windows client independently observed VM state, SSH, TCP and HTTP behavior. These versions reflect recorded lab information; this public package is not a complete Hyper-V provisioning receipt.

## 4. Infrastructure creation method

The original lab used separate, disposable Rocky clones and a generalized golden-image/NoCloud workflow. The reported VHDX disks were independent dynamic disks rather than differencing children. Full golden-image build artifacts and machine-level provisioning receipts are not part of this public candidate. For a fresh reproduction, use your own authorized isolated VM instead of trying to reconstruct the private source infrastructure.

## 5. Failure scenario

The test client's contract was `GET http://<test-target>:8080/readyz`, requiring HTTP 200 with JSON `ready=true`. Initially the service configured and listened on 8080. The operator explicitly changed `LISTEN_PORT=8080` to `LISTEN_PORT=8081` and restarted the test unit. The VM stayed up; the service worked on 8081; the expected 8080 endpoint stopped responding. Recovery restored 8080.

## 6. Reproduction or replay steps

For a **pure offline replay**, run the provided Python evaluator against the three **synthetic** fixtures and execute the unit tests. See [REPLAY.md](REPLAY.md). That validates the supplied classifier against a known signal pattern, not the historical VMs.

For a **new live lab reproduction**, provision a disposable Rocky VM, install the test service from `linux/`, establish an external baseline, separately invoke `01-inject-wrong-port.sh`, collect diagnostics through Ansible, independently verify external failure, invoke `02-recover-expected-port.sh`, then verify the expected external endpoint and re-collect diagnostics. Scripts that change state are marked **MUTATING**; the diagnostic collector must not perform recovery.

## 7. Observed symptoms

The following summarizes the recorded private lab observations, **not** the new public synthetic fixture data:

| Signal | Baseline | Deliberate wrong-port fault | Recovery |
|---|---|---|---|
| Hyper-V VM state | Running | Running | Running |
| Windows SSH collection | Successful | Successful | Successful |
| systemd ActiveState | Active | Active | Active |
| Service `LISTEN_PORT` | 8080 | 8081 | 8080 |
| Listening socket | 8080 | 8081 | 8080 |
| Windows TCP 8080 | Reachable | Unreachable | Reachable |
| Windows `8080 /readyz` | HTTP 200, ready true | Failed | HTTP 200, ready true |
| Windows `8081 /readyz` | Failed | HTTP 200, ready true | Failed |

These observations are not interchangeable: `systemctl` does not test the client path, while a successful alternate-port HTTP response alone does not establish availability of the specified endpoint.

## 8. Diagnostic commands and tools

Linux diagnostics included `systemctl show`, `ss -H -ltn`, `cat` of the test configuration, `journalctl`, and local HTTP GETs to 8080/8081. On Windows, Hyper-V state inspection, SSH collection, TCP connection tests and `curl.exe` independently checked the client path. RUN-002 used [`ansible/collect.yml`](../ansible/collect.yml) for target-side collection and [`python/evaluate.py`](../python/evaluate.py) for offline interpretation.

The Ansible collector did not intentionally change the **business service configuration**. It still executes remote modules, may create temporary files, and its GET requests may create ordinary access logs. Controller-side JSON output is a deliberate write.

## 9. Raw diagnostic material and source traceability

Private records contain timestamped Windows raw command outputs and HTTP bodies, Ansible JSON and classification outputs, operator receipts, journal extracts, and SHA-256 manifests. The reviewer separately checked **80 manifest entries across seven Windows snapshot directories and three Ansible stage directories** against the submitted archive; the directory count includes one preliminary Windows snapshot in which SSH collection failed before the accepted baseline. File-hash agreement is **internal byte consistency**, not independent proof of origin or trusted time.

The public package publishes **no original raw runtime records**. To make replay possible without exposing machine-specific details, its synthetic fixtures use fabricated process IDs and contain no observed host identifiers.

## 10. Timeline or state sequence

**RUN-001:** An initial pre-baseline observation exposed a separate collection/connectivity issue; after correction, the accepted baseline showed the 8080 endpoint healthy. A controlled change moved the service to 8081, subsequent local and Windows checks showed expected-port failure, and a distinct operator recovery action restored 8080. The manual run was closed with verified records.

**RUN-002:** A separate Ansible controller performed the same diagnosis on a healthy baseline, the injected fault state and recovery. The archived classifier outputs were:

```text
baseline  → EXPECTED_ENDPOINT_READY
fault     → PORT_MISMATCH_SUPPORTED
recovery  → EXPECTED_ENDPOINT_READY
```

The Windows client independently corroborated endpoint behavior. Target, controller and Windows clocks were not demonstrated as tightly synchronized, so this account does not claim sub-second cross-host event causality.

## 11. Competing hypotheses

| Alternative | Assessment within this run |
|---|---|
| VM powered off | Inconsistent with Hyper-V Running and successful SSH |
| Host entirely unreachable | Inconsistent with SSH access and alternate-port HTTP success |
| Application process stopped | Inconsistent with systemd Active and HTTP response on 8081 |
| Listener moved off expected endpoint | Supported by configuration=8081, socket=8081, HTTP 8081 success and HTTP 8080 failure |
| Pre-baseline firewall/network problem | A separate earlier concern; root cause **not confirmed** by complete pre/post change receipts |

These hypotheses are scoped to a deliberately constructed mismatch. The experiment does not compare every possible readiness failure family.

## 12. Diagnosis and confidence

**High confidence for the injected wrong-port failure**: configured listener, actual listening socket and successful alternate HTTP response agreed, while the client's expected port failed. The inverse pattern after recovery supports that interpretation. This is a bounded diagnosis supported by the recorded test, not a general-purpose or production-trained root-cause engine.

## 13. Recovery or containment action

A separate operator action restored the test configuration from `LISTEN_PORT=8081` to `LISTEN_PORT=8080` and restarted only the disposable lab service. The Ansible diagnostic collector did not initiate this state-changing action. This separation preserves a useful control boundary between observation and mutation.

## 14. Recovery validation

Recovery required a **fresh external** Windows TCP 8080 success, HTTP 200 from the expected `/readyz`, and a parsed JSON body containing `ready=true`. Linux configuration and socket observations matched port 8080 again; the RUN-002 classifier returned `EXPECTED_ENDPOINT_READY`. The invariant `systemd Active` alone was not accepted as proof of recovery.

## 15. Automation opportunity

The reusable artifact is an evidence-to-decision pattern: collect independent signals, retain raw observations, normalize to JSON, compute a bounded classification and confirm recovery from the client's path. The original `evaluate.py` was replayed against the archived RUN-002 raw JSON and reproduced its three stored classifications. This public package supplies synthetic replay tests. The v1.2 classifier update tightened optional Windows **healthy-state** corroboration to require external 8080 ready and 8081 not ready. The historic RUN-002 evaluator results used no `--windows-json` input and were not reclassified by that change.

**Not implemented:** AWX, AAP production deployment, automatic remediation, CI pipeline, Kubernetes/GPU diagnostics, fleet-scale control or platform-wide service-level assurance.

## 16. Known limitations

- The failure was intentionally injected into **one disposable VM**, not found in production.
- The test `/readyz` handler has a fixed `ready=true` response: no dependency/business transaction readiness was measured.
- RUN-002 inject/recover operator Transcripts did **not capture** direct remote change statements. Exit-code receipts and independent before/after observations corroborate the state but do not replace the missing stdout.
- Ansible baseline retained fewer log files than fault and recovery. The archived baseline raw JSON and diagnosis exist, but per-stage Playbook/stdout logs were not equally retained.
- Host and guest clock synchronization was not proven at sub-second granularity.
- The evaluator's optional Windows host-correlation fields were `null` in the recorded RUN-002 outputs; Windows evidence was checked **separately**, not merged into that classification.
- Hashes in the private evidence archive indicate internal integrity relative to manifests. They do not establish immutable storage, third-party attestation or cryptographic proof of experiment execution time.
- Fresh-machine rebuilding of the original golden-image workflow is not independently validated by this public package. Reproducibility is provided for synthetic classifier replay and documented as a prospective fresh lab exercise.

**Conclusion:** A VM being Running and a unit being Active are weaker observations than a successful HTTP transaction at the endpoint the client is contracted to use. The result is deliberately limited to this recorded local test and should not be generalized without further experiments.
