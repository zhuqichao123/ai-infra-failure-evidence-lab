# AI Infrastructure Failure Evidence Lab

**Controlled infrastructure failure experiments, bounded diagnosis and reproducible recovery verification.**

This repository publishes deliberately scoped engineering experiments that move from observable system state to a testable diagnosis and recovery check. It is a technical lab, **not** a collection of production incident records or an independent compliance certification.

## Experiment index

| ID | Failure scenario | Technology | Public evidence | Status |
| --- | --- | --- | --- | --- |
| [EXP01](experiments/EXP01-vm-running-not-ready/README.md) | VM Running Does Not Mean Service Ready | Hyper-V / Rocky Linux / systemd / Ansible / Python | Sanitized technical case, read-only collector, newly authored synthetic fixtures, offline replay | Local experiment completed; synthetic public replay available |

New experiments will be added beneath `experiments/`, each with its own scoped claims, code, synthetic sample data and verification instructions. There is no published EXP02 or GPU experiment yet.

## EXP01 in brief

The VM was Running and its service active, but the client-expected HTTP endpoint on port 8080 was unavailable. A deliberately configured listener on 8081 produced the mismatch; recovery restored the expected endpoint. The public code can replay the classifier on synthetic inputs without access to the original private observations. See the [detailed case study](experiments/EXP01-vm-running-not-ready/docs/CASE_STUDY.md) and [replay instructions](experiments/EXP01-vm-running-not-ready/docs/REPLAY.md).

```powershell
cd experiments/EXP01-vm-running-not-ready
python -m unittest discover -s tests -v
python python/evaluate.py fixtures/SYNTHETIC-ONLY-fault.json
```

## Evidence and safety boundaries

- `SYNTHETIC` fixtures are newly authored illustrative examples, **not** redacted original logs.
- `LOCAL-REPRODUCED` describes a controlled, single-VM lab; it does not imply a production incident, fleet-scale proof, or independently attested evidence.
- The `/readyz` sample endpoint only tests this toy HTTP response. It is **not** a dependency-aware or business-transaction health check.
- AWX/AAP, Kubernetes, GPU systems, automatic remediation, and high-availability operations were not tested by EXP01.
- Real hostnames, IP addresses, credentials, raw RUN-001/RUN-002 records and the separately retained private evidence freeze are **not** included.
- Some lab scripts intentionally mutate a disposable VM. Read the [reproduction guide](experiments/EXP01-vm-running-not-ready/docs/REPLAY.md) before running them; never use on production or shared infrastructure.

## Repository layout and integrity

- [`experiments/EXP01-vm-running-not-ready/`](experiments/EXP01-vm-running-not-ready/) — the independently scoped first experiment.
- [`experiments/EXP01-vm-running-not-ready/PUBLIC-SHA256SUMS.txt`](experiments/EXP01-vm-running-not-ready/PUBLIC-SHA256SUMS.txt) — file hashes relative to that experiment directory.
- [`PUBLIC-SHA256SUMS.txt`](PUBLIC-SHA256SUMS.txt) — repository-level SHA-256 manifest covering every other tracked source file, including the EXP01 manifest. A manifest stored in the repository is a reproducibility aid, **not external attestation**.
- [MIT License](LICENSE) — applies to the code and documentation in this repository unless stated otherwise.

The project is intentionally distinct from broader research about enterprise workflows in the AI era: this repository concentrates on executable technical failures and evidence-based diagnostics, not business process commentary.
