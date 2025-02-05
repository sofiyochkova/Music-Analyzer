import pandas as pd

from utils import lastfm_utils, spotipy_utils

# data_type - "artists" or "tracks"
def get_spotify_data_by_lastfm_data(lastm_data: pd.DataFrame):
    tracks_names_and_uris = [
        (name, artist, spotipy_utils.get_track_or_album_uri("track", name, artist))
        for name, artist in lastm_data[["name", "artist"]].values
    ]

    tracks_uris = [
        tup[2]
        for tup in tracks_names_and_uris
        if tup[2] is not None
    ]

    tracks_uris_split = [
        tracks_uris[i:i + 50]
        for i in range(0, len(tracks_uris), 50)
    ]

    tracks_data: list[dict] = []

    for uri_sublist in tracks_uris_split:
        tracks_data += spotipy_utils.get_tracks_data(uri_sublist)

    return pd.DataFrame(tracks_data)

if __name__ == "__main__":
    lfm = lastfm_utils.get_top_data_predefined_time_period("sandy1009", "tracks", "7day")
    # print(lfm[["name", "artist"]].values)

    if lfm is not None:
        print(get_spotify_data_by_lastfm_data(lfm))