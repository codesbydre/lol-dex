#  terminal: 
#  export SQLALCHEMY_DATABASE_URI=postgresql:///lol-dex-test
#  python -m unittest test_user_model.py
#  WSL: export SQLALCHEMY_DATABASE_URI=postgresql:///lol-dex-test; python -m unittest test_user_model.py

from unittest import TestCase
from sqlalchemy.exc import IntegrityError
from flask import Flask
from database import db, bcrypt
from models import Champion, User, Favorite, Comment


class UserModelTestCase(TestCase):
    """Test model for users"""

    def setUp(self):
        """Create test client, add sample data."""
        app = Flask(__name__)
        app.config['SQLALCHEMY_DATABASE_URI'] = "postgresql:///lol-dex-test"
        app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
        app.config['SECRET_KEY'] = "TEST_SECRET_KEY"

        db.init_app(app)
        bcrypt.init_app(app)

        self.client = app.test_client()

        self.app_context = app.app_context()
        self.app_context.push()

        db.create_all()

        self.user1 = User.signup("testuser1", "Abcdefg123!", "testuser1@email.com")
        self.user2 = User.signup("testuser2", "Hijklmn345@", "testuser2@email.com")
        db.session.commit()

    def tearDown(self):
        """Clean up fouled transactions."""
        db.session.rollback()

        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_user_model(self):
        """Does the User model work?"""
        self.assertEqual(len(User.query.all()), 2)

    def test_user_signup(self):
        """Does signup method correctly?"""
        user3 = User.signup("testuser3", "password", "testuser3@email.com")
        db.session.commit()

        self.assertEqual(len(User.query.all()), 3)
        self.assertEqual(user3.username, "testuser3")

    def test_user_authenticate(self):
        """Does authenticate method work correctly?"""
        user = User.authenticate("testuser1", "Abcdefg123!")

        self.assertIsNotNone(user)
        self.assertEqual(user.username, "testuser1")

        bad_user = User.authenticate("testuser1", "wrongpassword")
        self.assertFalse(bad_user)

    def test_unique_username(self):
        """Does the model correctly prevent duplicate usernames?"""
        with self.assertRaises(IntegrityError):
            duplicate_user = User.signup("testuser1", "password", "duplicate@email.com")
            db.session.commit()

    def test_unique_email(self):
        """Does the model correctly prevent duplicate emails?"""
        with self.assertRaises(IntegrityError):
            duplicate_user = User.signup("differentuser", "password", "testuser1@email.com")
            db.session.commit()

    def test_user_favorite_relationship(self):
        """Does the Favorite relationship in the User model work?"""
        champion = Champion(name="Test Champion", role="Role", tags=["Tag 1", "Tag 2"],
                            image_url="http://example.com/test_champ.png",
                            description="Test Champion description",
                            title="Test Champion title",
                            difficulty=3, abilities={}, passive={}, allytips={}, enemytips={}, skins={})
        db.session.add(champion)
        db.session.commit()

        favorite = Favorite(user_id=self.user1.id, champion_id=champion.id)
        db.session.add(favorite)
        db.session.commit()

        self.assertEqual(len(self.user1.favorites), 1)
        self.assertEqual(self.user1.favorites[0].champion_id, champion.id)

    def test_user_comment_relationship(self):
        """Does the Comment relationship in the User model work?"""
        champion = Champion(name="Test Champion", role="Role", tags=["Tag 1", "Tag 2"],
                            image_url="http://example.com/test_champ.png",
                            description="Test Champion description",
                            title="Test Champion title",
                            difficulty=3, abilities={}, passive={}, allytips={}, enemytips={}, skins={})
        db.session.add(champion)
        db.session.commit()

        comment = Comment(content="Test comment", user_id=self.user1.id, champion_id=champion.id)
        db.session.add(comment)
        db.session.commit()

        self.assertEqual(len(self.user1.comments), 1)
        self.assertEqual(self.user1.comments[0].content, "Test comment")
        self.assertEqual(self.user1.comments[0].champion_id, champion.id)