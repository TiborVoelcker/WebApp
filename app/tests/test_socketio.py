import unittest

from app import socketio
from app.models import Game, Player
from app.tests.helper import BaseCase, login


class TestSocketIO(BaseCase):
    def setUp(self):
        super().setUp()

    def test_connect(self):
        with self.app.test_client() as flask_c:
            g1, g2 = Game(slug="test_game1"), Game(slug="test_game2")
            self.db.session.add_all([g1, g2])
            self.db.session.commit()
            c = socketio.test_client(self.app, flask_test_client=flask_c)
            c.connect(query_string="game=test_game1")
            self.assertFalse(c.is_connected())
            login(flask_c, "test_player")
            c.connect(query_string="game=failing")
            self.assertTrue(c.is_connected())
            self.assertEqual(len(Game.query.get("test_game1").players), 0)

            c.connect(query_string="game=test_game1")
            self.assertNotEqual(len(Game.query.get("test_game1").players), 0)
            c.emit("join game", "test_game2")
            self.assertEqual(len(Game.query.get("test_game2").players), 0)
            Player.query.first().game = None
            self.db.session.commit()
            c.emit("join game", "test_game2")
            self.assertNotEqual(len(Game.query.get("test_game2").players), 0)

    def test_start_game(self):
        with self.app.test_client() as flask_c:
            login(flask_c, "test_player")
            g = Game(slug="test_game")
            self.db.session.add(g)
            self.db.session.commit()
            c = socketio.test_client(self.app)
            c.emit("join game", "test_game")
            self.assertTrue(c.is_connected())
            self.assertNotEqual(len(Game.query.get("test_game").players), 0)
            c.emit("start game")
            print(c.get_received())


if __name__ == '__main__':
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    suite.addTests(loader.loadTestsFromTestCase(TestSocketIO))

    runner = unittest.TextTestRunner(verbosity=2)
    runner.run(suite)
