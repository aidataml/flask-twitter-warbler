"""Message model tests."""

import os
from unittest import TestCase
from sqlalchemy import exc
from models import db, User, Message, Follows, Likes

os.environ['DATABASE_URL'] = "postgresql:///warbler-test"

from app import app

db.create_all()

class UserModelTestCase(TestCase):

    def setUp(self):
        db.drop_all()
        db.create_all()

        self.uid = 94566
        u = User.signup("testuser", "test@test.com", "password#", None)
        u.id = self.uid
        db.session.commit()

        self.u = User.query.get(self.uid)

        self.client = app.test_client()

    def test_message_model(self):
        
        m = Message(
            text="This is a test message.",
            user_id=self.uid
        )

        db.session.add(m)
        db.session.commit()

        self.assertEqual(len(self.u.messages), 1)
        self.assertEqual(self.u.messages[0].text, "This is a test message.")
        
    def tearDown(self):
        res = super().tearDown()
        db.session.rollback()
        return res