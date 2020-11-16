import unittest

from app import create_app, db


class BaseCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app("testing")
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.drop_all()
        db.create_all()
        self.session = db.session

    def tearDown(self):
        db.session.close_all()
        db.drop_all()
        self.app_context.pop()
