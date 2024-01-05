import csv
from sqlalchemy.exc import IntegrityError
from models import Movie, MovieGenre, Link, Tag, Rating, User
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password):
    return pwd_context.hash(password)

def check_and_read_data(db):
    # check if we have movies in the database
    # read data if database is empty
    if Movie.query.count() == 0:
        # read movies from csv
        with open('data/movies.csv', newline='', encoding='utf8') as csvfile:
            reader = csv.reader(csvfile, delimiter=',')
            count = 0
            for row in reader:
                if count > 0:
                    try:
                        id = row[0]
                        title = row[1]
                        movie = Movie(id=id, title=title)
                        db.session.add(movie)
                        genres = row[2].split('|')  # genres is a list of genres
                        for genre in genres:  # add each genre to the movie_genre table
                            movie_genre = MovieGenre(movie_id=id, genre=genre)
                            db.session.add(movie_genre)
                        db.session.commit()  # save data to database
                    except IntegrityError:
                        print("Ignoring duplicate movie: " + title)
                        db.session.rollback()
                        pass
                count += 1
                if count % 100 == 0:
                    print(count, " movies read")
        
        # read links from csv
        with open('data/links.csv', newline='', encoding='utf8') as csvfile:
            reader = csv.reader(csvfile, delimiter=',')
            count = 0
            for row in reader:
                if count > 0:
                    try:
                        movie_id = row[0]
                        imdb_id = row[1]
                        tmdb_id = row[2]
                        link = Link(id=movie_id, movie_id=movie_id, imdb_id=imdb_id, tmdb_id=tmdb_id)
                        db.session.add(link)
                        db.session.commit()  # save data to database
                    except IntegrityError:
                        print("Ignoring duplicate movie with id: " + movie_id)
                        db.session.rollback()
                        pass
                count += 1
                if count % 100 == 0:
                    print(count, " links read")
                
                if count > 1000:
                    db.session.rollback()
                    break
        
        # read tags from csv
        with open('data/tags.csv', newline='', encoding='utf8') as csvfile:
            reader = csv.reader(csvfile, delimiter=',')
            count = 0
            tags = {}
            for row in reader:
                if count > 0:
                    try:
                        user_id = row[0]
                        movie_id = row[1]
                        tag_content = row[2]
                        if (user_id, movie_id) not in tags.keys(): tags[(user_id, movie_id)] = []
                        if tag_content not in tags[(user_id, movie_id)]:
                            tags[(user_id, movie_id)].append(tag_content)
                            tag = Tag(id=count, user_id=user_id, movie_id=movie_id, tag_content=tag_content)
                            db.session.add(tag)
                            db.session.commit()  # save data to database
                    except IntegrityError:
                        print("Ignoring duplicate tag: " + tag_content + " (user: " + user_id + ", movie: " + movie_id + ")")
                        db.session.rollback()
                        pass
                count += 1
                if count % 100 == 0:
                    print(count, " tags read")
                
                if count > 1000:
                    db.session.rollback()
                    break
                    
                    
        # read ratings (and corresponding users) from csv
        with open('data/ratings.csv', newline='', encoding='utf8') as csvfile:
            reader = csv.reader(csvfile, delimiter=',')
            count = 0
            rating_counter = 0
            rating_ids = {}
            users = []
            for row in reader:
                if count > 0:
                    try:
                        user_id = row[0]
                        movie_id = row[1]
                        score = row[2]
                        if (user_id, movie_id) not in rating_ids.keys():
                            rating_ids[(user_id, movie_id)] = rating_counter
                            rating = Rating(id=rating_counter, user_id=user_id, movie_id=movie_id, rating=score)
                            rating_counter += 1
                            db.session.add(rating)
                            db.session.commit() 
                        if user_id not in users: 
                            name = "user_" + user_id
                            password = "user_key_" + user_id
                            # Hash the password
                            hashed_password = hash_password(password)
                            first = "Olaf_" + user_id
                            last = "Gordon"
                            user = User(id=user_id, active=1, username=name, password=hashed_password, first_name=first, last_name=last)
                            db.session.add(user)
                            db.session.commit() 
                            print(" user " + name +" added")
                            users.append(user_id)
                    except IntegrityError:
                        print("Ignoring duplicate (?)")
                        db.session.rollback()
                        pass
                count += 1
                if count % 100 == 0:
                    print(count, " ratings read")
                
                if count > 1000:
                    db.session.rollback()
                    break
            

