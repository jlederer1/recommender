from recommender import app
from models import Link
import requests
from bs4 import BeautifulSoup
import csv
import os


def get_movie_ids_and_tmdb_ids(n=10):
    
    with open('data/links.csv', newline='', encoding='utf8') as csvfile:
        reader = csv.reader(csvfile, delimiter=',')
        count = 0
        movie_ids = []
        for row in reader:
            if count > 0:
                try:
                    movie_id = row[0]
                    tmdb_id = row[2]
                    movie_ids.append([movie_id, tmdb_id])
                
                except IntegrityError:
                    print("Ignoring duplicate movie with id: " + movie_id)
                    pass
            count += 1
            if count % 100 == 0:
                print(count, " links read")
        return movie_ids[:n]

def write_to_table(movie_data):
    file_exists = os.path.isfile('data/movie_data.csv')
    with open('data/movie_data.csv', 'a' if file_exists else 'w', newline='', encoding='utf8') as csvfile:
        writer = csv.writer(csvfile, delimiter=',')
        if not file_exists:
            writer.writerow(['movie_id', 'tmdb_id', 'poster', 'tagline', 'overview'])
        for movie_id, tmdb_id, img_url, tagline, overview in movie_data:
            writer.writerow([movie_id, tmdb_id, img_url, tagline, overview])

def get_movie_data(tmdb_id):
    headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/50.0.2661.102 Safari/537.36'}

    tmdb_url = "https://www.themoviedb.org/movie/" + tmdb_id
    tmdb_page = requests.get(tmdb_url, headers=headers)
    tmdb_page.raise_for_status()
    tmdb_page_text = tmdb_page.text
    soup = BeautifulSoup(tmdb_page_text, 'html.parser')
    img_path = soup.find('div', class_='image_content backdrop').img['data-src']
    
    img_url = "https://www.themoviedb.org" + img_path
    overview = soup.find('div', class_='header_info').p.text
    tagline = soup.find('div', class_='header_info').h3.text
    
    return img_url, tagline, overview



def main():
    
    with app.app_context():
        movie_ids = get_movie_ids_and_tmdb_ids(n=10)

        for movie_id, tmdb_id in movie_ids:
            movie_poster_url, movie_tagline, movie_overview = get_movie_data(tmdb_id)

            write_to_table([[movie_id, tmdb_id, movie_poster_url, movie_tagline, movie_overview]])
        

if __name__=='__main__':
    main()

