import requests #type: ignore
import dotenv
import os
import pandas as pd

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

# data_type = albums, artists, tracks
def get_top_data_predefined(username: str, data_type: str, time_period: str): #-> pd.DataFrame:
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

        with open("idk.txt", "a") as fd:
            fd.write(str(response_dict))

        # TODO: better handling of this
        if "error" in response_dict.keys():
            print(response_dict)

        # TODO: better handling if data_type = artists
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
    print(list_tracks)
