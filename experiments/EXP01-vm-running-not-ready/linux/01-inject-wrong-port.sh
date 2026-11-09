#!/usr/bin/env bash
# MUTATING - controlled fault injection on lab VM only.
set -euo pipefail
if [[ $EUID -ne 0 ]]; then echo 'Run with sudo.' >&2; exit 2; fi
config=/etc/failurelab/experiment01.env
if [[ ! -f $config ]]; then echo 'Experiment 01 is not installed.' >&2; exit 2; fi
if ! systemctl cat failurelab-exp01.service >/dev/null 2>&1; then echo 'Service missing.' >&2; exit 2; fi
old="$(cat "$config")"
if [[ "$old" != 'LISTEN_PORT=8080' ]]; then
  echo "Expected healthy baseline config LISTEN_PORT=8080; observed: $old" >&2
  exit 2
fi
tmp="$(mktemp /etc/failurelab/experiment01.env.XXXXXX)"
trap 'rm -f -- "$tmp"' EXIT
printf 'LISTEN_PORT=8081\n' > "$tmp"
chmod 0644 "$tmp"
mv -f -- "$tmp" "$config"
trap - EXIT
systemctl restart failurelab-exp01.service
printf 'fault_injected_utc=%s old_port=8080 new_port=8081\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
