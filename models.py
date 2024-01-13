from flask_sqlalchemy import SQLAlchemy
from flask_user import UserMixin
from sqlalchemy.sql import func

db = SQLAlchemy()

# Define the User data-model.
# NB: Make sure to add flask_user UserMixin as this adds additional fields and properties required by Flask-User
class User(db.Model, UserMixin):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    active = db.Column('is_active', db.Boolean(), nullable=False, server_default='1')

    # User authentication information. The collation='NOCASE' is required
    # to search case insensitively when USER_IFIND_MODE is 'nocase_collation'.
    username = db.Column(db.String(100, collation='NOCASE'), nullable=False, unique=True)
    password = db.Column(db.String(255), nullable=False, server_default='')
    email_confirmed_at = db.Column(db.DateTime(), server_default=func.now())

    # User information
    first_name = db.Column(db.String(100, collation='NOCASE'), nullable=False, server_default='')
    last_name = db.Column(db.String(100, collation='NOCASE'), nullable=False, server_default='')


class Movie(db.Model):
    __tablename__ = 'movies'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100, collation='NOCASE'), nullable=False, unique=True)
    genres = db.relationship('MovieGenre', backref='movie', lazy=True)


class MovieGenre(db.Model):
    __tablename__ = 'movie_genres'
    id = db.Column(db.Integer, primary_key=True)
    movie_id = db.Column(db.Integer, db.ForeignKey('movies.id'), nullable=False)
    genre = db.Column(db.String(255), nullable=False, server_default='')
    
class Link(db.Model): 
    __tablename__ = 'movie_links'
    id = db.Column(db.Integer, primary_key=True)
    movie_id = db.Column(db.Integer, db.ForeignKey('movies.id'))
    imdb_id = db.Column(db.String(50))
    tmdb_id = db.Column(db.String(50))
    
    movie = db.relationship('Movie', backref='link')

class Tag(db.Model):
    __tablename__ = 'movie_tags'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    movie_id = db.Column(db.Integer, db.ForeignKey('movies.id'), nullable=False)
    tag_content = db.Column(db.String(100, collation='NOCASE'), nullable=False, unique=False)
    
    user = db.relationship('User', backref='user_tag')
    movie = db.relationship('Movie', backref='movie_tag')

class Rating(db.Model):
    __tablename__ = 'movie_ratings'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    movie_id = db.Column(db.Integer, db.ForeignKey('movies.id'), nullable=False)
    rating = db.Column(db.Integer, nullable=False) ### db.Float 
    
    user = db.relationship('User', backref='user_rating')
    movie = db.relationship('Movie', backref='movie_rating')
    
class Data(db.Model):
    __tablename__ = 'movie_data_scrape'
    id = db.Column(db.Integer, primary_key=True)
    movie_id = db.Column(db.Integer, db.ForeignKey('movies.id'), nullable=False)
    tmdb_id = db.Column(db.String(50))
    poster = db.Column(db.String(255), nullable=False, server_default='')
    tagline = db.Column(db.String(255), nullable=False, server_default='')
    overview = db.Column(db.String(255), nullable=False, server_default='')
    
    movie = db.relationship('Movie', backref='movie_data_scrape')