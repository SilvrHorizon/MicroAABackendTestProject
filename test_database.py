import unittest

from config import TestConfig
from app import create_app, db

from app.models import User, TrainingImage

from flask import url_for



class TestDatabase(unittest.TestCase):
    def setUp(self):
        self.app = create_app(TestConfig)
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_user(self):
        u = User(email="test@example.com", password_plain="secure_pass")
        self.assertEqual(u.email, "test@example.com")
        self.assertTrue(u.check_password("secure_pass"))

        # db.session.add(u)

    def test_training_image(self):
        u = User(email="test@example.com", password_plain="secure_pass")

        db.session.add(u)

        i = TrainingImage(user=u)
        db.session.add(i)

        db.session.commit()

        self.assertEqual(i.user, u)
        self.assertEqual(i.user_id, u.id)


if __name__ == '__main__':
    unittest.main()
