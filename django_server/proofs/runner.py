"""
proofs/runner.py — Custom Django test runner that colorises FAIL/ERROR output
and prints a final summary showing total tests run, failures/errors by file,
or a clean "all X tests passed" message.

Registered in settings.py:
  TEST_RUNNER = 'proofs.runner.ColorDiscoverRunner'

Replaces the subprocess-orchestrator in proofs/tests.py.  All test modules are
discovered and run once by Django's standard discovery mechanism; this runner
just adds bold-red colouring to failure markers and traceback headers.
"""

import sys
import unittest
from collections import defaultdict
from django.test.runner import DiscoverRunner

_RED   = "\x1b[1;31m"
_GREEN = "\x1b[1;32m"
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

    def run_tests(self, test_labels, **kwargs):
        result = super().run_tests(test_labels, **kwargs)
        self._print_final_summary()
        return result

    def _print_final_summary(self):
        """Print a one-line summary after Django's own output."""
        suite = self._last_suite if hasattr(self, '_last_suite') else None
        result = self._last_result if hasattr(self, '_last_result') else None
        if result is None:
            return

        use_color = _tty()
        total = result.testsRun
        problems = result.failures + result.errors
        total_bad = len(problems)

        stream = sys.stderr

        stream.write("\n" + "=" * 70 + "\n")

        if not problems:
            green, reset = (_GREEN, _RESET) if use_color else ("", "")
            stream.write(f"{green}All {total} tests passed.{reset}\n")
        else:
            red, reset = (_RED, _RESET) if use_color else ("", "")
            # Group failures/errors by source file
            by_file = defaultdict(int)
            for test, _ in problems:
                mod = type(test).__module__          # e.g. "induction_api.test_download_upload"
                # Convert dotted module path to a file path for readability
                file_path = mod.replace('.', '/') + '.py'
                by_file[file_path] += 1

            stream.write(
                f"{red}{total_bad} failure(s)/error(s) in {total} tests.{reset}\n"
            )
            stream.write("Files with failures:\n")
            for path, count in sorted(by_file.items()):
                stream.write(f"  {path}  ({count} failure(s))\n")

        stream.write("=" * 70 + "\n")
        stream.flush()

    def build_suite(self, *args, **kwargs):
        suite = super().build_suite(*args, **kwargs)
        self._last_suite = suite
        return suite

    def run_suite(self, suite, **kwargs):
        result = super().run_suite(suite, **kwargs)
        self._last_result = result
        return result
