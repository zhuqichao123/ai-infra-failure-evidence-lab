# Replay and optional live-lab procedure

There are **two different levels of reproducibility**. Offline replay of the bundled **synthetic** data is tested here; reproducing the failure on fresh infrastructure requires your own disposable lab and is not certified by the synthetic tests.

## A. Offline classifier replay (no live infrastructure)

Requirements: Python 3.9 or later, standard library only. From this EXP01 directory (`experiments/EXP01-vm-running-not-ready/`):

```bash
python3 -m unittest discover -s tests -v
python3 python/evaluate.py fixtures/SYNTHETIC-ONLY-baseline.json
python3 python/evaluate.py fixtures/SYNTHETIC-ONLY-fault.json
python3 python/evaluate.py fixtures/SYNTHETIC-ONLY-recovery.json
python3 python/evaluate.py fixtures/SYNTHETIC-ONLY-fault.json --windows-json fixtures/SYNTHETIC-ONLY-windows-fault.json
```

Expected labels: `EXPECTED_ENDPOINT_READY` / `PORT_MISMATCH_SUPPORTED` / `EXPECTED_ENDPOINT_READY`. With the optional synthetic Windows fixture, `host_observations_consistent` should be `true`. The labels are **not** generated from real logged production data.

## B. Optional fresh live-lab reproduction

**Safety boundary:** Never use a shared VM, golden image, customer system, production service or reachable public interface. The test HTTP app binds to all guest interfaces (`0.0.0.0`) and is intended for an isolated VM network. The install, inject and recover commands below deliberately change the lab VM.

### 1. Prepare

Use a disposable Rocky Linux 9 target VM and a separate Linux Ansible Controller (Ansible Core 2.14 was used in the recorded experiment). Ensure SSH authentication and verify the target host key independently. Install Python 3, `iproute` (for `ss`), curl and systemd on the target. Only if explicitly appropriate, configure **temporary, narrowly scoped** guest firewall access from a trusted Windows test host. Do not disable firewalld or publish this service on the internet.

Copy this experiment's `linux/` directory into the target user's home directory; remain in the **home directory** (the parent of `linux/`) when invoking the following commands. The install script intentionally does not change firewall rules. For an external Windows test, authorize **only** the necessary temporary traffic from a trusted test client and remove that access after the lab. No firewall helper script is bundled.

```bash
sudo bash linux/00-install.sh
systemctl is-active failurelab-exp01.service
cat /etc/failurelab/experiment01.env
ss -H -ltn
curl --noproxy '*' -fsS http://127.0.0.1:8080/readyz
```

Read the installation script before running it. It places the test code under `/opt/failurelab/experiment01` and the service under `/etc/systemd/system`.

### 2. Validate baseline from the Windows client

On the Windows host, substitute the real disposable VM's IP **locally**; do not commit your command history or outputs:

```powershell
$TargetIp = 'REPLACE-WITH-DISPOSABLE-VM-IP'
Test-NetConnection -ComputerName $TargetIp -Port 8080
curl.exe --noproxy '*' -i "http://${TargetIp}:8080/readyz"
```

Require TCP success, HTTP 200 and a parsed JSON body where `ready` is `true`. This endpoint is a basic test response, not a dependency-sensitive health check.

### 3. Configure the Ansible Collector

On the Linux Controller, copy `ansible/hosts.ini.example` to `ansible/hosts.ini` and edit target address and user for your lab. Never commit the real inventory or private SSH keys. Confirm the target's identity and the Ansible link:

```bash
ansible -i ansible/hosts.ini lab_rocky -m ansible.builtin.ping
ansible-playbook -i ansible/hosts.ini ansible/collect.yml --syntax-check
```

For Baseline (change `stage` and output path for later steps):

```bash
OUT="$HOME/failurelab/evidence/baseline-$(date -u +%Y%m%dT%H%M%SZ)"
ansible-playbook -i ansible/hosts.ini ansible/collect.yml -e "stage=baseline artifact_dir=$OUT"
# The JSON filename uses the exact inventory alias from hosts.ini.
python3 python/evaluate.py "$OUT/lab-node-a-baseline.json"
```

The collector writes its JSON on the Controller; it does not change test-service configuration. Ansible module staging and HTTP probes can cause temporary files/logs on the target.

### 4. Inject, collect and recover

On the disposable target only, verify the healthy baseline first, then:

```bash
sudo bash linux/01-inject-wrong-port.sh
```

Do not run any recovery command from Ansible. With the service listening on 8081, repeat the external Windows 8080 test and inspect port 8081 separately. On the controller, collect and classify the **fault** with a new artifact directory (the inventory alias is `lab-node-a` in the example):

```bash
OUT="$HOME/failurelab/evidence/fault-$(date -u +%Y%m%dT%H%M%SZ)"
ansible-playbook -i ansible/hosts.ini ansible/collect.yml -e "stage=fault artifact_dir=$OUT"
python3 python/evaluate.py "$OUT/lab-node-a-fault.json"
```

Require `PORT_MISMATCH_SUPPORTED`; preserve the results privately. Then recover independently on the disposable target:

```bash
sudo bash linux/02-recover-expected-port.sh
```

Retest Windows 8080 HTTP and parsed JSON. Back on the controller, collect and classify the **recovery** in a new directory:

```bash
OUT="$HOME/failurelab/evidence/recovery-$(date -u +%Y%m%dT%H%M%SZ)"
ansible-playbook -i ansible/hosts.ini ansible/collect.yml -e "stage=recovery artifact_dir=$OUT"
python3 python/evaluate.py "$OUT/lab-node-a-recovery.json"
```

Require `EXPECTED_ENDPOINT_READY` together with an independent external Windows response. If behavior differs, stop and preserve the raw evidence rather than forcing the classifier output. The evaluator's optional `--windows-json` flag consumes summary fields and does not replace independent raw HTTP-body validation.

### 5. Reset and teardown

For a correct recovery, `cat /etc/failurelab/experiment01.env` must show `LISTEN_PORT=8080` and a new external GET on port 8080 must return the test body. After saving evidence, destroy the disposable VM or explicitly disable/remove the test service and any temporary firewall rules. Destroy/reset is an **operator action**, not a function of the diagnostic collector.

## What this public kit does not include

The original Windows automation wrapper, original guest identifiers, raw logs, run receipts, SSH keys, IP configuration, private freeze, golden-image factory and original VM disk images are intentionally absent. Consequently, this is a **safe technical demonstration and offline replay package**, not an exact clone of the historical local environment.
