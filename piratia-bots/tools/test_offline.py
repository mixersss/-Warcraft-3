"""Run pure codec/policy regressions in environments that deny local sockets.

Eight real-socket integration tests remain in the full unittest suite; this
runner explicitly excludes them and reports their count. No network is opened.
"""
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tests'))


def flatten(suite):
    for item in suite:
        if isinstance(item,unittest.TestSuite):
            yield from flatten(item)
        else:
            yield item


if __name__ == '__main__':
    all_tests = unittest.defaultTestLoader.discover(str(ROOT/'tests'))
    selected, skipped = [], []
    for test in flatten(all_tests):
        identity = test.id()
        if (identity.startswith('test_classic.LoginTests.') or identity.startswith('test_classic.WireTests.')
                or identity == 'test_automatic.AutomaticCreationTests.test_creation_payload_matches_native_ui_look'):
            skipped.append(identity)
        else:
            selected.append(test)
    print(f'Pure offline checks: {len(selected)}; real-socket integration tests excluded: {len(skipped)}.',flush=True)
    result = unittest.TextTestRunner(verbosity=2).run(unittest.TestSuite(selected))
    sys.exit(not result.wasSuccessful())
