import unittest

from sqlalchemy.exc import IntegrityError

from app.models import Game, Player
from app.tests.helper import BaseCase


class TestModels(BaseCase):
    def test_nullable_constraints(self):
        g = Game()
        self.db.session.add(g)
        self.db.session.commit()
        p_error1 = Player(game=g)
        p_error2 = Player(name="", game=g)
        p_error3 = Player(name="test_player1")
        self.db.session.add(p_error1)
        self.assertRaises(IntegrityError, self.db.session.commit)
        self.db.session.rollback()
        self.db.session.add(p_error2)
        self.assertRaises(IntegrityError, self.db.session.commit)
        self.db.session.rollback()
        self.db.session.add(p_error3)
        self.assertRaises(IntegrityError, self.db.session.commit)
        self.db.session.rollback()
        p = Player(name="test_player1", game=g)
        self.db.session.add(p)
        self.db.session.commit()
        p.name = ""
        self.assertRaises(IntegrityError, self.db.session.commit)
        self.db.session.rollback()
        p.name = None
        self.assertRaises(IntegrityError, self.db.session.commit)
        self.db.session.rollback()
        p.game = None
        self.assertRaises(IntegrityError, self.db.session.commit)
        self.db.session.rollback()

    def test_delete_cascades(self):
        g = Game(slug="test_game")
        p1, p2 = Player(name="test_player1", game=g), Player(name="test_player2", game=g)
        self.db.session.add_all([g, p1, p2])
        g.players = [p1, p2]
        self.db.session.commit()
        g.current_chancellor = p1
        g.freeze_player_positions()
        self.db.session.delete(p1)
        self.db.session.commit()
        self.assertFalse(g.current_chancellor)
        self.assertNotIn(p1, g.players)
        self.db.session.delete(g)
        self.db.session.commit()
        self.assertFalse(Player.query.all())

    def test_unique_constraints(self):
        g1, g2 = Game(), Game()
        self.db.session.add_all([g1, g2])
        self.db.session.commit()
        g2.slug = g1.slug
        self.assertRaises(IntegrityError, self.db.session.commit)
        self.db.session.rollback()
        p1, p2 = Player(name="test_player1", sid=12, game=g1), Player(name="test_player2", game=g1)
        self.db.session.add_all([p1, p2])
        self.db.session.commit()
        p2.id = p1.id
        self.assertRaises(IntegrityError, self.db.session.commit)
        self.db.session.rollback()
        p2.sid = p1.sid
        self.assertRaises(IntegrityError, self.db.session.commit)
        self.db.session.rollback()

    def test_validations(self):
        g, p = Game(slug="test_game", current_state="nomination"), Player(name="test_player1", position=1)
        p.game = g
        self.db.session.add_all([g, p])
        self.db.session.commit()
        with self.assertRaises(AssertionError):
            g.current_state = "test_error"
        with self.assertRaises(AssertionError):
            g.elected_policies = [1, 0]
        with self.assertRaises(AssertionError):
            g.elected_policies += (1, 0, 2)
        with self.assertRaises(AssertionError):
            p.set_vote(1)
        with self.assertRaises(AssertionError):
            p.set_role("error")
        with self.assertRaises(AssertionError):
            p.set_role(1)
        g.players.clear()

    def test_game_methods(self):
        g, p1, p2, p3 = Game(slug="test_game"), Player(name="test_player1", sid=1), \
                        Player(name="test_player2", sid=2), Player(name="test_player3", sid=3)
        self.db.session.add_all([g, p1, p2, p3])
        g.players = [p1, p2, p3]
        p1.set_vote(True)
        p2.set_vote(False)
        self.assertFalse(g.everybody_voted())
        with self.assertRaises(AssertionError):
            g.evaluate_votes()
        p3.set_vote(False)
        self.assertTrue(g.everybody_voted())
        self.assertFalse(g.evaluate_votes())
        p3.set_vote(True)
        self.assertTrue(g.evaluate_votes())
        g.clear_votes()
        self.assertTrue(all(player.get_vote() is None for player in g.players))

        g.current_president = p1
        g.advance_president()
        self.assertEqual(g.current_president, p2)
        g.current_president = p3
        g.advance_president()
        self.assertEqual(g.current_president, p1)

        roles = g.get_roles()
        self.assertTrue(all(player.get_role() in ["fascist", "liberal", "hitler"] for player in g.players))
        self.assertEqual(g.get_roles(), roles)

        g.freeze_player_positions()
        self.db.session.commit()
        old = g.players
        self.assertTrue(all(player.position == g.players.index(player) for player in g.players))
        g.freeze_player_positions(scramble=True)
        self.db.session.commit()
        try:
            self.assertFalse(g.players == old)
        except AssertionError:
            g.freeze_player_positions(scramble=True)
            self.db.session.commit()
            self.assertTrue(all(player.position == g.players.index(player) for player in g.players))

    def test_game_allocation(self):
        g, p1, p2, p3 = Game(slug="test_game"), Player(name="test_player1"), Player(name="test_player2"), \
                        Player(name="test_player3")
        self.db.session.add_all([g, p1, p2])
        g.players.append(p1)
        p2.game = g
        self.assertEqual(g.players, [p1, p2])
        self.assertEqual(p1.game, g)
        self.assertEqual(p2.game, g)
        g.players.append(p3)
        self.assertEqual(g.players, [p1, p2, p3])
        self.assertEqual(p3.game, g)
        self.assertEqual(Player.query.all(), [p1, p2, p3])

    def test_assignment_allocation(self):
        g, g2 = Game(), Game()
        p = Player(name="test_player1", game=g2)
        self.db.session.add_all([g, g2, p])
        g.current_president = p
        self.db.session.commit()
        self.assertFalse(g.current_president)
        p.game = g
        g.current_president = p
        self.db.session.commit()
        self.assertEqual(g.current_president, p)


if __name__ == '__main__':
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    suite.addTests(loader.loadTestsFromTestCase(TestModels))

    runner = unittest.TextTestRunner(verbosity=2)
    runner.run(suite)
