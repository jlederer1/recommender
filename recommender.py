# Contains parts from: https://flask-user.readthedocs.io/en/latest/quickstart_app.html

from flask import Flask, render_template, request, session
from flask_user import login_required, UserManager, current_user 
from flask_user.forms import EditUserProfileForm

from flask_paginate import Pagination, get_page_args, get_page_parameter

from models import db, User, Movie, MovieGenre, Link, Tag, Rating, Data
from read_data import check_and_read_data
from sqlalchemy import func, or_
import math
import numpy as np

from create_recommendations import recommend_movies

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

    # get 4 random movies and their poster + one tagline
    not_complete = True
    while not_complete:
        movies = Movie.query.order_by(func.random()).limit(4).all()
        movie_ids = [m.id for m in movies]

        data = Data.query.filter(Data.movie_id.in_(movie_ids)).all()
        movie_data = {m.movie_id: {'poster': m.poster, 'tagline': m.tagline, 'overview': m.overview} for m in data}


        bad_batch = False
        for movie_id in movie_data:
            if movie_data[movie_id]["tagline"] == "" or movie_data[movie_id]["poster"] == "":
                bad_batch = True
                break
        if not bad_batch:
            not_complete = False
            
    correct_guess = np.random.choice(movie_ids)

    return render_template("home.html", movies=movies, movie_data=movie_data, correct_guess=correct_guess)

def load_all_ratings(movie_ids=None): 
    if not movie_ids:   
        movie_ids = [m.id for m in Movie.query.all()]
    ### Fetch all ratings for movies calculate averages
    ratings = Rating.query.filter(Rating.movie_id.in_(movie_ids)).all()
    all_ratings_dict = {}
    for rating in ratings:
        all_ratings_dict.setdefault(rating.movie_id, []).append(rating)
    
    counts = {}
    averages_dict = {}
    for m in movie_ids: 
        if m in all_ratings_dict.keys():
            scores = [r.rating for r in all_ratings_dict[m]]
            averages_dict[m] = math.ceil(sum(scores)/len(scores))
            counts[m] = len(scores)
        else:
            averages_dict[m] = 0
            counts[m] = 0
    
    return averages_dict, counts

def load_user_ratings(user_id, movie_ids=None): 
    if not movie_ids:   
        movie_ids = [m.id for m in Movie.query.all()]
    ### Fetch ratings made by the current user for these movies
    user_ratings = Rating.query.filter(
        Rating.user_id == user_id,
        Rating.movie_id.in_(movie_ids)
    ).all()
    user_ratings_dict = {}
    for rating in user_ratings:
        user_ratings_dict.setdefault(rating.movie_id, []).append(rating)
    
    return user_ratings_dict

# The Members page is only accessible to authenticated users via the @login_required decorator
@app.route('/movies')
@login_required  # User must be authenticated
def movies_page():
    # String-based templates

    # first 10 movies
    #movies = Movie.query.limit(10).all()
    #movie_ids = [m.id for m in movies]

    # use flask_paginate to paginate

    page = request.args.get(get_page_parameter(), type=int, default=1)
    per_page = 10

    search_query = request.args.get('q', '')
    order_by_rating = 'order_by_rating' in request.args

    #(WR) = (v ÷ (v+m)) × R + (m ÷ (v+m)) × C , where:
    """
    query = Movie.query
    if search_query:
        query = query.filter(Movie.title.contains(search_query))

    if order_by_rating:
        C = db.session.query(func.avg(Rating.rating)).scalar()
        m = 1
        query = query(Movie, func.count(Rating.id).label('votes')).\
            join(Rating).\
            group_by(Movie.id).\
            having(func.count(Rating.id) >= m).\
            order_by((func.count(Rating.id) / (func.count(Rating.id) + m) * func.avg(Rating.rating) + (m / (func.count(Rating.id) + m) * C)).desc()).all()
    """
    query = Movie.query
    if order_by_rating:
        C = db.session.query(func.avg(Rating.rating)).scalar()
        m = 2
        subquery = db.session.query(Movie.id, (func.count(Rating.id) / (func.count(Rating.id) + m) * func.avg(Rating.rating) + (m / (func.count(Rating.id) + m) * C)).label('weighted_rating')).\
            join(Rating).\
            group_by(Movie.id).\
            having(func.count(Rating.id) >= m).\
            subquery()
        query = db.session.query(Movie).join(subquery, Movie.id == subquery.c.id).order_by(subquery.c.weighted_rating.desc())
    
    if search_query:
            #query = query.filter(Movie.title.contains(search_query))
            query = query.join(Data, Movie.id == Data.movie_id).filter(or_(Movie.title.contains(search_query), Data.overview.contains(search_query)))


    movies = query.paginate(page=page, per_page=per_page, error_out=False)
    pagination = Pagination(page=page, total=movies.total, record_name='movies', per_page=per_page)

    # only Romance movies
    # movies = Movie.query.filter(Movie.genres.any(MovieGenre.genre == 'Romance')).limit(10).all()

    # only Romance AND Horror movies
    # movies = Movie.query\
    #     .filter(Movie.genres.any(MovieGenre.genre == 'Romance')) \
    #     .filter(Movie.genres.any(MovieGenre.genre == 'Horror')) \
    #     .limit(10).all()
    movie_ids = [m.id for m in movies]
    links = Link.query.filter(Link.movie_id.in_(movie_ids)).all()
    links = {link.movie_id: link for link in links}
    tag_list = Tag.query.filter(Tag.movie_id.in_(movie_ids)).all()
    tags = {}
    for tag in tag_list:
        tags.setdefault(tag.movie_id, []).append(tag)
    
    data = Data.query.filter(Data.movie_id.in_(movie_ids)).all()
    movie_data = {m.movie_id: {'poster': m.poster, 'tagline': m.tagline, 'overview': m.overview} for m in data}


    if current_user.is_authenticated:
        print("Loading user-specific ratings for movies")
        user_id = current_user.id
        user_ratings_dict = load_user_ratings(user_id, movie_ids)
        averages_dict, counts = load_all_ratings(movie_ids)
    else:
        print("Loading all ratings for movies")
        user_ratings_dict = {}
        averages_dict, counts = load_all_ratings(movie_ids)

    return render_template("movies.html", movies=movies, movie_links=links, movie_tags=tags, user_rating=user_ratings_dict, average_rating=averages_dict, votes=counts, movie_data=movie_data, pagination=pagination)

