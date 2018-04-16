# Import statements
import os
import requests
import json
from flask import Flask, render_template, session, redirect, request, url_for, flash
from flask_script import Manager, Shell
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, FileField, PasswordField, BooleanField, SelectMultipleField, ValidationError, IntegerField
from wtforms.validators import Required, Length, Email, Regexp, EqualTo
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate, MigrateCommand
from werkzeug.security import generate_password_hash, check_password_hash

# Imports for login management
from flask_login import LoginManager, login_required, logout_user, login_user, UserMixin, current_user
from werkzeug.security import generate_password_hash, check_password_hash

# Application configurations
app = Flask(__name__)
app.debug = True
app.config['SECRET_KEY'] = 'hardtoguessstringfromsi364thisisnotsupersecurebutitsok'
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get('DATABASE_URL') or "postgresql://localhost/SI364projectplanSADIES"
app.config['SQLALCHEMY_COMMIT_ON_TEARDOWN'] = True
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Set up Flask debug stuff
manager = Manager(app)
db = SQLAlchemy(app)
migrate = Migrate(app, db)
manager.add_command('db', MigrateCommand) # Add migrate command to manager

# Login configurations setup
login_manager = LoginManager()
login_manager.session_protection = 'strong'
login_manager.login_view = 'login'
login_manager.init_app(app) # set up login manager

#spotify api
client_id = '2efb491c8f8b49e6825224f3491a1e6e'
client_secret = '828d2c8abb9f407489ea390451d5d9fb'

#########################
##### Set up Models #####
#########################

# Association table #
#association Table between search terms and playlists
searched_playlists = db.Table('searched_playlists', db.Column('search_id', db.Integer, db.ForeignKey('search_term.id')), db.Column('playlist_id', db.Integer, db.ForeignKey('playlists.id')))


# Models #

# Special model for users to log in
class User(UserMixin, db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(255), unique=True, index=True)
    email = db.Column(db.String(64), unique=True, index=True)
    password_hash = db.Column(db.String(128))

    @property
    def password(self):
        raise AttributeError('password is not a readable attribute')

    @password.setter
    def password(self, password):
        self.password_hash = generate_password_hash(password)

    def verify_password(self, password):
        return check_password_hash(self.password_hash, password)

# Playlist model
class Playlist(db.Model):
    __tablename__ = "playlists"
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(64),unique=True)
    pictureURL = db.Column(db.String(256))
    reviews = db.relationship('PlaylistReviews', backref='Playlist') # one playlist can have many reviews, but the same review cannot be used for other playlists (one to many relationship)

    def __repr__(self): #__repr__ method that shows the title and the URL of the gif
        return "{}, URL: {}".format(self.title,self.pictureURL)

class PlaylistReviews(db.Model):
    __tablename__ = 'reviews'
    id = db.Column(db.Integer, primary_key=True)
    review = db.Column(db.String(256))
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    stars = db.Column(db.Integer())
    playlist = db.Column(db.Integer, db.ForeignKey("playlists.id"))

class SearchTerm(db.Model):
    __tablename__ = 'search_term'
    id = db.Column(db.Integer, primary_key=True)
    term = db.Column(db.String(32), unique=True)
    playlists = db.relationship('Playlist', secondary=searched_playlists, backref=db.backref('search_term', lazy='dynamic'), lazy='dynamic') #many to many relationship with playlists (a search will generate many playlists to save, and one playlist could potentially appear in many searches)
    def __repr__(self):
        return "{}".format(self.term) #__repr__ method that returns the term string


