# Contains parts from: https://flask-user.readthedocs.io/en/latest/quickstart_app.html

from flask import Flask, render_template, request
from flask_user import login_required, UserManager

from models import db, User, Movie, MovieGenre, Link, Tag, Rating
from read_data import check_and_read_data

# Class-based application configuration
class ConfigClass(object):
    """ Flask application config """

    # Flask settings
    SECRET_KEY = 'This is an INSECURE secret!! DO NOT use this in production!!'

    # Flask-SQLAlchemy settings
    SQLALCHEMY_DATABASE_URI = 'sqlite:///movie_recommender.sqlite'  # File-based SQL database
    SQLALCHEMY_TRACK_MODIFICATIONS = False  # Avoids SQLAlchemy warning

    # Flask-User settings
    USER_APP_NAME = "Movie Recommender"  # Shown in and email templates and page footers
    USER_ENABLE_EMAIL = False  # Disable email authentication
    USER_ENABLE_USERNAME = True  # Enable username authentication
    # USER_ENABLE_AUTH0 = True ### debug...
    USER_REQUIRE_RETYPE_PASSWORD = True  # Simplify register form

# Create Flask app
app = Flask(__name__)
app.config.from_object(__name__ + '.ConfigClass')  # configuration
app.app_context().push()  # create an app context before initializing db
db.init_app(app)  # initialize database
db.create_all()  # create database if necessary
user_manager = UserManager(app, db, User)  # initialize Flask-User management


@app.cli.command('initdb')
def initdb_command():
    global db
    """Creates the database tables."""
    with app.app_context():
        check_and_read_data(db)
    print('Initialized the database.')

# The Home page is accessible to anyone
@app.route('/')
def home_page():
    # render home.html template
    return render_template("home.html")


# The Members page is only accessible to authenticated users via the @login_required decorator
@app.route('/movies')
@login_required  # User must be authenticated
def movies_page():
    # String-based templates

    # first 10 movies
    movies = Movie.query.limit(10).all()
    movie_ids = [m.id for m in movies]

    # only Romance movies
    # movies = Movie.query.filter(Movie.genres.any(MovieGenre.genre == 'Romance')).limit(10).all()

    # only Romance AND Horror movies
    # movies = Movie.query\
    #     .filter(Movie.genres.any(MovieGenre.genre == 'Romance')) \
    #     .filter(Movie.genres.any(MovieGenre.genre == 'Horror')) \
    #     .limit(10).all()

    links = Link.query.filter(Link.movie_id.in_(movie_ids)).all()
    links = {link.movie_id: link for link in links}
    tag_list = Tag.query.filter(Tag.movie_id.in_(movie_ids)).all()
    tags = {}
    for tag in tag_list:
        tags.setdefault(tag.movie_id, []).append(tag)
    
    ratings = Rating.query.filter(Rating.movie_id.in_(movie_ids)).all()
    ratings_by_movie = {}
    for rating in ratings:
        ratings_by_movie.setdefault(rating.movie_id, []).append(rating)

    return render_template("movies.html", movies=movies, movie_links=links, movie_tags=tags, ratings=ratings_by_movie)

@app.route('/submit_ratings', methods=['POST'])
def submit_ratings():
    ratings = request.json['ratings']
    # Add logic to insert ratings into the database
    for r in ratings: 
        user_id = r['user_id']
        movie_id = r['movie_id']
        score = r['score']
        rating = Rating(user_id=user_id, movie_id=movie_id, rating=score)
        db.session.add(rating)
    db.session.commit() 
    print("received ratings")
    return 'Success', 200

# Start development web server
if __name__ == '__main__':
    app.run(port=5000, debug=True)
