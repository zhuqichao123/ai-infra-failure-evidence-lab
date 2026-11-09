"""Test only synthetic replay fixtures; these are not observed evidence."""
import json
import sys
import unittest
from pathlib import Path

root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(root / "python"))
from evaluate import evaluate


class FixtureReplayTests(unittest.TestCase):
    def test_expected_classifications(self):
        fixture_dir = root / "fixtures"
        expected = json.loads((fixture_dir / "expected-classifications.json").read_text(encoding="utf-8"))
        for name, label in expected.items():
            if name.startswith("_"):
                continue
            with self.subTest(fixture=name):
                record = json.loads((fixture_dir / name).read_text(encoding="utf-8"))
                self.assertEqual(record["evidence_class"], "SYNTHETIC")
                self.assertEqual(evaluate(record)["classification"], label)

    def test_synthetic_host_corroboration(self):
        fixture_dir = root / "fixtures"
        target = json.loads((fixture_dir / "SYNTHETIC-ONLY-fault.json").read_text(encoding="utf-8"))
        host = json.loads((fixture_dir / "SYNTHETIC-ONLY-windows-fault.json").read_text(encoding="utf-8"))
        observed = evaluate(target, host)
        self.assertEqual(observed["classification"], "PORT_MISMATCH_SUPPORTED")
        self.assertTrue(observed["signals"]["host_observations_consistent"])


if __name__ == "__main__":
    unittest.main()
