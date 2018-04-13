# Import statements
import os
import requests
import json
from flask import Flask, render_template, session, redirect, request, url_for, flash
from flask_script import Manager, Shell
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, FileField, PasswordField, BooleanField, SelectMultipleField, ValidationError
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


#association Table between playlists and songs
playlists_collections = db.Table('playlists_collections',db.Column('song_id',db.Integer, db.ForeignKey('songs.id')),db.Column('playlist_id',db.Integer, db.ForeignKey('playlists.id')))



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
    songs = db.relationship('Song',secondary=playlists_collections,backref=db.backref('playlists',lazy='dynamic'),lazy='dynamic') #many to may relationship between songs and playlists (one playlist can result in many songs, but one song can be on many different playlists)
    reviews = db.relationship('PlaylistReviews', backref='Playlist') # one playlist can have many reviews, but the same review cannot be used for other playlists (one to many relationship)

# Song model
class Song(db.Model):
    __tablename__ = 'songs'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128))
    artists = db.Column(db.Integer, db.ForeignKey("artists.id"))

class Artist(db.Model):
    __tablename__ = 'artists'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128))
    songs = db.relationship('Song',backref='Artist') # artists can have multiple songs

class PlaylistReviews(db.Model):
    __tablename__ = 'reviews'
    id = db.Column(db.Integer, primary_key=True)
    review = db.Column(db.String(256))
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    title = db.Column(db.String, db.ForeignKey('playlists.title'))
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
# Update
# Delete





##### Helper functions
### For database additions / get_or_create functions
# def get_spotify(term):
# def get_playlist_info(term):
# def get_playlist_songs_and_artist(tupple):
# def get_or_create_playlist
# def get_or_create_review
# def get_or_create_search_term






##### Routes and view functions #####
@app.route('/login',methods=["GET","POST"])
def login():
    pass #this will be a view function that will allow a user to login (via login form) to the application. it will render_template for login.html
    # return render_template('login.html',form=form)

@app.route('/logout')
@login_required
def logout():
    pass #tis will be a view function that will allow a user to logout and redirect url_for the index view function

    # logout_user()
    # flash('You have been logged out')
    # return redirect(url_for('index'))

@app.route('/register',methods=["GET","POST"])
def register():
    pass #this will be a view function that will allow a user to regiester (via registration form) and will redirect the user to the url_for login and allow the user to login. if the registration is unsuccessful (user already exists, it will render_template for register.html)

    #     flash('You can now log in!')
    #     return redirect(url_for('login'))
    # return render_template('register.html',form=form)

@app.route('/secret')
@login_required
def secret():
    pass #this will make sure that only users can view certain pages
    # return "Only authenticated users can do this! Try to log in or contact the site admin."


@app.route('/', methods=['GET', 'POST'])
def index():
    pass #this will be the home page. here a user will be able to search for a playlist or view previous reviews that users have left for other playlists. after serching, it will redirect url_for search_results. it will render the template for index.html

    #     return redirect(url_for('playlist_results', search_term = search_term))
    # return render_template('index.html',form=form)

@app.route('/playlist_results/<search_term>')
def playlist_results(search_term):
    pass #this will be a view function that returns the names of playlists that were in result of the search term, in the template, you will be able to click on the link and view the playlist's songs

    # return render_template('playlist_results.html',term=term)

@app.route('/playlist_songs/<playlist_name>')
def search_terms():
    pass #this will show the user the songs in a certain playlist. they will also be able to see reviews if a user has left any on this playlist. if they are logged in, they will be able to leave a review this will render url for leave_review
    # return render_template('playlist_songs.html')

# Provided
@app.route('/all_reviews')
def all_reviews():
    pass #this will show you all reviews that have been left by users
    # return render_template('all_reviews.html',all_reviews=reviews)

@app.route('/searched_terms')
def all_searches():
    pass #this will show you all searched terms
    # return render_template('all_searches.html', searches = searches)

@app.route('/leave_review',methods=["GET","POST"])
@login_required
def leave_review():
    pass #a user is required to be logged in to leave a review. they will be able to leave a review and after leaving it will redirect url_for playlist reviews. it will render template for leave_review.html


@app.route('/my_reviews')
@login_required
def my_reviews():
    pass #this view functionw will render a template to allow a user to view their own reviews for playlists
    # return render_template('my_reviews.html', reviews=my_reviews)


if __name__ == '__main__':
    db.create_all()
    manager.run()
