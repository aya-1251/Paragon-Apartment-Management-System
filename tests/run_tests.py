#!/usr/bin/env python3
"""
run_tests.py
Single entry-point to run the full PAMS automated test suite.

Usage:
    python run_tests.py              # run all tests
    python run_tests.py -v           # verbose output
"""

import sys
import os
import unittest

# Add the project root (two levels up from this file) to sys.path
# This allows 'import db_manager', 'import models' to work.
project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Directory containing this script (views/tests/)
test_dir = os.path.dirname(__file__)

def run(verbosity: int = 1) -> bool:
    """Run all discovered tests. Returns True if all tests passed."""
    loader = unittest.TestLoader()
    # Discover all test files matching test_*.py inside test_dir
    suite = loader.discover(start_dir=test_dir, pattern="test_*.py")

    runner = unittest.TextTestRunner(verbosity=verbosity, stream=sys.stdout)
    result = runner.run(suite)

    total = result.testsRun
    failed = len(result.failures) + len(result.errors)
    passed = total - failed

    print("\n" + "═" * 72)
    print(f"  Results: {passed}/{total} passed", end="")
    if failed:
        print(f"  |  {failed} FAILED")
    else:
        print("  ✓  ALL PASSED")
    print("═" * 72)

    return failed == 0

if __name__ == "__main__":
    verbosity = 2 if "-v" in sys.argv else 1
    success = run(verbosity)
    sys.exit(0 if success else 1)