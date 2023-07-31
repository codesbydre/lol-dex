#  terminal: 
#  export SQLALCHEMY_DATABASE_URI=postgresql:///lol-dex-test
#  python -m unittest test_champion_model.py
#  WSL: export SQLALCHEMY_DATABASE_URI=postgresql:///lol-dex-test; python -m unittest test_champion_model.py

from unittest import TestCase
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm.collections import InstrumentedList
from flask import Flask
from database import db, bcrypt
from models import Champion, User, Favorite, Comment


class ChampionModelTestCase(TestCase):
    """Test model for champions"""

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

        champion1 = Champion(name="Test Champion 1", role="Role 1", tags=["Tag 1", "Tag 2"],
                             image_url="http://example.com/test_champ_1.png",
                             description="Test Champion 1 description",
                             title="Test Champion 1 title",
                             difficulty=3, abilities={}, passive={}, allytips={}, enemytips={}, skins={})

        champion2 = Champion(name="Test Champion 2", role="Role 2", tags=["Tag 3", "Tag 4"],
                             image_url="http://example.com/test_champ_2.png",
                             description="Test Champion 2 description",
                             title="Test Champion 2 title",
                             difficulty=5, abilities={}, passive={}, allytips={}, enemytips={}, skins={})

        db.session.add(champion1)
        db.session.add(champion2)
        db.session.commit()

        self.champion1 = champion1
        self.champion2 = champion2

    def tearDown(self):
        """Clean up fouled transactions."""

        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_champion_model(self):
        """Does the Champion model work?"""
        self.assertEqual(len(Champion.query.all()), 2)

        self.assertEqual(Champion.query.get(self.champion1.id).name, "Test Champion 1")
        self.assertEqual(Champion.query.get(self.champion2.id).name, "Test Champion 2")

    def test_champion_datatypes(self):
        """Does the Champion model have correct data types for properties?"""
        champion = Champion.query.get(self.champion1.id)

        self.assertIsInstance(champion.name, str)
        self.assertIsInstance(champion.role, str)
        self.assertIsInstance(champion.tags, list)
        self.assertIsInstance(champion.image_url, str)
        self.assertIsInstance(champion.description, str)
        self.assertIsInstance(champion.title, str)
        self.assertIsInstance(champion.difficulty, int)
        self.assertIsInstance(champion.abilities, dict)
        self.assertIsInstance(champion.passive, dict)
        self.assertIsInstance(champion.allytips, dict)
        self.assertIsInstance(champion.enemytips, dict)
        self.assertIsInstance(champion.skins, dict)

        self.assertIsInstance(champion.favorites, InstrumentedList)
        self.assertIsInstance(champion.comments, InstrumentedList)

    def test_champion_required_name(self):
        """Does Champion model enforce name being non-nullable?"""
        with self.assertRaises(IntegrityError):
            bad_champion = Champion(role="Role 3")
            db.session.add(bad_champion)
            db.session.commit()
    
    def test_champion_update(self):
        """Can we update a Champion instance?"""
        champion = Champion.query.get(self.champion1.id)
        champion.name = "Updated Test Champion 1"
        db.session.commit()

        self.assertEqual(champion.name, "Updated Test Champion 1")

    def test_champion_delete(self):
        """Can we delete a Champion instance?"""
        db.session.delete(self.champion1)
        db.session.commit()

        self.assertEqual(len(Champion.query.all()), 1)

    def test_champion_favorite_relationship(self):
        """Does the Favorite relationship in the Champion model work?"""
        user = User.signup("test_user", "password", "test_user@email.com")
        db.session.add(user)
        db.session.commit()

        favorite = Favorite(user_id=user.id, champion_id=self.champion1.id)
        db.session.add(favorite)
        db.session.commit()

        self.assertEqual(len(self.champion1.favorites), 1)
        self.assertEqual(self.champion1.favorites[0].user_id, user.id)

    def test_champion_comment_relationship(self):
        """Does the Comment relationship in the Champion model work?"""
        user = User.signup("test_user", "password", "test_user@email.com")
        db.session.add(user)
        db.session.commit()

        comment = Comment(content="Test comment", user_id=user.id, champion_id=self.champion1.id)
        db.session.add(comment)
        db.session.commit()

        self.assertEqual(len(self.champion1.comments), 1)
        self.assertEqual(self.champion1.comments[0].content, "Test comment")
        self.assertEqual(self.champion1.comments[0].user_id, user.id)
