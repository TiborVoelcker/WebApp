import unittest

from flask import url_for

from app import create_app, db


class BaseCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app("testing")
        self.app_context = self.app.app_context()
        self.app_context.push()
        self.db = db
        self.db.drop_all()
        self.db.create_all()

    def tearDown(self):
        self.db.session.remove()
        self.db.session.close_all()
        self.db.drop_all()
        self.app_context.pop()


def login(client, slug, username, follow_redirects=True):
    return client.post(url_for("main.login", slug=slug), data={"username": username}, follow_redirects=follow_redirects)


def logout(client, follow_redirects=True):
    return client.get('/logout', follow_redirects=follow_redirects)