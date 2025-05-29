import requests
from bs4 import BeautifulSoup
from imdb import IMDb
import time
from http.client import IncompleteRead
from requests.adapters import HTTPAdapter
from requests.exceptions import ConnectionError, Timeout, RequestException
from urllib3.util.retry import Retry
import json

ia = IMDb()

base_url = "https://www.bbc.co.uk/iplayer/a-z/"
letters_to_scrape = ['r', 's', 't', 'u', 'v', 'w', 'x', 'y', 'z']  # CHANGE RANGE

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.183 Safari/537.36",
    "Accept-Language": "en-US,en;q=0.9",
}

session = requests.Session()
retries = Retry(total=5, backoff_factor=1, status_forcelist=[500, 502, 503, 504])
session.mount("https://", HTTPAdapter(max_retries=retries))

def get_imdb_details(title, year=None):
    imdb_data = {
        "imdb_title": None,
        "imdb_plot": None,
        "imdb_synopsis": None,
        "imdb_link": None,
        "imdb_genre": None,
    }
    try:
        imdb_results = ia.search_movie(title)
        if not imdb_results:
            print(f"No IMDb results found for title: {title}")
            return imdb_data
        movie = ia.get_movie(imdb_results[0].movieID)
        imdb_data["imdb_title"] = movie.get("title", "N/A")
        imdb_data["imdb_plot"] = movie.get("plot", ["No plot available"])[0]
        imdb_data["imdb_synopsis"] = movie.get("synopsis", ["No synopsis available"])[0]
        imdb_data["imdb_genre"] = movie.get("genres", ["No genre available"])
        imdb_data["imdb_link"] = f"https://www.imdb.com/title/tt{movie.movieID}/"
    except Exception as e:
        print(f"Error fetching IMDb data for {title}: {e}")
    return imdb_data


def get_programme_website_url(iplayer_url):
    try:
        response = session.get(iplayer_url, headers=headers, timeout=10)
        if response.status_code != 200:
            print(f"Failed to retrieve iPlayer page: {iplayer_url}")
            return None
        soup = BeautifulSoup(response.text, 'lxml')
        website_link = soup.find("a", string="Programme website")
        if website_link:
            return "https://www.bbc.co.uk" + website_link["href"]
        else:
            print(f"No 'Programme website' link found for: {iplayer_url}")
            return None
    except RequestException as e:
        print(f"Error fetching iPlayer page: {iplayer_url}: {e}")
        return None

# GENRE + SUBGENRES FROM BBC PROGRAMME PAGE
def get_iplayer_genre(programme_website_url):
    try:
        response = session.get(programme_website_url, headers=headers, timeout=10)
        if response.status_code != 200:
            print(f"Failed to retrieve programme website: {programme_website_url}")
            return ["Genre Not Found"]
        soup = BeautifulSoup(response.text, 'lxml')
        genre_elements = soup.select("ul li a[href^='/programmes/genres/']")
        genres = [el.text.strip() for el in genre_elements]
        return genres if genres else ["Genre Not Found"]
    except RequestException as e:
        print(f"Error fetching programme website: {programme_website_url}: {e}")
        return ["Genre Not Found"]


# SCRAPING FORMAT

def get_iplayer_format(programme_website_url):
    try:
        response = session.get(programme_website_url, headers=headers, timeout=10)
        if response.status_code != 200:
            print(f"Failed to retrieve programme website: {programme_website_url}")
            return ["Format Not Found"]
        soup = BeautifulSoup(response.text, 'lxml')
        format_elements = soup.select("ul li a[href^='/programmes/formats/']")
        format = [el.text.strip() for el in format_elements]
        return format if format else ["Format Not Found"]
    except RequestException as e:
        print(f"Error fetching programme website: {programme_website_url}: {e}")
        return ["Format Not Found"]


# LONGER PROGRAMME DESCRIPTION FROM IPLAYER PROGRAMME PAGE
def get_iplayer_long_description(programme_url):
    try:
        response = session.get(programme_url, headers=headers, timeout=10)
        if response.status_code != 200:
            print(f"Failed to retrieve programme page: {programme_url}")
            return "No Long Description"
        soup = BeautifulSoup(response.text, 'lxml')
        description_element = soup.select_one("div.synopsis.typo p.synopsis__paragraph")
        long_description = description_element.text.strip() if description_element else "No Long Description"
        return long_description
    except RequestException as e:
        print(f"Error fetching programme page: {programme_url}: {e}")
        return "No Long Description"


program_data = []
for letter in letters_to_scrape:
    url = f"{base_url}{letter}"
    print(f"Scraping section: {letter.upper()} - URL: {url}")
    response = session.get(url, headers=headers, timeout=10)
    if response.status_code != 200:
        print(f"Failed to retrieve {url}")
        continue
    soup = BeautifulSoup(response.text, 'lxml')
    programme_elements = soup.select("a.list-content-item")
    for programme in programme_elements:
        title = programme.select_one(".list-content-item__title").text.strip() if programme.select_one(
            ".list-content-item__title") else "No Title"
        iplayer_description = programme.get("aria-label", "No Description")
        link = "https://www.bbc.co.uk" + programme.get("href", "No Link")
        availability = programme.select_one(".list-content-item__sublabel")
        availability_text = availability.text.strip() if availability else "Availability Unknown"
        print(f"Title found: {title}")

        imdb_details = get_imdb_details(title)

        programme_website_url = get_programme_website_url(link)
        if programme_website_url:
            iplayer_genre = get_iplayer_genre(programme_website_url)
            main_genre = iplayer_genre[0] if iplayer_genre else "Genre Not Found"
            subgenres = iplayer_genre[1:] if len(iplayer_genre) > 1 else []
            iplayer_format = get_iplayer_format(programme_website_url)

        else:
            main_genre, subgenres = "Genre Not Found", []
            iplayer_format = "Format Not Found", []

        iplayer_long_description = get_iplayer_long_description(link)

        iplayer_format = get_iplayer_format(programme_website_url)

        program_data.append({
            "title": title,
            "iplayer_description": iplayer_description,
            "availability": availability_text,
            "link": link,
            "iplayer_main_genre": main_genre,
            "iplayer_subgenres": subgenres,
            "iplayer_format": iplayer_format,
            "iplayer_programme_descriptions": iplayer_long_description,
            **imdb_details
        })

        time.sleep(2)

# Save collected programme data to JSON file
output_file = "../2005_iPlayer_format_r_2_z.json"
with open(output_file, "w", encoding="utf-8") as f:
    json.dump(program_data, f, indent=4, ensure_ascii=False)

print(f"Scraped! Saved to {output_file}!")
