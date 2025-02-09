"""
    Contains all functions requiring Spotify API calls.
"""

import re

import spotipy # type: ignore
from spotipy.oauth2 import SpotifyClientCredentials # type: ignore
import dotenv
import pandas as pd

from utils import validation

dotenv.load_dotenv()

auth_manager = SpotifyClientCredentials()
spotify = spotipy.Spotify(auth_manager=auth_manager)

WAIT_TIME = 0.5
SEMAPHORE_NUMBER = 3

def get_artist_uri(artist_name: str) -> str | None:
    "Search an artist by name - returns their unique uri code"

    # spotify search doesn't like special symbols
    artist_name_clean = re.sub(r"[^\w\s]", "", artist_name)
    print("Getting " + artist_name_clean)
    search_results = spotify.search(q=f"artist:{artist_name_clean}", type="artist", limit=50)

    if search_results["artists"]["items"] == []:
        return None

    search_results_filtered = [
        result["uri"]
        for result in search_results["artists"]["items"]
        if result["name"].lower() == artist_name.lower()
    ]

    print(search_results_filtered)
    return None if search_results_filtered == [] else search_results_filtered[0]

def get_track_or_album_uri(data_type: str, name: str, artist: str) -> str | None:
    "Search an artist by name - returns their unique uri code"

    if not validation.check_spotify_data_type(data_type):
        return None

    search_results = spotify.search(q=f"{data_type}:{name} artist:{artist}", type=data_type)

    if search_results[data_type + "s"]["items"] == []:
        return None

    uri_popularity_tuples: list[tuple[str, str]] = sorted([
        (result["uri"], result["popularity"])
        for result in search_results[data_type + "s"]["items"]
        if result["name"].lower() == name.lower()
    ], key=lambda item: item[1], reverse=True)

    uri_list = [
        uri
        for uri, _ in uri_popularity_tuples
    ]

    return None if not uri_list else uri_list[0]

# unfortunately, it doesn't return genres for most artists right now...
def get_artists_data(uri_list: list[str | None]) -> pd.DataFrame:
    "Get artists data based on a given list of uri codes"

    uri_list = [
        uri
        for uri in uri_list
        if uri is not None
    ]

    artists_data = spotify.artists(uri_list)

    artists_data_clean = [
        {
            "name": artist["name"],
            "genres": artist["genres"],
            "popularity": int(artist["popularity"]), 
            "uri": artist["uri"]
        }
        for artist in artists_data["artists"]
    ]

    return pd.DataFrame(artists_data_clean)

def get_tracks_data(uri_list: list[str | None]) -> pd.DataFrame:
    "Get tracks data based on a given list of uris"

    uri_list = [
        uri
        for uri in uri_list
        if uri is not None
    ]

    result_data = spotify.tracks(uri_list)
            
    search_results_clean = [
                {
                    "name": result["name"],
                    "artist": result["artists"][0]["name"],
                    "album": result["album"]["name"],
                    "release_date": result["album"]["release_date"],
                    "duration": int(result["duration_ms"]) // 1000,
                    "popularity": int(result["popularity"]), 
                    "uri": result["uri"]
                }
                for result in result_data["tracks"]
            ]

    return pd.DataFrame(search_results_clean)

def get_albums_data(uri_list: list[str | None]) -> pd.DataFrame:
    "Get tracks data based on a given list of uris."

    uri_list = [
        uri
        for uri in uri_list
        if uri is not None
    ]

    result_data = spotify.albums(uri_list)

    search_results_clean = [
                {
                    "name": result["name"],
                    "artist": result["artists"][0]["name"],
                    "release_date": result["release_date"],
                    "popularity": int(result["popularity"]), 
                    "uri": result["uri"]
                }
                for result in result_data["albums"]
            ]

    return pd.DataFrame(search_results_clean)
