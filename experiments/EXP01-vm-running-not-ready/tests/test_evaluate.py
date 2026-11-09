import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'python'))
from evaluate import evaluate


def sample(port=8081, active=True):
    return {
        'stage': 'fault' if port == 8081 else 'baseline',
        'systemd_show': 'LoadState=loaded\nActiveState=%s\nSubState=running' % ('active' if active else 'inactive'),
        'config': 'LISTEN_PORT=%s' % port,
        'sockets': 'LISTEN 0 5 0.0.0.0:%d 0.0.0.0:*' % port,
        'expected_http': {'status': 200, 'json': {'ready': True}} if port == 8080 else {'status': -1, 'msg': 'Connection refused'},
        'alternate_http': {'status': 200, 'json': {'ready': True}} if port == 8081 else {'status': -1, 'msg': 'Connection refused'},
    }


class EvaluateTests(unittest.TestCase):
    def test_fault_signal_pattern(self):
        result = evaluate(sample(8081))
        self.assertEqual(result['classification'], 'PORT_MISMATCH_SUPPORTED')
        self.assertFalse(result['signals']['local_http_8080_ready'])
        self.assertTrue(result['signals']['local_http_8081_ready'])

    def test_healthy_signal_pattern(self):
        self.assertEqual(evaluate(sample(8080))['classification'], 'EXPECTED_ENDPOINT_READY')

    def test_service_inactive_is_not_port_diagnosis(self):
        self.assertEqual(evaluate(sample(8081, active=False))['classification'], 'UNRESOLVED')

    def test_windows_disagreement_is_not_hidden(self):
        host = {'vm_running': True, 'ssh_collector_ok': True,
                'http_8080': {'ready': False}, 'http_8081': {'ready': False}}
        result = evaluate(sample(8081), host)
        self.assertFalse(result['signals']['host_observations_consistent'])

    def test_healthy_windows_confirmation(self):
        host = {'vm_running': True, 'ssh_collector_ok': True,
                'http_8080': {'ready': True}, 'http_8081': {'ready': False}}
        self.assertTrue(evaluate(sample(8080), host)['signals']['host_observations_consistent'])

    def test_healthy_windows_unexpected_alternate_readiness_is_inconsistent(self):
        # Previously returned True even though the external state contradicted
        # the expected exclusive listener state in the healthy matrix.
        host = {'vm_running': True, 'ssh_collector_ok': True,
                'http_8080': {'ready': True}, 'http_8081': {'ready': True}}
        self.assertFalse(evaluate(sample(8080), host)['signals']['host_observations_consistent'])

    def test_healthy_windows_ssh_failure_is_inconsistent(self):
        host = {'vm_running': True, 'ssh_collector_ok': False,
                'http_8080': {'ready': True}, 'http_8081': {'ready': False}}
        result = evaluate(sample(8080), host)
        self.assertFalse(result['signals']['host_vm_and_ssh_verified'])
        self.assertFalse(result['signals']['host_observations_consistent'])

    def test_windows_confirmation(self):
        host = {'vm_running': True, 'ssh_collector_ok': True,
                'http_8080': {'ready': False}, 'http_8081': {'ready': True}}
        self.assertTrue(evaluate(sample(8081), host)['signals']['host_observations_consistent'])


if __name__ == '__main__':
    unittest.main()