@app.route('/submit_ratings', methods=['POST'])
def submit_ratings():
    ratings = request.json['ratings']
    # Add logic to insert ratings into the database
    for r in ratings: 
        user_id = r['user_id']
        movie_id = r['movie_id']
        score = r['score']
        rating = Rating(user_id=user_id, movie_id=movie_id, rating=score)

        #query_db = db.session.execute(text(f"SELECT user_id, movie_id, rating FROM movie_ratings WHERE user_id = {user_id} AND movie_id = {movie_id}"))
        #if False :#len(query_db.all()) == 1:
        #    print("already exists, so will be deleted and created again")
        #    db.session.delete(query_db)

        row = Rating.query.filter(Rating.user_id==user_id, Rating.movie_id==movie_id).all()
        if len(row) > 0:
            print(row[0])
            print("already exists, so will be deleted and created again")
            db.session.delete(row[0])
        db.session.add(rating)

    db.session.commit()
    print("received ratings")
    return 'Success', 200

@app.route('/custom-user-profile')
def custom_user_profile():
    user_id = current_user.id
    user_ratings_dict = load_user_ratings(user_id)
    averages_dict, counts = load_all_ratings()
    
    # movie_ids in user_ratings_dict
    movie_ids = list(user_ratings_dict.keys())
    # movies for which the current user gave a rating
    movies = Movie.query.filter(Movie.id.in_(movie_ids)).all()
    
    form = EditUserProfileForm()
    
    return render_template('custom_user_profile.html', movies=movies, user_rating=user_ratings_dict, average_rating=averages_dict, form=form, counts=counts)

@app.route('/recommendations')
@login_required  # User must be authenticated
def recommendations_page():
    user_id = current_user.id

    already_rated, predictions = recommend_movies(app, user_id)
    predictions = predictions["movie_id"]
    predictions = Movie.query.filter(Movie.id.in_(predictions))#.all()

    page = request.args.get(get_page_parameter(), type=int, default=1)
    per_page = 10


    movies = predictions.paginate(page=page, per_page=per_page, error_out=False)
    pagination = Pagination(page=page, total=movies.total, record_name='movies', per_page=per_page)


    movie_ids = [m.id for m in movies]
    links = Link.query.filter(Link.movie_id.in_(movie_ids)).all()
    links = {link.movie_id: link for link in links}
    tag_list = Tag.query.filter(Tag.movie_id.in_(movie_ids)).all()
    tags = {}
    for tag in tag_list:
        tags.setdefault(tag.movie_id, []).append(tag)
    
    data = Data.query.filter(Data.movie_id.in_(movie_ids)).all()
    movie_data = {m.movie_id: {'poster': m.poster, 'tagline': m.tagline, 'overview': m.overview} for m in data}


    if current_user.is_authenticated:
        print("Loading user-specific ratings for movies")
        user_id = current_user.id
        user_ratings_dict = load_user_ratings(user_id, movie_ids)
        averages_dict, counts = load_all_ratings(movie_ids)
    else:
        print("Loading all ratings for movies")
        user_ratings_dict = {}
        averages_dict, counts = load_all_ratings(movie_ids)

    return render_template("recommendations.html", movies=movies, movie_links=links, movie_tags=tags, user_rating=user_ratings_dict, average_rating=averages_dict, votes=counts, movie_data=movie_data, pagination=pagination)


# Start development web server
if __name__ == '__main__':
    app.run(port=5000, debug=True)
