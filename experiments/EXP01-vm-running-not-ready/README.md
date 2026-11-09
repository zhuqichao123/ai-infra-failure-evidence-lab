# EXP01 — VM Running Does Not Mean Service Ready

**A controlled, single-VM infrastructure failure experiment.** The virtual machine and systemd unit were running while the client-facing HTTP endpoint on the expected port was unavailable. A deliberately changed service listener (8080 → 8081) explained the observed mismatch; restoring it returned the expected response.

**Evidence classification:** `SYNTHETIC` injected fault + `LOCAL-REPRODUCED` lab observations. This is neither a production incident nor evidence of fleet-scale resilience.

## Contents of this experiment

- [Full 16-section technical case](docs/CASE_STUDY.md): hypothesis, method, observed state transitions, competing explanations, recovery, limitations.
- [Offline replay guide](docs/REPLAY.md): run the classifier and tests without Hyper-V, SSH, or a live guest.
- [`python/evaluate.py`](python/evaluate.py): offline signal classifier used in the experiment.
- [`ansible/collect.yml`](ansible/collect.yml): read-only **with respect to target business configuration**; writes results on the controller.
- [`linux/`](linux/): minimal test HTTP server and explicitly mutating, lab-only install/inject/recover scripts.
- [`fixtures/`](fixtures/): **NEWLY AUTHORED SYNTHETIC EXAMPLES**. These are not redacted or transformed real logs.
- [`tests/`](tests/): classifier regression and synthetic-fixture replay tests.

Private RUN-001/RUN-002 evidence, SSH material, operator receipts, raw journals, machine identifiers, and real network addresses are intentionally **not included**. No public artifact here is presented as independently attested incident evidence.

## Try the offline replay first

Requires Python 3.9+; tested with Python's built-in `unittest`, no pip install required.

```bash
python3 -m unittest discover -s tests -v
python3 python/evaluate.py fixtures/SYNTHETIC-ONLY-baseline.json
python3 python/evaluate.py fixtures/SYNTHETIC-ONLY-fault.json
python3 python/evaluate.py fixtures/SYNTHETIC-ONLY-recovery.json
```

Expected classifications, respectively: `EXPECTED_ENDPOINT_READY`, `PORT_MISMATCH_SUPPORTED`, `EXPECTED_ENDPOINT_READY`. These outputs demonstrate the classifier on **synthetic replay inputs**; they do not independently reproduce the original Hyper-V run.

## Optional fresh lab reproduction

Only use a **disposable Linux VM on a trusted isolated network**. The HTTP server binds to `0.0.0.0`; install and inject/recover scripts mutate its test service. Follow [the reproduction instructions](docs/REPLAY.md#b-optional-fresh-live-lab-reproduction) and review the exact scripts before execution. Ansible requires a Linux controller with SSH access to the target. Do **not** run the mutation scripts on production systems or golden images.

## Claim boundary

For this test application, `/readyz` is a deliberately simple HTTP response whose body always says `"ready": true` when the request handler runs. It does **not** check database connections, dependencies or business transactions. The proven distinction is *client-expected HTTP endpoint availability vs. VM/service runtime state*, not general application health. AWX, AAP, Kubernetes, GPU workloads, automatic remediation and production HA were not tested.

**Diagnostic evidence is not compliance assurance.** The recorded private evidence remains separate from this public code and synthetic fixtures. See the case study for collection provenance and evidence limitations.

**Source lineage:** Public EXP01 material was reviewed in release v1.3; the v1.4 repository genesis places it under `experiments/` without changing the collector, classifier, Linux scripts, case study or synthetic fixtures. The historic private experiment records remain separate and unchanged. Publication status must be established from the actual GitHub remote, not merely from these files.

**License:** [MIT](../../LICENSE). The publisher confirmed ownership/authorization of the original code and narrative. The public synthetic fixtures are newly authored examples, not original run logs. See the [publication checklist](docs/RELEASE_CHECKLIST.md) for release and remote-verification steps.
