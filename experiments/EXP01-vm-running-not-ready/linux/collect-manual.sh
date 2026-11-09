#!/usr/bin/env bash
# READ-ONLY diagnostic collector on VM (HTTP GETs can generate access logs).
set +e
run() {
  echo
  printf '+ '
  printf '%q ' "$@"
  echo
  "$@"
  code=$?
  printf 'EXIT_CODE=%s\n' "$code"
}
printf 'COLLECT_UTC=%s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
run uname -a
run hostnamectl
run systemctl is-active failurelab-exp01.service
run systemctl show failurelab-exp01.service -p LoadState -p ActiveState -p SubState -p MainPID -p ExecMainStartTimestamp
run cat /etc/failurelab/experiment01.env
run ss -H -ltn
run curl --noproxy '*' -sS -i --connect-timeout 2 --max-time 4 http://127.0.0.1:8080/readyz
run curl --noproxy '*' -sS -i --connect-timeout 2 --max-time 4 http://127.0.0.1:8081/readyz
run journalctl -u failurelab-exp01.service --no-pager -n 25 -o short-iso-precise
printf '\nCOLLECT_END_UTC=%s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
