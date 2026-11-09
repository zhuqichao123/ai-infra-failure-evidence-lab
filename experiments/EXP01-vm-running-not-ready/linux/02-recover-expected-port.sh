#!/usr/bin/env bash
# MUTATING - explicit, separate recovery; never run from the collector.
set -euo pipefail
if [[ $EUID -ne 0 ]]; then echo 'Run with sudo.' >&2; exit 2; fi
config=/etc/failurelab/experiment01.env
if [[ ! -f $config ]]; then echo 'Experiment 01 is not installed.' >&2; exit 2; fi
old="$(cat "$config")"
if [[ "$old" != 'LISTEN_PORT=8081' ]]; then
  echo "Expected injected config LISTEN_PORT=8081; observed: $old" >&2
  exit 2
fi
tmp="$(mktemp /etc/failurelab/experiment01.env.XXXXXX)"
trap 'rm -f -- "$tmp"' EXIT
printf 'LISTEN_PORT=8080\n' > "$tmp"
chmod 0644 "$tmp"
mv -f -- "$tmp" "$config"
trap - EXIT
systemctl restart failurelab-exp01.service
printf 'recovered_utc=%s old_port=8081 new_port=8080\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
