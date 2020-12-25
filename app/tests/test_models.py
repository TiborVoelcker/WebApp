import unittest

from sqlalchemy.exc import IntegrityError

from app.models import Game, Player
from app.tests.helper import BaseCase


class TestModels(BaseCase):
    def test_nullable_constraints(self):
        p_error1 = Player()
        p_error2 = Player(name="")
        self.db.session.add(p_error1)
        self.assertRaises(IntegrityError, self.db.session.commit)
        self.db.session.rollback()
        self.db.session.add(p_error2)
        self.assertRaises(IntegrityError, self.db.session.commit)
        self.db.session.rollback()
        p = Player(name="test_player1")
        self.db.session.add(p)
        self.db.session.commit()
        p.name = ""
        self.assertRaises(IntegrityError, self.db.session.commit)
        self.db.session.rollback()
        p.name = None
        self.assertRaises(IntegrityError, self.db.session.commit)
        self.db.session.rollback()

    def test_delete_cascades(self):
        g, p1, p2 = Game(slug="test_game"), Player(name="test_player1"), Player(name="test_player2")
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
        self.assertFalse(p2.game)
        self.assertFalse(p2.position)

    def test_unique_constraints(self):
        g1, g2, p1, p2 = Game(), Game(), Player(name="test_player1", sid=12), Player(name="test_player2")
        self.db.session.add_all([g1, g2, p1, p2])
        self.db.session.commit()
        g2.slug = g1.slug
        self.assertRaises(IntegrityError, self.db.session.commit)
        self.db.session.rollback()
        p2.id = p1.id
        self.assertRaises(IntegrityError, self.db.session.commit)
        self.db.session.rollback()
        p2.sid = p1.sid
        self.assertRaises(IntegrityError, self.db.session.commit)
        self.db.session.rollback()

    def test_add_objects(self):
        def assert_fields(g, p):
            self.assertEqual(g.slug, "test_game")
            self.assertEqual(g.turn_no, 4)
            self.assertEqual(g.current_state, "nomination")
            self.assertEqual(g.elected_policies, (1, 0))
            self.assertEqual(p.name, "test_player2")
            self.assertEqual(p.id, 29)
            self.assertEqual(p.sid, 135)
            self.assertEqual(p.position, 5)
        g1, p1 = Game(), Player(name="test_player1")
        self.db.session.add_all([g1, p1])
        self.db.session.commit()
        self.assertEqual(Game.query.all(), [g1])
        self.assertEqual(Player.query.all(), [p1])
        g1.slug = "test_game"
        g1.turn_no = 4
        g1.current_state = "nomination"
        g1.elected_policies += (1, 0)
        p1.name = "test_player2"
        p1.position = 5
        p1.id = 29
        p1.sid = 135
        self.db.session.commit()
        assert_fields(g1, p1)
        self.db.session.delete(g1)
        self.db.session.delete(p1)
        self.db.session.commit()
        self.assertFalse(Game.query.first())
        self.assertFalse(Player.query.first())
        g2 = Game(slug="test_game", turn_no=4, current_state="nomination", elected_policies=(1, 0))
        p2 = Player(name="test_player2", id=29, sid=135, position=5)
        self.db.session.add_all([g2, p2])
        self.db.session.commit()
        assert_fields(g2, p2)

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
        self.db.session.commit()
        self.assertEqual(p.position, None)

    def test_game_methods(self):
        g, p1, p2, p3 = Game(slug="test_game"), Player(name="test_player1", sid=1), \
                        Player(name="test_player2", sid=2), Player(name="test_player3", sid=3)
        self.db.session.add_all([g, p1, p2, p3])
        g.players = [p1, p2, p3]
        self.db.session.commit()
        p1.set_vote(True)
        p2.set_vote(False)
        self.db.session.commit()
        self.assertFalse(g.everybody_voted())
        with self.assertRaises(AssertionError):
            g.evaluate_votes()
        p3.set_vote(False)
        self.db.session.commit()
        self.assertTrue(g.everybody_voted())
        self.assertFalse(g.evaluate_votes())
        p3.set_vote(True)
        self.db.session.commit()
        self.assertTrue(g.evaluate_votes())
        g.clear_votes()
        self.db.session.commit()
        self.assertTrue(all(player.get_vote() is None for player in g.players))

        g.current_president = p1
        g.advance_president()
        self.db.session.commit()
        self.assertEqual(g.current_president, p2)
        g.current_president = p3
        g.advance_president()
        self.db.session.commit()
        self.assertEqual(g.current_president, p1)

        roles = g.get_roles()
        self.db.session.commit()
        self.assertTrue(all(player.get_role() in ["fascist", "liberal", "hitler"] for player in g.players))
        self.assertEqual(g.get_roles(), roles)

        g.freeze_player_positions()
        self.assertTrue(all(player.position == g.players.index(player) for player in g.players))
        g.freeze_player_positions(scramble=True)
        self.assertTrue(all(type(player.position) is int for player in g.players))

    def test_game_allocation(self):
        g, p1, p2, p3 = Game(slug="test_game"), Player(name="test_player1"), Player(name="test_player2"), \
                        Player(name="test_player3")
        self.db.session.add_all([g, p1, p2])
        self.db.session.commit()
        g.players.append(p1)
        p2.game = g
        self.db.session.commit()
        self.assertEqual(g.players, [p1, p2])
        self.assertEqual(p1.game, g)
        self.assertEqual(p2.game, g)
        g.players.append(p3)
        self.db.session.commit()
        self.assertEqual(g.players, [p1, p2, p3])
        self.assertEqual(p3.game, g)
        self.assertEqual(Player.query.all(), [p1, p2, p3])

    def test_assignment_allocation(self):
        g, p1, p2, p3 = Game(slug="test_game"), Player(name="test_player1"), Player(name="test_player2"), \
                        Player(name="test_player3")
        self.db.session.add_all([g, p1, p2])
        self.db.session.commit()
        g.current_president = p1
        self.db.session.commit()
        self.assertFalse(g.current_president)
        p1.game = g
        self.db.session.commit()
        g.current_president = p1
        self.assertEqual(g.current_president, p1)


if __name__ == '__main__':
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    suite.addTests(loader.loadTestsFromTestCase(TestModels))

    runner = unittest.TextTestRunner(verbosity=2)
    runner.run(suite)
