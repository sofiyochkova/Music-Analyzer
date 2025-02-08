"""
    Contains all functions requiring Last.fm API calls.
"""

import os
from datetime import date, datetime

import requests
import dotenv
import pandas as pd
from flask import flash

from utils import validation

dotenv.load_dotenv()

REQUEST_TIMEOUT = 600
LASTFM_API_KEY = os.getenv("LASTFM_API_KEY")
ROOT_URL = "http://ws.audioscrobbler.com/2.0/"

def check_if_user_exists(username: str) -> bool:
    "Send a request to the Last.fm API checking if a user exists."

    params = {
        "method": "user.getinfo",
        "user": username,
        "api_key": LASTFM_API_KEY,
        "format": "json"
    }

    response = requests.get(ROOT_URL, params=params, timeout=REQUEST_TIMEOUT)

    return response.ok

def get_registration_date(username: str) -> date | None:
    "Get the registration date of a user by username."

    params = {
        "method": "user.getinfo",
        "user": username,
        "api_key": LASTFM_API_KEY,
        "format": "json"
    }

    response = requests.get(ROOT_URL, params=params, timeout=REQUEST_TIMEOUT)

    if not validation.check_lastfm_response(response):
        return None

    return date.fromtimestamp(int(response.json()["user"]["registered"]["unixtime"]))

def get_top_data_predefined_period(
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

        if not validation.check_lastfm_response(response):
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

def get_recent_tracks_by_custom_dates(
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

        if not validation.check_lastfm_response(response) \
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
