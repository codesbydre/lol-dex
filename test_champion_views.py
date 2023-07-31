#  terminal: 
#  export SQLALCHEMY_DATABASE_URI=postgresql:///lol-dex-test
#  python -m unittest test_champion_views.py
#  WSL: export SQLALCHEMY_DATABASE_URI=postgresql:///lol-dex-test; python -m unittest test_champion_views.py

from unittest import TestCase
from database import db
from models import Champion
from app import app


class ChampionViewsTestCase(TestCase):
    """Test model for champions"""

    def setUp(self):
        """Create test client, add sample data."""
        app.config['SQLALCHEMY_DATABASE_URI'] = "postgresql:///lol-dex-test"
        app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
        app.config['SECRET_KEY'] = "TEST_SECRET_KEY"

        self.client = app.test_client()

        self.app_context = app.app_context()
        self.app_context.push()

        db.create_all()

        # Create sample champions
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

    def tearDown(self):
        """Clean up fouled transactions."""
        db.session.rollback()
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_homepage(self):
        """Test champion homepage is populating correctly"""
        with self.client as c:
            resp = c.get("/")
            self.assertEqual(resp.status_code, 200)

            self.assertIn(self.champion1.name, resp.get_data(as_text=True))
            self.assertIn(self.champion2.name, resp.get_data(as_text=True))

    def test_champion_page(self):
        """Test individual champion page functioning"""
        with self.client as c:
            resp = c.get(f"/champion/{self.champion1.name}")
            self.assertEqual(resp.status_code, 200)

            # Checks if the correct champion details are in the response body
            self.assertIn(self.champion1.name, resp.get_data(as_text=True))
            self.assertIn(self.champion1.role, resp.get_data(as_text=True))
            self.assertIn(self.champion1.title, resp.get_data(as_text=True))
            self.assertIn(self.champion1.description, resp.get_data(as_text=True))

    def test_search_route(self):
        """Test search route"""
        with self.client as c:
            resp = c.get("/search?q=Test")
            self.assertEqual(resp.status_code, 200)
            self.assertIn(self.champion1.name, resp.get_data(as_text=True))
            self.assertIn(self.champion2.name, resp.get_data(as_text=True))

    def test_tag_route(self):
        """Test tag route"""
        with self.client as c:
            resp = c.get("/tag/Tank")
            self.assertEqual(resp.status_code, 200)
            self.assertIn(self.champion1.name, resp.get_data(as_text=True))
            self.assertNotIn(self.champion2.name, resp.get_data(as_text=True))

    
