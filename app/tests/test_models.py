import unittest

from sqlalchemy.exc import IntegrityError

from app.models import Game, Player
from app.tests.helper import BaseCase


class TestModels(BaseCase):
    def test_constraints(self):
        p_error1 = Player()
        p_error2 = Player(name="")
        self.session.add(p_error1)
        self.assertRaises(IntegrityError, self.session.commit)
        self.session.rollback()
        self.session.add(p_error2)
        self.assertRaises(IntegrityError, self.session.commit)
        self.session.rollback()

    def test_game_allocation(self):
        g, p1, p2, p3 = Game(slug="test_game"), Player(name="test_player1"), Player(name="test_player2"),\
                        Player(name="test_player3")
        self.session.add_all([g, p1, p2])
        self.session.commit()
        g.players.append(p1)
        p2.game = g
        self.session.commit()
        self.assertEqual(g.players, [p1, p2])
        self.assertEqual(p1.game, g)
        self.assertEqual(p2.game, g)

    def test_assignment_allocation(self):
        g, p1, p2, p3 = Game(slug="test_game"), Player(name="test_player1"), Player(name="test_player2"), \
                        Player(name="test_player3")
        self.session.add_all([g, p1, p2])
        self.session.commit()
        g.current_president = p1
        self.session.commit()
        self.assertFalse(g.current_president)
        g1 = Game()
        g2 = Game()


if __name__ == '__main__':
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    suite.addTests(loader.loadTestsFromTestCase(TestModels))

    runner = unittest.TextTestRunner(verbosity=2)
    runner.run(suite)
