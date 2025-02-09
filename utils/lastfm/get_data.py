"""
    Contains functions related to getting
    data from Last.fm which is then going
    to be visualized and processed.
"""

import os
from datetime import datetime

import requests
import dotenv
import pandas as pd

from utils import validation
from utils.lastfm import lastfm_validation

dotenv.load_dotenv()

REQUEST_TIMEOUT = 600
LASTFM_API_KEY = os.getenv("LASTFM_API_KEY")
ROOT_URL = "http://ws.audioscrobbler.com/2.0/"

def top_data_predefined_period(
        username: str,
        data_type: str,
        time_period: str
    ) -> pd.DataFrame:
    """Returns a dataframe of the scrobbles
       based on a predefined time period.
    
    Keyword arguments:
    - username -- description
    - data_type -- tracks | albums | artists
    - time_period -- 7day | 1month | 3month | 6month | 12month | overall
    """

    if not (
        validation.username_exists_in_lastfm(username)
        and validation.check_data_type(data_type)
        and validation.valid_time_period(time_period)
    ):
        return pd.DataFrame()

    page = 1
    list_tracks = []

    while True:
        params = {
            "method": "user.gettop" + data_type,
            "user": username,
            "api_key": LASTFM_API_KEY,
            "format": "json",
            "period": time_period,
            "limit": 200,
            "page": page
        }

        response = requests.get(ROOT_URL, params=params, timeout=REQUEST_TIMEOUT)

        if not lastfm_validation.check_lastfm_response(response):
            return pd.DataFrame()

        response_dict = response.json()

        list_tracks += [
            {
                "name": entry["name"],
                "artist": None if data_type == "artists" else entry["artist"]["name"],
                "scrobble count": int(entry["playcount"])
            }

            for entry in response_dict["top" + data_type][data_type[:-1]]
        ]

        total_pages = response_dict["top" + data_type]["@attr"]["totalPages"]

        if page >= int(total_pages):
            break

        page += 1

    df_tracks = pd.DataFrame(list_tracks)
    df_tracks.dropna(axis=1, inplace=True)
    df_tracks.index += 1

    return df_tracks

def recent_tracks_by_custom_dates(
    username: str,
    start_date: str,
    end_date: str
    ) -> pd.DataFrame:
    """Returns a dataframe of the tracks 
    scrobbled between start_date and end_date.
    
    Keyword arguments:
    - username -- Last.fm username
    - start_date -- start date
    - end_date -- end_date
    """

    start_datetime = datetime.fromisoformat(start_date + "T00:00:00")
    start_timestamp = int(start_datetime.timestamp())

    end_datetime = datetime.fromisoformat(end_date + "T23:59:59")
    end_datetime.replace(hour=23, minute=59, second=59)
    end_timestamp = int(end_datetime.timestamp())

    page = 1
    list_response = []

    while True:
        params = {
            "method": "user.getrecenttracks",
            "user": username,
            "api_key": LASTFM_API_KEY,
            "format": "json",
            "from": start_timestamp,
            "to": end_timestamp,
            "limit": 200,
            "page": page
        }

        response = requests.get(ROOT_URL, params=params, timeout=REQUEST_TIMEOUT)
        response_dict = response.json()

        if not lastfm_validation.check_lastfm_response(response) \
            or response_dict.get("recenttracks").get("@attr").get("total") == "0":
            return pd.DataFrame()

        list_response += [
            {
                "track": track["name"], 
                "artist": track["artist"]["#text"],
                "album": track["album"]["#text"],
                "scrobble_time": datetime.fromtimestamp(int(track["date"]["uts"]))
            }
            for track in response_dict["recenttracks"]["track"]
            if "@attr" not in track.keys()
        ]

        total_pages = response_dict["recenttracks"]["@attr"]["totalPages"]

        if page >= int(total_pages):
            break

        page += 1

    return pd.DataFrame(list_response)

def similar_artists(artist_name: str) -> set[tuple[str, str]]:
    "Return a set of similar artists based on a given artist name."

    params = {
        "method": "artist.getSimilar",
        "artist": artist_name,
        "api_key": LASTFM_API_KEY,
        "format": "json"
    }

    response = requests.get(ROOT_URL, params=params, timeout=REQUEST_TIMEOUT)

    if not lastfm_validation.check_lastfm_response(response):
        return set()

    response_json = response.json()

    similar_artists_set = (
        (artist.get("name"), artist.get("url"))
        for artist in response_json.get("similarartists").get("artist")
        if float(artist.get("match")) > 0.7
    )

    return set(similar_artists_set)

def all_similar_artists(artists: pd.Series, top_artist_limit: int=10) -> pd.DataFrame:
    """Returns the top similar artists based on Last.fm data
        given the top top_artist_limit most listened to artist during
        a particular time period.
    """
    similar_artists_set = set()

    for artist in artists.head(top_artist_limit):
        similar = similar_artists(artist)
        similar_artists_set.update(similar)

    similar_artists_distinct = [
        (name, url)
        for name, url in similar_artists_set
        if name.lower() not in list(map(lambda artist: artist.lower(), artists))
    ]

    return pd.DataFrame(similar_artists_distinct, columns=["name", "url"])

def duration(name: str, artist: str) -> int:
    "Gets duration by track name and artist from Last.fm in milliseconds"

    params = {
        "method": "track.getInfo",
        "track": name,
        "artist": artist,
        "api_key": LASTFM_API_KEY,
        "format": "json"
    }

    response = requests.get(ROOT_URL, params=params, timeout=REQUEST_TIMEOUT)

    if not lastfm_validation.check_lastfm_response(response):
        return 0

    response_json = response.json()

    return int(response_json["track"]["duration"])
