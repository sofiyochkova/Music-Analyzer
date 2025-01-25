import requests #type: ignore
import dotenv
import os
import pandas as pd
from datetime import date, datetime

dotenv.load_dotenv()
LASTFM_API_KEY = os.getenv("LASTFM_API_KEY")

root_url = "http://ws.audioscrobbler.com/2.0/"

def check_if_user_exists(username: str) -> bool:
    params = {
        "method": "user.getinfo",
        "user": username,
        "api_key": LASTFM_API_KEY,
        "format": "json"
    }

    response = requests.get(root_url, params=params)

    if("error" in response.json().keys()):
        return False

    return True

def get_registration_date(username: str):
    params = {
        "method": "user.getinfo",
        "user": username,
        "api_key": LASTFM_API_KEY,
        "format": "json"
    }

    response = requests.get(root_url, params=params)

    if("error" in response.json().keys()):
        return None

    return date.fromtimestamp(int(response.json()["user"]["registered"]["unixtime"]))

def get_top_data_predefined_time_period(username: str, data_type: str, time_period: str) -> pd.DataFrame | None:
    if not check_if_user_exists(username):
        return None

    # TODO: return better values, maybe the messages
    if data_type not in ["albums", "tracks", "artists"]:
        print(f"Invalid data type {data_type}!")
        return None

    if time_period not in ["7day", "1month", "3month", "6month", "12month", "overall"]:
        print(f"Invalid time period {time_period}!")
        return None

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

        response = requests.get(root_url, params=params)
        response_dict = response.json()

        # TODO: better handling of this case
        if "error" in response_dict.keys():
            print(response_dict["error"])

        list_tracks += [
            {
                "name": entry["name"], 
                "artist": None if data_type == "artists" else entry["artist"]["name"], 
                "rank": entry["@attr"]["rank"],
                "playcount": entry["playcount"]
            }
            
            for entry in response_dict["top" + data_type][data_type[:-1]]
        ]
        
        total_pages = response_dict["top" + data_type]["@attr"]["totalPages"]

        if page >= int(total_pages):
            break

        page += 1

    return pd.DataFrame(list_tracks)

def get_recent_tracks_by_custom_dates(username: str, start_date: str, end_date: str) -> pd.DataFrame:
    start_stripped = datetime.strptime(start_date, "%d.%m.%Y")
    start_timestamp = int(start_stripped.timestamp())

    end_stripped = datetime.strptime(end_date, "%d.%m.%Y")
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

        response = requests.get(root_url, params=params)
        response_dict = response.json()
        
        # TODO: handle the now playing track if there is one
        list_response += [
            {
                "name": track["name"], 
                "artist": track["artist"]["#text"],
                "album": track["album"]["#text"],
                "image": track["image"][-1],
                "scrobble_date_uts": track["date"]["uts"],
                "scrobble_date_text": track["date"]["#text"]
            }
            for track in response_dict["recenttracks"]["track"][1:]
            if "attr" not in track.keys()
        ]

        total_pages = response_dict["recenttracks"]["@attr"]["totalPages"]

        if page >= int(total_pages):
            break

        page += 1

    return pd.DataFrame(list_response)
    