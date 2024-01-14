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