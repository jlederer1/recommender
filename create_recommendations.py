import pandas as pd 
import numpy as np
from models import Movie, Rating
from scipy.sparse.linalg import svds


def recommend_movies(app, userID, num_recommendations=10):
    with app.app_context():
        ratings = Rating.query.all()
        movies = Movie.query.all()
        rating_data = {r.id: {'user_id': r.user_id, 'movie_id': r.movie_id, 'rating': r.rating} for r in ratings}
        df = pd.DataFrame(rating_data).T

        movie_data = {m.id: {'movie_id': m.id, 'title': m.title} for m in movies}
        movie_df = pd.DataFrame(movie_data).T

        R_df = df.pivot(index = 'user_id', columns ='movie_id', values = 'rating').fillna(0)
       
       # Normalize the data
        R = R_df.values
        user_ratings_mean = np.mean(R, axis = 1)
        R_demeaned = R - user_ratings_mean.reshape(-1, 1)

        # Factorize the matrix
        U, sigma, Vt = svds(R_demeaned, k = 5)

        # Convert sigma to a diagonal matrix
        sigma = np.diag(sigma)

        # Get the predicted ratings
        all_user_predicted_ratings = np.dot(np.dot(U, sigma), Vt) + user_ratings_mean.reshape(-1, 1)

        # Convert the predicted ratings to a DataFrame
        preds_df = pd.DataFrame(all_user_predicted_ratings, columns = R_df.columns)

        #already_rated, predictions = recommend_movies(preds_df, 1, movie_df, df, 10)

        # Get the user's predictions
        user_row_number = userID #- 1
        sorted_user_predictions = preds_df.iloc[user_row_number].sort_values(ascending=False)
        
        # Get the user's data and merge in the movie information.
        user_data = df[df.user_id == (userID)]
        user_full = (user_data.merge(movie_df, how = 'left', left_on = 'movie_id', right_on = 'movie_id').
                        sort_values(['rating'], ascending=False)
                    )

        # Recommend the highest predicted rating movies that the user hasn't seen yet.
        recommendations = (movie_df[~movie_df['movie_id'].isin(user_full['movie_id'])].
            merge(pd.DataFrame(sorted_user_predictions).reset_index(), how = 'left',
                left_on = 'movie_id',
                right_on = 'movie_id').
            rename(columns = {user_row_number: 'Predictions'}).
            sort_values('Predictions', ascending = False).
                        iloc[:num_recommendations, :-1]
                        )

        return user_full, recommendations
    


'''
from flask import Flask, render_template, request, session
from flask_user import login_required, UserManager, current_user 
from flask_user.forms import EditUserProfileForm

from flask_paginate import Pagination, get_page_args, get_page_parameter

from models import db, User, Movie, MovieGenre, Link, Tag, Rating, Data
from read_data import check_and_read_data
from sqlalchemy import func, or_
import math
import numpy as np

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
'''


def check_4_new_ratings():
    newest_rating = Rating.query.order_by(Rating.id.desc()).first()
    with open('persistent_data') as f:
        data = f.readline()
        
    if int(data) == int(newest_rating.id):
        print('no new ratings, use old matrix factorization')
        return False
    else:
        print('new ratings, retrain matrix factorization')
        # train matrix factorization
        # save new data to persistent_data
        with open('persistent_data', 'w') as f:
            f.write(str(newest_rating.id))
        return True


def matrix_factorization():
    # get data from database
    ratings = Rating.query.all()
    movies = Movie.query.all()
    rating_data = {r.id: {'user_id': r.user_id, 'movie_id': r.movie_id, 'rating': r.rating} for r in ratings}
    df = pd.DataFrame(rating_data).T

    movie_data = {m.id: {'movie_id': m.id, 'title': m.title} for m in movies}
    movie_df = pd.DataFrame(movie_data).T

    R_df = df.pivot(index = 'user_id', columns ='movie_id', values = 'rating').fillna(0)
   
   # Normalize the data
    R = R_df.values
    user_ratings_mean = np.mean(R, axis = 1)
    R_demeaned = R - user_ratings_mean.reshape(-1, 1)
    

    # Factorize the matrix using MSE and gradient descent
    num_users, num_movies = R_df.shape
    K = 5
    P = np.random.rand(num_users, K)
    Q = np.random.rand(num_movies, K)
    steps = 200
    alpha = 0.0001
    beta = 0.02
    R_binary = R > 0
    prev_e = np.inf
    for step in range(steps):
        eij = R - np.dot(P, Q.T)
        eij = eij * R_binary  # apply the mask
        P = P + alpha * (2 * np.dot(eij, Q) - beta * P)
        Q = Q + alpha * (2 * np.dot(eij.T, P) - beta * Q)
        e = np.sum(np.square(eij)) + (beta/2) * (np.sum(np.square(P)) + np.sum(np.square(Q)))
        if e > prev_e:  # if the error starts to increase
            break
        prev_e = e
        if e < 0.001:
            break
    
    # save the factorized matrix as csv file
    np.savetxt("P.csv", P, delimiter=",")
    np.savetxt("Q.csv", Q, delimiter=",")


def get_user_recommendations(user_id):
    # read data from csv file
    P = np.loadtxt("P.csv", delimiter=",")
    Q = np.loadtxt("Q.csv", delimiter=",")
    # get the predicted ratings
    all_user_predicted_ratings = np.dot(P, Q.T)
    # Convert the predicted ratings to a DataFrame
    preds_df = pd.DataFrame(all_user_predicted_ratings)
    # Get the user's predictions
    user_row_number = user_id - 1
    sorted_user_predictions = preds_df.iloc[user_row_number].sort_values(ascending=False)

    print(sorted_user_predictions.iloc[:10])
    predictions = list(sorted_user_predictions.iloc[:10].index)
    print(predictions)
    #print(sorted_user_predictions.iloc[:10])

    movies = Movie.query.all()
    movie_preds = [movies[p].id for p in predictions]
    print(movie_preds)


    return movie_preds

#check_4_new_ratings()
#matrix_factorization()
#get_user_recommendations()
