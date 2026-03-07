import os
import unittest


def _addons_tests_dirs():
    """Yield paths to tests/ directories in each addon."""
    addons_dir = os.path.join(os.path.dirname(__file__), '..', 'addons')
    addons_dir = os.path.normpath(addons_dir)
    for name in sorted(os.listdir(addons_dir)):
        tests_dir = os.path.join(addons_dir, name, 'tests')
        if os.path.isdir(tests_dir):
            yield tests_dir


def test_suite():
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    for tests_dir in _addons_tests_dirs():
        discovered = loader.discover(tests_dir, pattern='test_*.py', top_level_dir=tests_dir)
        suite.addTests(discovered)
    return suite


def main():
    unittest.main(module='gtimelog.tests', defaultTest='test_suite')
