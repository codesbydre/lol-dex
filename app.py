from flask import Flask, request, jsonify, render_template, flash, redirect, url_for, session, g
from database import db, bcrypt
from sqlalchemy.exc import IntegrityError
from werkzeug.utils import secure_filename
from models import Champion, User, Favorite, Comment
from forms import SignupForm, LoginForm, UserEditForm, CommentForm
from riotwatcher import LolWatcher
from api_keys import RIOT_API_KEY, SECRET_KEY
import requests

CURR_USER_KEY = "curr_user"

API_URL = "https://ddragon.leagueoflegends.com/cdn/13.14.1"
lol_watcher = LolWatcher(RIOT_API_KEY)

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql:///lol-dex'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = SECRET_KEY

db.init_app(app)
bcrypt.init_app(app) 

#########################################################################
# Get API data to populate database, call command `flask seeddb` in Terminal to initialize
def get_profile_icons():
    response = requests.get(f'{API_URL}/data/en_US/profileicon.json')
    profile_icons = response.json()['data']
    return profile_icons

def get_champion_data():
    try:
        # Fetch the list of all champions
        response = requests.get(f'{API_URL}/data/en_US/champion.json')
        champion_list = response.json()['data']

        # Fetch detailed data for each champion
        champions_data = {}
        for champion_name, _ in champion_list.items():
            response = requests.get(f'{API_URL}/data/en_US/champion/{champion_name}.json')
            champions_data[champion_name] = response.json()['data'][champion_name]
        
        return champions_data
    except Exception as err:
        print(f"An error occurred while fetching data from Riot API: {err}")


def populate_champions():
    champions_data = get_champion_data()
    for champion_name, info in champions_data.items():
        image_url = f"https://ddragon.leagueoflegends.com/cdn/img/champion/splash/{info['id']}_0.jpg"
        champion = Champion.query.filter_by(name=champion_name).first()
        description = info.get('lore', info.get('blurb', 'No description available'))
       
        difficulty = info.get('info', {}).get('difficulty')  

        skins = info.get('skins', [])                      
        for skin in skins:
            skin_url = f"http://ddragon.leagueoflegends.com/cdn/img/champion/splash/{info['id']}_{skin.get('num', '0')}.jpg"
            skin['url'] = skin_url
        
        abilities = info.get('spells', [])                      
        for ability in abilities:
            ability_image = ability.get('image', {})
            ability_image_url = f"{API_URL}/img/{ability_image.get('group', '')}/{ability_image.get('full', '')}"
            ability['image_url'] = ability_image_url
        
        passive = info.get('passive', {})
        passive_image = passive.get('image', {})
        passive_image_url = f"{API_URL}/img/{passive_image.get('group', '')}/{passive_image.get('full', '')}"
        passive['image_url'] = passive_image_url
        info['passive'] = passive

        allytips = info.get('allytips')                      
        enemytips = info.get('enemytips')                    

        if champion:
            champion.role = info['tags'][0]
            champion.tags = info['tags']
            champion.image_url = image_url
            champion.description = description
            champion.title = info.get('title', '')
            champion.difficulty = difficulty
            champion.abilities = abilities
            champion.passive = info.get('passive')
            champion.allytips = allytips
            champion.enemytips = enemytips
            champion.skins = skins
        else:
            champion = Champion(name=champion_name, role=info['tags'][0], tags=info['tags'],
                                image_url=image_url, description=description,
                                title=info.get('title', ''), difficulty=difficulty,
                                abilities=abilities, passive=info.get('passive'),
                                allytips=allytips, enemytips=enemytips, skins=skins)
            db.session.add(champion)
    try:
        db.session.commit()
    except Exception as e:
        print(f"An error occurred while updating the champions: {e}")
        db.session.rollback()

def seed_database():
    with app.app_context():
        db.create_all()  
        populate_champions()  

@app.cli.command("seeddb")
def seed_database_command():
    """Seeds the database."""
    seed_database()
    print("Seeded the database.")

###########################################################################
# User signup/login/logout 
@app.before_request
def add_user_to_g():
    """If we're logged in, add curr user to Flask global."""
    if CURR_USER_KEY in session:
        g.user = User.query.get(session[CURR_USER_KEY])
    else:
        g.user = None



def do_login(user):
    """Log in user."""

    session[CURR_USER_KEY] = user.id
    flash(f"Hello, {user.username}!", "success")

def do_logout():
    """Logout user."""

    if CURR_USER_KEY in session:
        del session[CURR_USER_KEY]
        flash("You have been successfully logged out.", "info")

@app.route('/signup', methods=["GET", "POST"])
def signup():
    """Handle user signup."""
    form = SignupForm()
    if form.validate_on_submit():
        try:
            user = User.signup(
                username=form.username.data,
                password=form.password.data,
                email=form.email.data,
            )
            db.session.commit()

        except IntegrityError:
            flash("Username already taken", 'danger')
            return render_template('signup.html', form=form)

        flash('New user has been created!', 'primary')
        do_login(user)

        return redirect("/")

    else:
        return render_template('signup.html', form=form)
    
@app.route('/login', methods=["GET", "POST"])
def login():
    """Handle user login."""

    form = LoginForm()

    if form.validate_on_submit():
        user = User.authenticate(form.username.data,
                                 form.password.data)

        if user:
            do_login(user)
            return redirect("/")

        flash("Invalid credentials.", 'danger')

    return render_template('login.html', form=form)

@app.route('/logout')
def logout():
    """Handle logout of user."""

    do_logout()
    return redirect('/')

