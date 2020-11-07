import unittest

from app import app, db, socketio


class GameCase(unittest.TestCase):
    def setUp(self):
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite://'
        db.create_all()

        self.client = app.test_client()
        self.socketio_client = socketio.test_client(app, flask_test_client=self.client)

    def tearDown(self):
        db.session.remove()
        db.drop_all()


if __name__ == '__main__':
    unittest.main(verbosity=2)