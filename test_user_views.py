#  terminal: 
#  export SQLALCHEMY_DATABASE_URI=postgresql:///lol-dex-test
#  python -m unittest test_user_views.py
#  WSL: export SQLALCHEMY_DATABASE_URI=postgresql:///lol-dex-test; python -m unittest test_user_views.py

from unittest import TestCase
from database import db, bcrypt
from models import Champion, User, Comment, Favorite
from flask import session
from app import app, CURR_USER_KEY

class UserViewsTestCase(TestCase):
    """Test model for champions"""

    def setUp(self):
        """Create test client, add sample data."""
        app.config['SQLALCHEMY_DATABASE_URI'] = "postgresql:///lol-dex-test"
        app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
        app.config['SECRET_KEY'] = "TEST_SECRET_KEY"
        app.config['WTF_CSRF_ENABLED'] = False

        self.client = app.test_client()

        self.app_context = app.app_context()
        self.app_context.push()

        db.create_all()

        self.user1 = User.signup("testuser1", "Abcdefg123!", "testuser1@email.com")
        self.user2 = User.signup("testuser2", "Hijklmn345@", "testuser2@email.com")
        db.session.commit()

        champion1 = Champion(
            name="Test Champion 1", 
            role="Tank", 
            tags=["Tank", "Fighter"],
            image_url="http://example.com/test_champ_1.png",
            description="Test Champion 1 description",
            title="Test Champion 1 title",
            difficulty=3,
            abilities=[{"id": 1, "name": "Ability 1", "description": "Description 1"}, {"id": 2, "name": "Ability 2", "description": "Description 2"}, {"id": 3, "name": "Ability 3", "description": "Description 3"},{"id": 4, "name": "Ability 4", "description": "Description 4"}],
            skins= [
                {
                    "id": "266000",
                    "num": 0,
                    "name": "default",
                }]
                
        )

        champion2 = Champion(
            name="Test Champion 2", 
            role="Mage", 
            tags=["Mage", "Support"],
            image_url="http://example.com/test_champ_2.png",
            description="Test Champion 2 description",
            title="Test Champion 2 title",
            difficulty=8,
            abilities=[{"id": 1, "name": "Ability 1", "description": "Description 1"}, {"id": 2, "name": "Ability 2", "description": "Description 2"},{"id": 3, "name": "Ability 3", "description": "Description 3"},{"id": 4, "name": "Ability 4", "description": "Description 4"}],
               skins= [
                {
                    "id": "366000",
                    "num": 0,
                    "name": "default"
                }]
        )

        db.session.add(champion1)
        db.session.add(champion2)
        db.session.commit()

        self.champion1 = champion1
        self.champion2 = champion2
        db.session.commit()

    def tearDown(self):
        """Clean up fouled transactions."""
        db.session.rollback()
        db.session.remove()
        db.drop_all()
        self.app_context.pop()
    
    def login(self, username):
        with self.client as c:
            with c.session_transaction() as sess:
                user = User.query.filter(User.username == username).first()
                sess[CURR_USER_KEY] = user.id


    def test_show_profile(self):
        """Test showing a user's profile"""

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.user1.id
            
            resp = c.get(f"/profile/{self.user1.username}")

            self.assertEqual(resp.status_code, 200)

            self.assertIn("testuser1@email.com", str(resp.data)) 
            self.assertIn("testuser1", str(resp.data))

    def test_edit_profile(self):
        """Test editing a user's profile"""

        self.login("testuser1")

        with self.client as c:
            resp = c.get(f"/profile/{self.user1.username}/edit")
            self.assertEqual(resp.status_code, 200)
            self.assertIn('Edit Profile', str(resp.data))
            
            updated_data = {
                "bio": "Updated bio",
                "summoner_name": "UpdatedSummoner",
            }

            resp = c.post(f"/profile/{self.user1.username}/edit", data=updated_data, follow_redirects=True)

            self.assertEqual(resp.status_code, 200)
            
            user = User.query.filter_by(username=self.user1.username).first()
            
            # Check the update in the database
            self.assertEqual(user.bio, updated_data["bio"])
            self.assertEqual(user.summoner_name, updated_data["summoner_name"])

            self.assertIn(updated_data["bio"], str(resp.data))
            self.assertIn(updated_data["summoner_name"], str(resp.data))

    def test_show_favorites(self):
        """Test showing a user's favorite champions"""
        
        self.login("testuser1")

        favorite1 = Favorite(user_id=self.user1.id, champion_id=self.champion1.id)
        favorite2 = Favorite(user_id=self.user1.id, champion_id=self.champion2.id)

        db.session.add(favorite1)
        db.session.add(favorite2)
        db.session.commit()

        with self.client as c:
            resp = c.get(f"/profile/{self.user1.username}/favorites")
            
            self.assertEqual(resp.status_code, 200)
            self.assertIn("Test Champion 1", str(resp.data)) 
            self.assertIn("Test Champion 2", str(resp.data)) 
                
    def test_show_favorites_no_favorites(self):
        """Test showing a user's favorite champions when they have no favorites"""
        
        self.login("testuser1")

        with self.client as c:
            resp = c.get(f"/profile/{self.user1.username}/favorites")
            
            self.assertEqual(resp.status_code, 200)
            self.assertIn("No favorites added yet", str(resp.data)) 

    def test_show_comments(self):
        """Test showing a user's comments"""

        self.login("testuser1")

        comment1 = Comment(content="This is a test comment 1", user_id=self.user1.id, champion_id=self.champion1.id)
        comment2 = Comment(content="This is a test comment 2", user_id=self.user1.id, champion_id=self.champion2.id)

        db.session.add(comment1)
        db.session.add(comment2)
        db.session.commit()

        with self.client as c:
            resp = c.get(f"/profile/{self.user1.username}/comments")
            
            self.assertEqual(resp.status_code, 200)
            self.assertIn("This is a test comment 1", str(resp.data)) 
            self.assertIn("This is a test comment 2", str(resp.data)) 
                
    def test_show_comments_no_comments(self):
        """Test showing a user's comments when they have no comments"""
        
        self.login("testuser1")

        with self.client as c:
            resp = c.get(f"/profile/{self.user1.username}/comments")
            
            self.assertEqual(resp.status_code, 200)
            self.assertIn("No comments found.", str(resp.data)) 



    
