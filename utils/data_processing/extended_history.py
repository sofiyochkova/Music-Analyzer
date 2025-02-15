"""
    Module with functions which collect
    and analyze Spotify listening data based on json files.
"""

import json
from datetime import datetime

import pandas as pd

def parse_file_data(uploaded_files: dict) -> pd.DataFrame:
    """
        Return a dataframe with all data in the uploads folder.
    """

    dataframes = []

    for filename in uploaded_files:
        json_data = json.load(filename)
        selected_stats = [
            {
                "track": entry.get("master_metadata_track_name"),
                "artist": entry.get("master_metadata_album_artist_name"),
                "album": entry.get("master_metadata_album_album_name"),
                "seconds_played": entry.get("ms_played") / 1000,
                "scrobble_time": datetime.fromisoformat(entry.get("ts")),
                "reason_end": entry.get("reason_end"),
                "skipped": entry.get("skipped"),
                "track_uri": entry.get("spotify_track_uri")
            }
            for entry in json_data
            if entry.get("ms_played") / 1000 >= 30
        ]

        dataframes.append(pd.DataFrame(selected_stats))

    if dataframes:
        all_dataframes = pd.concat(dataframes)
    else:
        all_dataframes = pd.DataFrame()

    return all_dataframes
