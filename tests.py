import unittest

from app import create_app, db, socketio
from app.models import Game, Player
from config import Config


class TestConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite://'


class GameCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app("testing")
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()

        if not Game.query.get("test-game"):
            self.g = Game(slug="test-game")
            db.session.add(self.g)
            db.session.commit()

        self.flask_client1 = self.app.test_client()
        self.flask_client2 = self.app.test_client()
        self.client1 = socketio.test_client(self.app, flask_test_client=self.flask_client1, query_string="?game=test-game")
        self.client2 = socketio.test_client(self.app, flask_test_client=self.flask_client2, query_string="?game=test-game")

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    @staticmethod
    def login(client, username):
        return client.post('/login', data={"username": username}, follow_redirects=True)

    @staticmethod
    def logout(client):
        return client.get('/logout', follow_redirects=True)

    def test_login(self):
        p = Player.query.filter_by(name="Test-Player1").all()
        self.assertEqual(len(p), 0)
        r = self.login(self.flask_client1, "Test-Player1")
        p = Player.query.filter_by(name="Test-Player1").all()
        self.assertEqual(len(p), 1)
        self.assertTrue(p[0].is_authenticated)
        self.assertIn("Logged in as Test-Player1", r.data.decode())
        r = self.login(self.flask_client1, "Test-Player1")
        self.assertNotIn("Loggin in as Test-Player1", r.data.decode())
        r = self.logout(self.flask_client1)
        self.assertIn("logged out.", r.data.decode())
        r = self.logout(self.flask_client1)
        self.assertNotIn("logged out.", r.data.decode())
        p = Player.query.filter_by(name="Test-Player1").all()
        self.assertEqual(len(p), 0)

    def test_game(self):
        self.assertFalse(self.client1.is_connected())
        r = self.login(self.flask_client1, "Test-Player1")
        self.client1.connect(query_string="?game=test-game")
        self.assertTrue(self.client1.is_connected())


if __name__ == '__main__':
    unittest.main(verbosity=2)