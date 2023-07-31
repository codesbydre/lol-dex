from database import db, bcrypt
from datetime import datetime

class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String, nullable=False, unique=True)
    email = db.Column(db.String, nullable=False, unique=True)
    password = db.Column(db.String, nullable=False)
    image_url = db.Column(db.String, nullable=True, default='http://ddragon.leagueoflegends.com/cdn/12.6.1/img/profileicon/57.png')
    bio = db.Column(db.Text, nullable=True)
    summoner_name = db.Column(db.String, nullable=True)
    favorites = db.relationship('Favorite', backref='user', lazy=True)
    comments = db.relationship('Comment', backref='user', lazy=True)

    @classmethod
    def signup(cls, username, password, email):
        user = User(
            username=username,
            password=bcrypt.generate_password_hash(password).decode('utf-8'),
            email=email,
        )

        db.session.add(user)
        return user

    @classmethod
    def authenticate(cls, username, password):
        """Validate that user exists & password is correct.

        Return user if valid; else return False.
        """

        user = User.query.filter_by(username=username).first()

        if user and bcrypt.check_password_hash(user.password, password):
            # return user instance
            return user
        else:
            return False

class Champion(db.Model):
    __tablename__ = 'champions'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)
    role = db.Column(db.String)
    tags = db.Column(db.ARRAY(db.String))
    image_url = db.Column(db.String)
    description = db.Column(db.Text) 
    title = db.Column(db.String) 
    difficulty = db.Column(db.Integer)  
    abilities = db.Column(db.JSON)     
    passive = db.Column(db.JSON)   
    allytips = db.Column(db.JSON)      
    enemytips = db.Column(db.JSON) 
    skins = db.Column(db.JSON)
    favorites = db.relationship('Favorite', backref='champion', lazy=True)
    comments = db.relationship('Comment', backref='champion', lazy=True)

class Favorite(db.Model):
    __tablename__ = 'favorites'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    champion_id = db.Column(db.Integer, db.ForeignKey('champions.id'), nullable=False)

class Comment(db.Model):
    __tablename__ = 'comments'

    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.String, nullable=False)
    date = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    champion_id = db.Column(db.Integer, db.ForeignKey('champions.id'), nullable=False)
