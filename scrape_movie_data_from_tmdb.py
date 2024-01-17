from recommender import app
from models import Link
import requests
from bs4 import BeautifulSoup
import pandas as pd
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
                
                except:
                    print("Ignoring duplicate movie with id: " + movie_id)
                    pass
            count += 1
            if count % 100 == 0:
                print(count, " links read")
        #return movie_ids[:n]
        return movie_ids

def write_to_table(movie_data):
    file_exists = os.path.isfile('data/movie_data.csv')
    with open('data/movie_data.csv', 'a' if file_exists else 'w', newline='', encoding='utf8') as csvfile:
        writer = csv.writer(csvfile, delimiter=',')
        if not file_exists:
            writer.writerow(['movie_id', 'tmdb_id', 'poster', 'tagline', 'overview'])
        for movie_id, tmdb_id, img_url, tagline, overview in movie_data:
            writer.writerow([movie_id, tmdb_id, img_url, tagline, overview])


import aiohttp
import asyncio

async def get_movie_data(tmdb_id):
    headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/50.0.2661.102 Safari/537.36'}

    tmdb_url = "https://www.themoviedb.org/movie/" + tmdb_id

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(tmdb_url, headers=headers) as response:
                tmdb_page_text = await response.text()
    except:
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(tmdb_url, headers=headers) as response:
                    tmdb_page_text = await response.text()
        except:
            return "", "", ""


    soup = BeautifulSoup(tmdb_page_text, 'html.parser')
    try:
        img_path = soup.find('div', class_='image_content backdrop').img['data-src']
        if img_path[:5] != "/t/p/":
            img_url = img_path
        else:
            img_url = "https://image.tmdb.org" + img_path 

        #img_url = "https://image.tmdb.org" + img_path
    except:
        img_url = ""
    
    try:
        overview = soup.find('div', class_='header_info').p.text
    except:
        overview = ""
    try:
        tagline = soup.find('div', class_='header_info').h3.text
        if tagline == "Overview":
            tagline = ""
    except:
        tagline = ""
    
    return img_url, tagline, overview

def get_movie_data_via_api(tmdb_id, api_key):
    headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/50.0.2661.102 Safari/537.36'}
    tmdb_url = "https://api.themoviedb.org/3/movie/{0}?api_key={1}".format(tmdb_id, api_key)

    try:
        tmdb_data = requests.get(tmdb_url, headers=headers).json()             
    except:
        try:
            tmdb_data = requests.get(tmdb_url, headers=headers).json() 
        except:
            return "", "", ""
    
    try:
        img_url = "https://image.tmdb.org/t/p/w300_and_h450_bestv2" + tmdb_data["poster_path"]
    except:
        img_url = ""

    try:
        overview = tmdb_data["overview"]
    except:
        overview = ""
    try:
        tagline = tmdb_data["tagline"]
        if tagline == "Overview":
            tagline = ""
    except:
        tagline = ""
    
    return img_url, tagline, overview

def main():
    
    use_api = True
    fill_up = False

    with app.app_context():
        movie_ids = get_movie_ids_and_tmdb_ids(n=10)

        with open('data/movie_data.csv', newline='', encoding='utf8') as csvfile:
            reader = csv.reader(csvfile, delimiter=',')
            last_known_movie_id = list(reader)[-1][0]
        
        if use_api:
            from config import api_key
            import time

        if fill_up:
            df = pd.read_csv('data/movie_data.csv')

        count = 0
        for movie_id, tmdb_id in movie_ids:

            if fill_up:
                if not df['movie_id'].isin([int(movie_id)]).any():
                    if api_key:
                        movie_poster_url, movie_tagline, movie_overview = get_movie_data_via_api(tmdb_id, api_key)
                        time.sleep(0.6) # because you are only allowed 40 requests in 10 seconds (added some padding)
                    else:
                        movie_poster_url, movie_tagline, movie_overview = asyncio.run(get_movie_data(tmdb_id))

                    write_to_table([[movie_id, tmdb_id, movie_poster_url, movie_tagline, movie_overview]])
            else:
                if int(movie_id) > int(last_known_movie_id):
                
                    if api_key:
                        movie_poster_url, movie_tagline, movie_overview = get_movie_data_via_api(tmdb_id, api_key)
                        time.sleep(0.6) # because you are only allowed 40 requests in 10 seconds (added some padding)
                    else:
                        movie_poster_url, movie_tagline, movie_overview = asyncio.run(get_movie_data(tmdb_id))

                    write_to_table([[movie_id, tmdb_id, movie_poster_url, movie_tagline, movie_overview]])

                    count += 1
                    if count % 100 == 0:
                        print(count, " movies scraped")
        

if __name__=='__main__':
    main()

