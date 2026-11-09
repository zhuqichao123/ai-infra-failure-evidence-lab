#!/usr/bin/env bash
# MUTATING - install only on a disposable Rocky 9 or Ubuntu 24.04 lab clone.
set -euo pipefail
if [[ $EUID -ne 0 ]]; then echo 'Run: sudo bash 00-install.sh' >&2; exit 2; fi
source_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
for command_name in python3 systemctl ss curl install; do
  if ! command -v "$command_name" >/dev/null 2>&1; then
    echo "Missing prerequisite: $command_name. Install it explicitly before continuing." >&2
    exit 2
  fi
done
if ! id nobody >/dev/null 2>&1; then echo 'Missing service account: nobody' >&2; exit 2; fi
if [[ -e /etc/systemd/system/failurelab-exp01.service || -e /etc/failurelab/experiment01.env ]]; then
  echo 'Lab service/config already exists; refusing to overwrite. Use inject/recover instead.' >&2
  exit 2
fi
install -d -m 0755 /opt/failurelab/experiment01 /etc/failurelab
install -m 0644 "$source_dir/app.py" /opt/failurelab/experiment01/app.py
install -m 0755 "$source_dir/collect-manual.sh" /opt/failurelab/experiment01/collect-manual.sh
printf 'LISTEN_PORT=8080\n' > /etc/failurelab/experiment01.env
chmod 0644 /etc/failurelab/experiment01.env
install -m 0644 "$source_dir/failurelab-exp01.service" /etc/systemd/system/failurelab-exp01.service
systemctl daemon-reload
systemctl enable --now failurelab-exp01.service
printf 'installed_utc=%s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
printf 'baseline_expected_port=8080\n'
echo 'No firewall rules were changed. If needed, explicitly authorize temporary port access only from your trusted test client; remove it after the lab.'
