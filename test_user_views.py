"""User View tests."""

import os
from unittest import TestCase

from models import db, connect_db, Message, User, Likes, Follows
from bs4 import BeautifulSoup
from app import app, CURR_USER_KEY

os.environ['DATABASE_URL'] = "postgresql:///warbler-test"


db.create_all()

app.config['WTF_CSRF_ENABLED'] = False


class MessageViewTestCase(TestCase):
    """Test views for messages."""

    def setUp(self):
        db.drop_all()
        db.create_all()
        self.client = app.test_client()
        self.testuser = User.signup(username="testuser",
                                    email="test@test.com",
                                    password="password#",
                                    image_url=None)
        self.testuser_id = 8989
        self.testuser.id = self.testuser_id

        self.u1 = User.signup("testuser1", "test1@test.com", "password#", None)
        self.u1_id = 778
        self.u1.id = self.u1_id
        self.u2 = User.signup("testuser2", "test2@test.com", "password#", None)
        self.u2_id = 884
        self.u2.id = self.u2_id
        self.u3 = User.signup("testuser3", "test3@test.com", "password#", None)
        self.u4 = User.signup("testuser4", "test4@test.com", "password#", None)

        db.session.commit()

    def tearDown(self):
        resp = super().tearDown()
        db.session.rollback()
        return resp

    def test_users_index(self):
        with self.client as c:
            resp = c.get("/users")

            self.assertIn("@testuser", str(resp.data))
            self.assertIn("@testuser1", str(resp.data))
            self.assertIn("@testuser2", str(resp.data))
            self.assertIn("@testuser3", str(resp.data))
            self.assertIn("@testuser4", str(resp.data))

    def test_users_search(self):
        with self.client as c:
            resp = c.get("/users?q=test")

            self.assertIn("@testuser", str(resp.data))
            self.assertIn("@testuser1", str(resp.data))            
            self.assertNotIn("@testuser2", str(resp.data))
            self.assertNotIn("@testuser3", str(resp.data))
            self.assertNotIn("@testuser4", str(resp.data))

    def test_user_show(self):
        with self.client as c:
            resp = c.get(f"/users/{self.testuser_id}")

            self.assertEqual(resp.status_code, 200)

            self.assertIn("@testuser", str(resp.data))

    def test_add_like(self):
        m = Message(id=1984, text="This is a test message.", user_id=self.u1_id)
        db.session.add(m)
        db.session.commit()

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser_id

            resp = c.post("/messages/1984/like", follow_redirects=True)
            self.assertEqual(resp.status_code, 200)

            likes = Likes.query.filter(Likes.message_id==1984).all()
            self.assertEqual(len(likes), 1)
            self.assertEqual(likes[0].user_id, self.testuser_id)

    def setup_followers(self):
        f1 = Follows(user_being_followed_id=self.u1_id, user_following_id=self.testuser_id)
        f2 = Follows(user_being_followed_id=self.u2_id, user_following_id=self.testuser_id)
        f3 = Follows(user_being_followed_id=self.testuser_id, user_following_id=self.u1_id)

        db.session.add_all([f1,f2,f3])
        db.session.commit()

    def test_show_following(self):

        self.setup_followers()
        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser_id

            resp = c.get(f"/users/{self.testuser_id}/following")
            self.assertEqual(resp.status_code, 200)
            self.assertIn("@testuser1", str(resp.data))
            self.assertIn("@testuser2", str(resp.data))
            self.assertNotIn("@testuser3", str(resp.data))
            self.assertNotIn("@testuser4", str(resp.data))

    def test_show_followers(self):

        self.setup_followers()
        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser_id

            resp = c.get(f"/users/{self.testuser_id}/followers")

            self.assertIn("@testuser1", str(resp.data))
            self.assertNotIn("@testuser2", str(resp.data))
            self.assertNotIn("@testuser3", str(resp.data))
            self.assertNotIn("@testuser4", str(resp.data))

    def test_unauthorized_following_page_access(self):
        self.setup_followers()
        with self.client as c:

            resp = c.get(f"/users/{self.testuser_id}/following", follow_redirects=True)
            self.assertEqual(resp.status_code, 200)
            self.assertNotIn("@testuser1", str(resp.data))
            self.assertIn("Access unauthorized", str(resp.data))

    def test_unauthorized_followers_page_access(self):
        self.setup_followers()
        with self.client as c:

            resp = c.get(f"/users/{self.testuser_id}/followers", follow_redirects=True)
            self.assertEqual(resp.status_code, 200)
            self.assertNotIn("@testuser1", str(resp.data))
            self.assertIn("Access unauthorized", str(resp.data))