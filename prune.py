import requests
from datetime import datetime, timedelta
from dotenv import load_dotenv
import os

load_dotenv()

# Radarr setup
API_KEY_RADARR = os.getenv('RADARR_API_KEY')
RADARR_HOST = 'http://192.168.1.206:7878'
RADARR_API_URL = f"{RADARR_HOST}/api/v3/movie?apiKey={API_KEY_RADARR}"
RADARR_TAG_API_URL = f"{RADARR_HOST}/api/v3/tag?apiKey={API_KEY_RADARR}"
RADARR_DELETE_URL = f"{RADARR_HOST}/api/v3/movie/{{}}?deleteFiles=true&addImportExclusion=true&apiKey={API_KEY_RADARR}"
# Criteria for pruning
FILE_SIZE_THRESHOLD_MB = 15000  # Movies larger than this size in MB will be considered for pruning
AGE_THRESHOLD_DAYS = 220  # Movies older than this many days in the library will be considered
EXCLUDE_TAG = "mdblist"  # Exclude movies with this tag from being considered

def fetch_tag_id(tag_name):
    """Fetch the ID for a given tag name."""
    response = requests.get(RADARR_TAG_API_URL)
    if response.status_code == 200:
        tags = response.json()
        for tag in tags:
            if tag['label'].lower() == tag_name.lower():
                return tag['id']
    return None

# Add a global variable to keep track of the total size of deleted movies
TOTAL_DELETED_SIZE_MB = 0

def delete_movie_from_radarr(movie_id, movie_size_mb):
    """Delete a movie from Radarr by ID and update the total deleted size."""
    global TOTAL_DELETED_SIZE_MB
    url = RADARR_DELETE_URL.format(movie_id)
    response = requests.delete(url)
    if response.status_code == 200:
        TOTAL_DELETED_SIZE_MB += movie_size_mb
    return response.status_code == 200

def fetch_movies_for_pruning(exclude_tag_id):
    """Fetch movies from Radarr and print those eligible for pruning based on file size, age, excluding specific tag."""
    response = requests.get(RADARR_API_URL)
    if response.status_code == 200:
        movies = response.json()
        for movie in movies:
            if 'movieFile' in movie and 'added' in movie:
                if exclude_tag_id is not None and exclude_tag_id in movie.get('tags', []):
                    continue  # Skip movies with the excluded tag
                file_size_mb = movie['movieFile'].get('size', 0) / (1024 * 1024)  # Convert bytes to MB
                added_date = datetime.strptime(movie['added'], '%Y-%m-%dT%H:%M:%SZ')
                if file_size_mb > FILE_SIZE_THRESHOLD_MB and (datetime.utcnow() - added_date).days > AGE_THRESHOLD_DAYS:
                    print(f"Eligible for pruning: {movie['title']} (Size: {file_size_mb:.2f} MB, Added: {added_date.date()})")
                    # Here, you could potentially add logic to flag these for review or manual deletion
                    # delete_movie_from_radarr(movie['id'], file_size_mb)
    else:
        print(f"Failed to fetch movies from Radarr. Status code: {response.status_code}")

if __name__ == "__main__":
    exclude_tag_id = fetch_tag_id(EXCLUDE_TAG)
    fetch_movies_for_pruning(exclude_tag_id)
    print(f"Total space returned after deletion: {TOTAL_DELETED_SIZE_MB:.2f} MB")