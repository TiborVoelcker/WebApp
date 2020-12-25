import unittest

from flask_login import current_user

from app.models import Player, Game
from app.tests.helper import BaseCase, login, logout


class TestRoutes(BaseCase):
    def test_index(self):
        with self.app.test_client() as c:
            res = c.get('/')
            self.assertEqual(res.status_code, 200)
            res = c.get('/index')
            self.assertEqual(res.status_code, 200)

            g = Game(slug="test_game")
            self.session.add(g)
            self.session.commit()
            res = c.post('/', data={"submit": True, "game_slug": "test_game"})
            self.assertEqual(res.status_code, 302)
            res = c.post('/', data={"submit": True, "game_slug": "failing"})
            self.assertEqual(res.status_code, 200)

            length = len(Game.query.all())
            res = c.post('/', data={"new_game": True})
            self.assertEqual(res.status_code, 302)
            self.assertEqual(len(Game.query.all()), length+1)

            res = c.post('/', data={"rejoin": True})
            self.assertEqual(res.status_code, 200)
            login(c, "test_player")
            res = c.post('/', data={"rejoin": True})
            self.assertEqual(res.status_code, 200)
            current_user.game = g
            self.session.commit()
            res = c.post('/', data={"rejoin": True})
            self.assertEqual(res.status_code, 302)

    def test_login(self):
        with self.app.test_client() as c:
            res = c.get("/login")
            self.assertEqual(res.status_code, 200)
            res = login(c, "test_player", False)
            self.assertEqual(res.status_code, 302)
            self.assertEqual(len(Player.query.filter(Player.name == "test_player").all()), 1)
            p = Player.query.filter(Player.name == "test_player").first()
            self.assertTrue(p.is_authenticated)
            self.assertEqual(p, current_user)
            res = c.get("/login")
            self.assertEqual(res.status_code, 302)

    def test_logout(self):
        with self.app.test_client() as c:
            res = logout(c, False)
            self.assertEqual(res.status_code, 302)
            self.assertEqual(len(Player.query.filter(Player.name == "test_player").all()), 0)
            self.assertFalse(current_user.is_authenticated)

    def test_game(self):
        with self.app.test_request_context():
            with self.app.test_client() as c:
                g = Game(slug="test_game")
                self.session.add(g)
                self.session.commit()
                res = c.get("/game/test_game")
                self.assertEqual(res.status_code, 302)
                login(c, "test_player")
                res = c.get("/game/test_game")
                self.assertEqual(res.status_code, 200)
                res = c.get("/game/failing")
                self.assertEqual(res.status_code, 404)


if __name__ == '__main__':
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    suite.addTests(loader.loadTestsFromTestCase(TestRoutes))

    runner = unittest.TextTestRunner(verbosity=2)
    runner.run(suite)