###########################################################################
# User routes
@app.route('/profile/<string:username>', methods=["GET"])
def profile(username):
    """Show user profile"""
    user = User.query.filter_by(username=username).first()
    if user is None:
        return render_template('404.html'), 404
    favorites = Favorite.query.filter_by(user_id=user.id).all()
    return render_template('profile.html', user=user, favorites=favorites)

@app.route('/profile/<string:username>/edit', methods=["GET", "POST"])
def edit_profile(username):
    """Edit user profile"""
    if g.user is None or g.user.username != username:
        flash("You are not authorized to edit this profile.", "danger")
        return redirect('/')
    
    user = User.query.filter_by(username=username).first()
    if user is None:
        return render_template('404.html'), 404

    form = UserEditForm(obj=user)
    if form.validate_on_submit():
        user.image_url = form.image_url.data or user.image_url
        user.bio = form.bio.data or user.bio
        user.summoner_name = form.summoner_name.data or user.summoner_name
        db.session.commit()
        flash('Profile has been updated!', 'primary')   
        return redirect(url_for('profile', username=username)) 

    return render_template('edit_profile.html', form=form, user=user)

@app.route('/favorites')
def favorites():
    """Show user's favorite champions (current user)"""
    if g.user is None:
        flash("You must be logged in to view your favorites.", "info")
        return redirect('/')
    
    favorites = Favorite.query.filter_by(user_id=g.user.id).all()
    return render_template('favorites.html', favorites=favorites)

@app.route('/profile/<string:username>/favorites', methods=["GET"])
def profile_favorites(username):
    """Show user's favorite champions (another user)"""
    user = User.query.filter_by(username=username).first()
    if user is None:
        return render_template('404.html'), 404
    favorites = Favorite.query.filter_by(user_id=user.id).all()
    return render_template('favorites.html', favorites=favorites)

@app.route('/comments', methods=["GET"])
def my_comments():
    """Show current user's comments (current user)"""
    if g.user is None:
        flash("You must be logged in to view your comments.", "info")
        return redirect('/')
    
    comments = Comment.query.filter_by(user_id=g.user.id).all()
    return render_template('comments.html', comments=comments)

@app.route('/profile/<string:username>/comments', methods=["GET"])
def profile_comments(username):
    """Show a user's comments (another user)"""
    user = User.query.filter_by(username=username).first()
    if user is None:
        return render_template('404.html'), 404
    comments = Comment.query.filter_by(user_id=user.id).all()
    return render_template('comments.html', comments=comments, username=username)

#########################################################################
# Champion detail, favoriting, commenting 
@app.route('/champion/<string:name>')
def champion(name):
    """Show champion detail page"""
    champion = Champion.query.filter_by(name=name).first()
    difficulty_percentage = champion.difficulty * 10
    form = CommentForm()
    if champion is None:
        return render_template('404.html'), 404
    
    is_favorited = False
    if g.user:
        favorite = Favorite.query.filter_by(user_id=g.user.id, champion_id=champion.id).first()
        if favorite:
            is_favorited = True

    return render_template('champion.html', champion=champion, is_favorited=is_favorited, form=form, difficulty_percentage=difficulty_percentage)


@app.route('/favorite/<int:champion_id>', methods=["POST"])
def favorite_champion(champion_id):
    """Add/remove favorite champion for current user"""
    if g.user is None:
        return jsonify({'message': 'User not authenticated', 'is_authenticated': False}), 401

    champion = Champion.query.get_or_404(champion_id)

    favorite = Favorite.query.filter_by(user_id=g.user.id, champion_id=champion.id).first()

    if favorite:
        db.session.delete(favorite)
        db.session.commit()
        return jsonify({'is_favorited': False, 'is_authenticated': True})

    favorite = Favorite(user_id=g.user.id, champion_id=champion.id)
    db.session.add(favorite)
    db.session.commit()
    return jsonify({'is_favorited': True, 'is_authenticated': True})


@app.route('/champion/<string:name>/comment', methods=['POST'])
def comment(name):
    """Add a comment to a champion."""
    if g.user is None:
        flash("You must be logged in to comment.", "info")
        return redirect(f'/champion/{name}')

    form = CommentForm()
    if form.validate_on_submit():
        comment = Comment(
            content=form.content.data,
            user_id=g.user.id,
            champion_id=Champion.query.filter_by(name=name).first().id
        )
        db.session.add(comment)
        db.session.commit()
        flash("Your comment has been posted.", "success")
    else:
        flash("There was an error with your comment.", "danger")
    return redirect(f'/champion/{name}')

###########################################################################
# Homepage and other routes
@app.route('/')
def homepage():
    """Show homepage"""
    champions = Champion.query.all() 
    
    return render_template('home.html', champions=champions) 


@app.route('/search')
def search():
    """Search for champion by name"""
    query = request.args.get('q')
    if not query:
        return jsonify([])
    champions = Champion.query.filter(Champion.name.ilike(f'%{query}%')).all()
    return jsonify([champion.name for champion in champions])

@app.route('/tag/<string:tag_name>')
def tag(tag_name):
    """Show all champions with a specific tag."""
    champions = Champion.query.filter(Champion.tags.any(tag_name)).all()
    if not champions:
        return render_template('404.html'), 404
    return render_template('tag.html', champions=champions, tag=tag_name)

@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

#########################################################################

def slugify(s):
    """Transform string to simplified URL friendly format"""
    return secure_filename(s).replace(' ', '_').lower()

app.jinja_env.filters['slugify'] = slugify


def contains(container, value):
    """For multiple carousel use on homepage"""
    return value in container

app.jinja_env.tests['contains'] = contains


if __name__ == '__main__':
    app.run()
