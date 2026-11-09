#!/usr/bin/env python3
"""Evaluate observed Exp01 Ansible and optional Windows snapshots.

Classifications are bounded diagnostic interpretations, never automatic remediation.
"""
import argparse
import json
import re
from pathlib import Path


def _port_open(sockets, port):
    return bool(re.search(r':%d(?:\s|$)' % port, sockets, flags=re.M))


def _port_config(config):
    match = re.search(r'(?m)^LISTEN_PORT=(\d+)\s*$', config)
    return int(match.group(1)) if match else None


def _http_ready(probe):
    return probe.get('status') == 200 and probe.get('json', {}).get('ready') is True


def evaluate(data, host=None):
    service = data.get('systemd_show', '')
    active = bool(re.search(r'(?m)^ActiveState=active\s*$', service))
    port = _port_config(data.get('config', ''))
    sockets = data.get('sockets', '')
    listening_8080 = _port_open(sockets, 8080)
    listening_8081 = _port_open(sockets, 8081)
    expected_ready = _http_ready(data.get('expected_http', {}))
    alternate_ready = _http_ready(data.get('alternate_http', {}))

    fault_match = all((active, port == 8081, listening_8081,
                       not expected_ready, alternate_ready))
    healthy_match = all((active, port == 8080, listening_8080,
                         expected_ready, not alternate_ready))
    if fault_match:
        conclusion = 'PORT_MISMATCH_SUPPORTED'
        explanation = ('Service active, configured and listening on 8081 with successful '
                       'local HTTP readiness there, while the expected 8080 probe fails.')
    elif healthy_match:
        conclusion = 'EXPECTED_ENDPOINT_READY'
        explanation = 'Service active, configured and listening on 8080; expected local HTTP readiness succeeds.'
    else:
        conclusion = 'UNRESOLVED'
        explanation = 'Observed signals do not meet the full fault or healthy pattern; examine raw evidence.'

    remote_verified = None
    host_consistent = None
    if host is not None:
        remote_verified = all((
            host.get('vm_running') is True,
            host.get('ssh_collector_ok') is True,
        ))
        ready_8080 = host.get('http_8080', {}).get('ready') is True
        ready_8081 = host.get('http_8081', {}).get('ready') is True
        if conclusion == 'PORT_MISMATCH_SUPPORTED':
            host_consistent = remote_verified and not ready_8080 and ready_8081
        elif conclusion == 'EXPECTED_ENDPOINT_READY':
            # The accepted healthy state requires 8080 ready and 8081 not ready.
            # Host booleans are summaries: verify raw external HTTP separately.
            host_consistent = remote_verified and ready_8080 and not ready_8081

    return {
        'stage': data.get('stage', 'unknown'),
        'classification': conclusion,
        'explanation': explanation,
        'signals': {
            'service_active': active,
            'config_port': port,
            'socket_8080': listening_8080,
            'socket_8081': listening_8081,
            'local_http_8080_ready': expected_ready,
            'local_http_8081_ready': alternate_ready,
            'host_vm_and_ssh_verified': remote_verified,
            'host_observations_consistent': host_consistent,
        },
        'limitations': [
            'One snapshot cannot by itself establish temporal causality.',
            'Confirm a known-good baseline before injection and a recovery snapshot after correction.',
            'Verify end-to-end readiness from Windows; local probes alone cannot rule out network/firewall faults.',
            'Do not publish actual local hostnames, IP addresses, usernames, or SSH details.',
        ],
    }


def main():
    parser = argparse.ArgumentParser(description='Evaluate Exp01 evidence without modifying systems')
    parser.add_argument('ansible_json', type=Path)
    parser.add_argument('--windows-json', type=Path, help='Matching Windows snapshot.json')
    parser.add_argument('--output', type=Path, help='Optional local JSON report path')
    args = parser.parse_args()
    data = json.loads(args.ansible_json.read_text(encoding='utf-8-sig'))
    host = None
    if args.windows_json:
        host = json.loads(args.windows_json.read_text(encoding='utf-8-sig'))
    result = evaluate(data, host)
    encoded = json.dumps(result, ensure_ascii=False, indent=2) + '\n'
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(encoded, encoding='utf-8')
    print(encoded, end='')
    return 0 if result['classification'] != 'UNRESOLVED' else 3


if __name__ == '__main__':
    raise SystemExit(main())
