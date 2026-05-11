"""
proofs/runner.py — Custom Django test runner that colorises FAIL/ERROR output.

Registered in settings.py:
  TEST_RUNNER = 'proofs.runner.ColorDiscoverRunner'

Replaces the subprocess-orchestrator in proofs/tests.py.  All test modules are
discovered and run once by Django's standard discovery mechanism; this runner
just adds bold-red colouring to failure markers and traceback headers.
"""

import sys
import unittest
from django.test.runner import DiscoverRunner

_RED   = "\x1b[1;31m"
_RESET = "\x1b[0m"


def _tty() -> bool:
    return getattr(sys.stderr, "isatty", lambda: False)()


class ColorTextTestResult(unittest.TextTestResult):
    """TextTestResult with bold-red markers for FAIL and ERROR."""

    def addFailure(self, test, err):
        # Call the grandparent (TestResult) directly to record without printing,
        # then write our own (optionally coloured) status marker.
        unittest.TestResult.addFailure(self, test, err)
        red, reset = (_RED, _RESET) if _tty() else ("", "")
        if self.showAll:
            self.stream.writeln(red + "FAIL" + reset)
        elif self.dots:
            self.stream.write(red + "F" + reset)
            self.stream.flush()

    def addError(self, test, err):
        unittest.TestResult.addError(self, test, err)
        red, reset = (_RED, _RESET) if _tty() else ("", "")
        if self.showAll:
            self.stream.writeln(red + "ERROR" + reset)
        elif self.dots:
            self.stream.write(red + "E" + reset)
            self.stream.flush()

    def printErrorList(self, flavour, errors):
        red, reset = (_RED, _RESET) if _tty() else ("", "")
        for test, err in errors:
            self.stream.writeln(self.separator1)
            self.stream.writeln(f"{red}{flavour}{reset}: {self.getDescription(test)}")
            self.stream.writeln(self.separator2)
            self.stream.writeln(err)


class ColorTextTestRunner(unittest.TextTestRunner):
    resultclass = ColorTextTestResult


class ColorDiscoverRunner(DiscoverRunner):
    test_runner = ColorTextTestRunner
