"""
    Module with functions which collect
    and analyze Spotify listening data based on json files.
"""

import json
import os
from datetime import datetime

import pandas as pd

def parse_file_data(upload_folder: str) -> pd.DataFrame:
    """
        Return a dataframe with all data in the uploads folder.
    """
                    
    for filename in os.listdir(upload_folder):
        file_path = os.path.join(upload_folder, filename)

        dataframes = []

        with open(file_path, "r", encoding="utf-8") as fd:
            json_data = json.load(fd)
            selected_stats = [
                {
                    "name": entry.get("master_metadata_track_name"),
                    "artist": entry.get("master_metadata_album_artist_name"),
                    "album": entry.get("master_metadata_album_album_name"),
                    "time": datetime.fromisoformat(entry.get("ts")),
                    "reason_end": entry.get("reason_end"),
                    "skipped": entry.get("skipped"),
                    "track_uri": entry.get("spotify_track_uri")
                }
                for entry in json_data
            ]

            dataframes.append(pd.DataFrame(selected_stats))

    if dataframes:
        all_dataframes = pd.concat(dataframes)
    else:
        all_dataframes = pd.DataFrame()

    return all_dataframes
