import unittest

from app import app, db, socketio
from app.models import Game, Player


class GameCase(unittest.TestCase):
    def setUp(self):
        app.config['TESTING'] = True
        app.config['WTF_CSRF_ENABLED'] = False
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///'
        db.create_all()

        self.flask_client1 = app.test_client()
        self.flask_client2 = app.test_client()
        self.client1 = socketio.test_client(app, flask_test_client=self.flask_client1)
        self.client2 = socketio.test_client(app, flask_test_client=self.flask_client2)

        if not Game.query.get("test-game"):
            self.g = Game(slug="test-game")
            db.session.add(self.g)
            db.session.commit()

    def tearDown(self):
        db.session.remove()
        db.drop_all()

    @staticmethod
    def login(client, username):
        return client.post('/login', data={"username": username}, follow_redirects=True)

    @staticmethod
    def logout(client):
        return client.get('/logout', follow_redirects=True)

    def test_login(self):
        p = Player.query.filter_by(name="Tibor").all()
        self.assertEqual(len(p), 0)
        r = self.login(self.flask_client1, "Tibor")
        p = Player.query.filter_by(name="Tibor").all()
        self.assertEqual(len(p), 1)
        self.assertTrue(p[0].is_authenticated)
        self.assertIn("Logged in as Tibor", r.data.decode())
        r = self.login(self.flask_client1, "Tibor")
        self.assertNotIn("Loggin in as Tibor", r.data.decode())
        r = self.logout(self.flask_client1)
        self.assertIn("logged out.", r.data.decode())
        r = self.logout(self.flask_client1)
        self.assertNotIn("logged out.", r.data.decode())
        p = Player.query.filter_by(name="Tibor").all()
        self.assertEqual(len(p), 0)

    def test_game(self):
        pass


if __name__ == '__main__':
    unittest.main(verbosity=2)