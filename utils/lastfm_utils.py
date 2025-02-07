import os
from datetime import date, datetime

import requests
import dotenv
import pandas as pd

dotenv.load_dotenv()

LASTFM_API_KEY = os.getenv("LASTFM_API_KEY")
ROOT_URL = "http://ws.audioscrobbler.com/2.0/"

def check_if_user_exists(username: str) -> bool:
    params = {
        "method": "user.getinfo",
        "user": username,
        "api_key": LASTFM_API_KEY,
        "format": "json"
    }

    response = requests.get(ROOT_URL, params=params)

    try:
        if "error" in response.json().keys():
            return False
    except requests.exceptions.JSONDecodeError:
        print("API is down right now...")
        return False

    return True

def get_registration_date(username: str):
    params = {
        "method": "user.getinfo",
        "user": username,
        "api_key": LASTFM_API_KEY,
        "format": "json"
    }

    response = requests.get(ROOT_URL, params=params)

    if "error" in response.json().keys():
        return None

    return date.fromtimestamp(int(response.json()["user"]["registered"]["unixtime"]))

def get_top_data_predefined_period(username: str, data_type: str, time_period: str) -> pd.DataFrame | str:
    if not check_if_user_exists(username):
        return f"User {username} does not exist"

    if data_type not in ["albums", "tracks", "artists"]:
        return f"Invalid data type {data_type}!"

    if time_period not in ["7day", "1month", "3month", "6month", "12month", "overall"]:
        return f"Invalid time period {time_period}!"

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

        response = requests.get(ROOT_URL, params=params)
        response_dict = response.json()

        if "error" in response_dict.keys():
            return "Encountered error: " + response_dict["message"]

        list_tracks += [
            {
                "name": entry["name"],
                "artist": None if data_type == "artists" else entry["artist"]["name"],
                "playcount": int(entry["playcount"])
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

def get_recent_tracks_by_custom_dates(username: str, start_date: str, end_date: str) -> pd.DataFrame:
    start_stripped = datetime.fromisoformat(start_date + "T00:00:00")
    start_timestamp = int(start_stripped.timestamp())

    end_stripped = datetime.fromisoformat(end_date + "T23:59:59")
    end_stripped.replace(hour=23, minute=59, second=59)
    end_timestamp = int(end_stripped.timestamp())

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

        response = requests.get(ROOT_URL, params=params)
        response_dict = response.json()

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