##### Set up Forms #####
# Registration
class RegistrationForm(FlaskForm):
    email = StringField('Email:', validators=[Required(),Length(1,64),Email()])
    username = StringField('Username:',validators=[Required(),Length(1,64),Regexp('^[A-Za-z][A-Za-z0-9_.]*$',0,'Usernames must have only letters, numbers, dots or underscores')])
    password = PasswordField('Password:',validators=[Required(),EqualTo('password2',message="Passwords must match")])
    password2 = PasswordField("Confirm Password:",validators=[Required()])
    submit = SubmitField('Register User')

    #Additional checking methods for the form
    def validate_email(self,field):
        if User.query.filter_by(email=field.data).first():
            raise ValidationError('Email already registered.')

    def validate_username(self,field):
        if User.query.filter_by(username=field.data).first():
            raise ValidationError('Username already taken')

# Login
class LoginForm(FlaskForm):
    email = StringField('Email', validators=[Required(), Length(1,64), Email()])
    password = PasswordField('Password', validators=[Required()])
    remember_me = BooleanField('Keep me logged in')
    submit = SubmitField('Log In')

# Search for a playlist
class PlaylistSearchForm(FlaskForm):
    search = StringField("Enter a term to search for a playlist", validators=[Required()])
    submit = SubmitField('Submit')

# Leave a review
class LeaveReviewForm(FlaskForm):
    review = StringField("Enter a review for this playlist", validators=[Required(),Length(max=300, message="The review cannot be longer than 300 characters!")])
    stars = IntegerField("Rate the movie out of 5 stars ",validators=[Required()])
    submit = SubmitField("Submit your review")

    def validate_stars(form, field):
        if len(str(field.data)) > 1 :
            raise ValidationError('Have to be full numbers, no decimals for star rating')

# Update
# Delete





##### Helper functions
### For database additions / get_or_create functions
#in this function, you will pass in a term/phrase of what type/kind of playlist you are looking for. it will then return a search object with a dictionary of playlist information
def spotify_search(term):
    oauth_token = "BQD9dTfBQLNX2Ci2HyLSRME9vCIlmtFuYPZFPVZhNkxrv1E0DOTPsEJNFu8gtOxBDfaLS9Xb51NZJ4RMpvmx7CP1ZN7NzFJQKQYLzI61FZc0B85Fzgv32YomBLxLlB2oA3i5Fs56VWDE7Le6A_QO-cMy1j98wFKWrjY" #oauth token for spotify
    headers ={"Content-Type": "application/json", "Authorization": "Bearer " + oauth_token}
    params = { 'q': term, 'type': 'playlist', 'limit':'10'} #q is any term that will be used to get a playlsit
    search_object = requests.get('https://api.spotify.com/v1/search?', headers=headers, params = params).json() #search object
    playlists = search_object['playlists']['items'] #get the playlist items
    return(playlists)

#this function will take in a term and then use the get_spotify function to recieve list of tupples for each playlist. each tupple will contain a playlist's name, id, and user_id
def list_of_playlist_tupples(term):
    list_of_playlist_dicts = spotify_search(term)
    list_of_playlist_info = []
    for item in list_of_playlist_dicts:
        playlist_name = item['name']
        playlist_id = item['id']
        user_id = item['owner']['id']
        pictureURL = item['images'][0]['url']
        list_of_playlist_info.append((playlist_name,playlist_id, user_id, pictureURL))
    return(list_of_playlist_info)

#this function will use a tupple (containing playlist name, id, and user_id) and make another request to spotify to get the tracks and artists for each playlist
def get_playlist_songs_and_artist(tupple):
    songs_and_artists = []
    oauth_token = "BQAVhLvaDkhPII_qNBURcrjL0B4T-038NOG5i96cttghdFZnrzlABEueS--puYg33Yx0op6ccX7YNTHjc3gGv26VAkD2H0XtOqv7blYzM3tQ3JxeHWcEd77XAbog_Aap5CMWQiWmnY15oNd65PlbFFc3WdKLYqpolTI" #you need to generate the OAuth token from https://beta.developer.spotify.com/console/get-search-item/
    headers ={"Content-Type": "application/json", "Authorization": "Bearer " + oauth_token}
    search_object = requests.get('https://api.spotify.com/v1/users/'+tupple[2]+'/playlists/'+tupple[1]+'/tracks', headers=headers).json()['items']#[0]['track']
    for item in search_object:
        song = item['track']['name']
        all_artists = item['track']['artists']
        artist_list = []
        for a in all_artists:
            artist = a['name']
            artist_list.append(artist)
        tup = (song,artist_list)
        songs_and_artists.append(tup)
    return(songs_and_artists)


