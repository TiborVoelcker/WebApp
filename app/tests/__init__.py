import unittest

from .test_models import TestModels

loader = unittest.TestLoader()
suite = unittest.TestSuite()

# load test models
suite.addTests(loader.loadTestsFromTestCase(TestModels))

runner = unittest.TextTestRunner(verbosity=2)


def run():
    return runner.run(suite)
