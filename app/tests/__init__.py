import unittest

from .test_models import TestModels
from .test_routes import TestRoutes
from .test_socketio import TestSocketIO

loader = unittest.TestLoader()
suite = unittest.TestSuite()

# load test models
suite.addTests(loader.loadTestsFromTestCase(TestModels))
suite.addTests(loader.loadTestsFromTestCase(TestRoutes))
suite.addTests(loader.loadTestsFromTestCase(TestSocketIO))

runner = unittest.TextTestRunner(verbosity=2)


def run():
    return runner.run(suite)