def get_or_create_playlist(title, pictureURL):
    playlist = Playlist.query.filter_by(title=title).first()
    if playlist:
        return playlist
    else:
        playlist = Playlist(title=title, pictureURL=pictureURL)
        db.session.add(playlist)
        db.session.commit()
        return playlist

def get_or_create_search_term(term):
    search_term = SearchTerm.query.filter_by(term=term).first()
    if search_term:
        print("Found term")
        return search_term
    else:
        print("Adding term")
        search_term = SearchTerm(term=term)
        playlists_search = list_of_playlist_tupples(term)
        for playlist in playlists_search:
            title=playlist[0]
            pictureURL = playlist[3]
            new_playlist = get_or_create_playlist(title, pictureURL)
            search_term.playlists.append(new_playlist)
        db.session.add(search_term)
        db.session.commit()
        return search_term


# def get_or_create_review ?????



##### Routes and view functions #####
@app.route('/login',methods=["GET","POST"])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user is not None and user.verify_password(form.password.data):
            login_user(user, form.remember_me.data)
            return redirect(request.args.get('next') or url_for('index'))
        flash('We cannot find this account, please register.')
    return render_template('login.html',form=form)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out')
    return redirect(url_for('index'))

@app.route('/register',methods=["GET","POST"])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(email=form.email.data,username=form.username.data,password=form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('You can now log in!')
        return redirect(url_for('login'))
    return render_template('register.html',form=form)

@app.route('/secret')
@login_required
def secret():
    return "Only authenticated users can do this! Try to log in or contact the site admin."


@app.route('/', methods=['GET', 'POST'])
def index():
    form = PlaylistSearchForm()
    if form.validate_on_submit():
        search_term = form.search.data
        term = get_or_create_search_term(search_term)
        return redirect(url_for('playlist_results',search_term=search_term))
    return render_template('index.html', form=form)


@app.route('/playlist_results/<search_term>')
def playlist_results(search_term):
    term = SearchTerm.query.filter_by(term=search_term).first()
    relevant_playlists = term.playlists.all()
    return render_template('searched_playlists.html', playlists = relevant_playlists, term = term)

@app.route('/playlist_songs/<playlist_name>')
def playlist_songs(playlist_name):
    pass #this will show the user the songs in a certain playlist. they will also be able to see reviews if a user has left any on this playlist. if they are logged in, they will be able to leave a review this will render url for leave_review it will use get_playlist_songs_and_artist
    # return render_template('playlist_songs.html')

# Provided
@app.route('/all_reviews')
def all_reviews():
    pass #this will show you all reviews that have been left by users
    # return render_template('all_reviews.html',all_reviews=reviews)

@app.route('/searched_terms')
def all_searches():
    all_terms = SearchTerm.query.all()
    return render_template('search_terms.html', all_terms = all_terms)

@app.route('/leave_review',methods=["GET","POST"])
@login_required
def leave_review():
    pass #a user is required to be logged in to leave a review. they will be able to leave a review and after leaving it will redirect url_for playlist reviews. it will render template for leave_review.html


# @app.route('/my_reviews')
# @login_required
# def my_reviews():
#     pass #this view functionw will render a template to allow a user to view their own reviews for playlists
#     # return render_template('my_reviews.html', reviews=my_reviews)

@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html')

@app.errorhandler(500)
def page_not_found(e):
    return render_template('500.html')

if __name__ == '__main__':
    db.create_all()
    manager.run()
