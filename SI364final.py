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
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get('DATABASE_URL') or "postgresql://localhost/SI364finalSADIES"
app.config['SQLALCHEMY_COMMIT_ON_TEARDOWN'] = True
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['HEROKU_ON'] = os.environ.get('HEROKU')

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
oauth_token = 'BQDtSbKCPKIgnW3ns2YfbFu8NRKGW7XxCmCjSiB_nZXOZtdAhMuuNlfXC572iPOZfYnLCEbxqgPWDDkdz1yGT7-wkNxqVTO06Jf-GGhj1ivYDwoZWVppP_5juipzHRJHaRMTFvj3hMiVGTzy6TwibcbLOZcdBXPCdI4'

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


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id)) # returns User object or None

# Playlist model
class Playlist(db.Model):
    __tablename__ = "playlists"
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(64),unique=True)
    spotify_id = db.Column(db.String())
    user_id = db.Column(db.String())
    pictureURL = db.Column(db.String(256))
    reviews = db.relationship('PlaylistReviews', backref='Playlist') # one playlist can have many reviews, but the same review cannot be used for other playlists (one to many relationship)

    def __repr__(self): #__repr__ method that shows the title and the URL of the gif
        return "{}, URL: {}".format(self.title,self.pictureURL)

class PlaylistReviews(db.Model):
    __tablename__ = 'reviews'
    id = db.Column(db.Integer, primary_key=True)
    review = db.Column(db.String(256))
    username = db.Column(db.String, db.ForeignKey('users.username'))
    stars = db.Column(db.Integer())
    playlist = db.Column(db.String, db.ForeignKey("playlists.title"))

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

    def validate_seach(form, field):
        if len(field.data) = 0  :
            raise ValidationError('Have to search for something to use this!')


# Leave a review
class LeaveReviewForm(FlaskForm):
    review = StringField("Enter a review for this playlist", validators=[Required(),Length(max=300, message="The review cannot be longer than 300 characters!")])
    stars = IntegerField("Rate the playlist out of 5 stars ",validators=[Required()])
    submit = SubmitField("Submit your review")

    def validate_stars(form, field):
        if len(str(field.data)) > 1 :
            raise ValidationError('Have to be full numbers, no decimals for star rating')

class UpdateButtonForm(FlaskForm):
    submit = SubmitField('Update')


class DeleteButtonForm(FlaskForm):
    submit = SubmitField('Delete')


class UpdateReviewForm(FlaskForm):
    new_review = StringField("What your new review for this playlist?", validators=[Required(),Length(max=300, message="The review cannot be longer than 300 characters!")])
    new_stars = IntegerField("Rate the playlist out of 5 stars ",validators=[Required()])
    submit = SubmitField('Update')

    def validate_new_stars(form, field):
        if len(str(field.data)) > 1 :
            raise ValidationError('Have to be full numbers, no decimals for star rating')


##### Helper functions
def spotify_search(term):
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
def get_playlist_songs_and_artist(user_id, spotify_id):
    songs_and_artists = []
    headers ={"Content-Type": "application/json", "Authorization": "Bearer " + oauth_token}
    search_object = requests.get('https://api.spotify.com/v1/users/'+user_id+'/playlists/'+spotify_id+'/tracks', headers=headers).json()['items']
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


def get_or_create_playlist(title, spotify_id, user_id, pictureURL):
    playlist = Playlist.query.filter_by(title=title).first()
    if playlist:
        return playlist
    else:
        playlist = Playlist(title=title, spotify_id=spotify_id, user_id = user_id, pictureURL=pictureURL)
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
            spotify_id = playlist[1]
            user_id = playlist[2]
            pictureURL = playlist[3]
            new_playlist = get_or_create_playlist(title, spotify_id, user_id, pictureURL)
            search_term.playlists.append(new_playlist)
        db.session.add(search_term)
        db.session.commit()
        return search_term


def get_or_create_review(current_user, playlist, review, stars):
    playlist_review = PlaylistReviews.query.filter_by(review=review, username = current_user.username).first()
    if playlist_review:
        print("Found review")
        return playlist_review
    else:
        print("Adding review")
        playlist_review = PlaylistReviews(review=review, username = current_user.username, stars = stars, playlist = playlist)
        db.session.add(playlist_review)
        db.session.commit()
        return playlist_review



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
# @login_required
def playlist_songs(playlist_name):
    playlist = Playlist.query.filter_by(title=playlist_name).first()
    playlist_tupple = get_playlist_songs_and_artist(playlist.user_id, playlist.spotify_id)
    reviews = PlaylistReviews.query.filter_by(playlist = playlist.title).all()
    number_of_songs = str(len(playlist_tupple))
    return render_template('playlist_songs.html', playlist_tupple=playlist_tupple, playlist_name = playlist.title, reviews = reviews, number_of_songs=number_of_songs)


@app.route('/leave_review/<playlist_name>',methods=["GET","POST"])
@login_required
def leave_review(playlist_name):
    form = LeaveReviewForm()
    if request.method == "POST":
        playlist_review = get_or_create_review(current_user=current_user, playlist=playlist_name, review=form.review.data, stars=form.stars.data)
        return redirect(url_for('all_reviews'))
    return render_template('leave_review.html', form=form, playlist_name = playlist_name)


@app.route('/all_reviews')
@login_required
def all_reviews():
    reviews = PlaylistReviews.query.all()
    return render_template('all_reviews.html',all_reviews=reviews)

@app.route('/searched_terms')
def all_searches():
    all_terms = SearchTerm.query.all()
    return render_template('search_terms.html', all_terms = all_terms)


@app.route('/my_reviews')
@login_required
def my_reviews():
    form1 = UpdateButtonForm()
    form2 = DeleteButtonForm()
    user_reviews = PlaylistReviews.query.filter_by(username=current_user.username).all()
    return render_template('user_reviews.html', user_reviews=user_reviews, form1 = form1, form2=form2)

@app.route('/update/<review>',methods=["GET","POST"])
@login_required
def update(review):
    form = UpdateReviewForm()
    if form.validate_on_submit():
        new_review = form.new_review.data
        new_stars = form.new_stars.data
        playlist = PlaylistReviews.query.filter_by(review=review).first()
        playlist.review = new_review
        playlist.stars = new_stars
        db.session.commit()
        flash("Updated review")
        return redirect(url_for('my_reviews'))
    return render_template('update_review.html', review = review, form=form)

@app.route('/delete/<review>',methods=["GET","POST"])
@login_required
def delete(review):
    playlist_review = PlaylistReviews.query.filter_by(review=review).first()
    playlist_review_title = playlist_review.playlist
    db.session.delete(playlist_review)
    flash("Successfully deleted your review for: {}".format(playlist_review_title))
    return redirect(url_for('my_reviews'))

@app.route('/all_users')
@login_required
def all_users():
    all_users = User.query.all()
    return render_template('all_users.html',all_users=all_users)

@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html')

@app.errorhandler(500)
def page_not_found(e):
    return render_template('500.html')

if __name__ == '__main__':
    db.create_all()
    manager.run()
