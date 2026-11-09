# EXP01 release checklist — multi-experiment repository

**Status:** historical evidence claims remain limited to the controlled local experiment. Public release can only be claimed after confirming the actual remote main branch. This checklist is not an external attestation.

## Evidence and public statements

- [ ] Keep `SYNTHETIC` injected-fault inputs distinct from `LOCAL-REPRODUCED` lab observations. The published JSON fixtures are newly authored examples, not original logs.
- [ ] Preserve the operator transcript gaps, lack of sub-second clock attestation, simplified `/readyz`, and untested AWX/AAP, Kubernetes, GPU and production HA boundaries.
- [ ] Do not upload original RUN-001/RUN-002 evidence, operator receipts, SSH material, actual network identifiers, freeze archives, or disks.

## Validation

From `experiments/EXP01-vm-running-not-ready/`:

```powershell
python -m unittest discover -s tests -v
python python/evaluate.py fixtures/SYNTHETIC-ONLY-baseline.json
python python/evaluate.py fixtures/SYNTHETIC-ONLY-fault.json
python python/evaluate.py fixtures/SYNTHETIC-ONLY-recovery.json
```

- [ ] Verify this experiment's `PUBLIC-SHA256SUMS.txt` against all 20 experiment files.
- [ ] Verify repository-root `PUBLIC-SHA256SUMS.txt` against all other 25 tracked source files, including the EXP01 manifest.
- [ ] Review the exact Git Index, including `git diff --cached --check`, before push. Ignore rules alone do not prove exclusion.
- [ ] Confirm the root README, project LICENSE, and every README/CASE_STUDY/REPLAY link renders in GitHub.

## Publication gate

- [x] Publisher stated that public code/narrative is owned or authorized for release.
- [x] MIT License selected for original release material.
- [ ] Confirm target `zhuqichao123/ai-infra-failure-evidence-lab` remains an empty **Public** repository at push time.
- [ ] Confirm `gh api user --jq .login` returns `zhuqichao123`; use the HTTPS Git remote, not an SSH key authenticated to another account.
- [ ] Confirm the first commit uses a personal or GitHub no-reply author identity.
- [ ] Confirm the remote `main` SHA, public visibility, and the complete 26-file Git tree after push.

No GitHub upload is assumed until the actual push and remote verification pass.
