"""
    Functions which take data from Last.fm and
    merge it with the data found from Spotify.
"""

import os
import json

import pandas as pd

from utils.spotify import non_async

def merge_tracks_data_predefined(lastfm_tracks_data: pd.DataFrame) -> pd.DataFrame:
    "Merge track data from Last.fm and Spotify - non-async."

    uris = [
        non_async.get_track_or_album_uri("track", track["name"], track["artist"])
        for _, track in lastfm_tracks_data.iterrows()
    ]

    spotify_track_data = non_async.get_tracks_data(uris)
    df_merged = lastfm_tracks_data.merge(spotify_track_data, how="left", on=["name", "artist"])

    return df_merged

def merge_artists_data_predefined(lastfm_artists_data: pd.DataFrame, top: int=10) -> pd.DataFrame:
    "Merge artist data from Last.fm and Spotify - non-async."
        
    lastfm_artists_data = lastfm_artists_data.head(top)

    uris = [
        non_async.get_artist_uri(track["name"])
        for _, track in lastfm_artists_data.iterrows()
    ]

    spotify_artist_data = non_async.get_artists_data(uris)

    lastfm_artists_data["name_lower"] = lastfm_artists_data["name"].str.lower()
    spotify_artist_data["name_lower"] = spotify_artist_data["name"].str.lower()

    df_merged = lastfm_artists_data.merge(spotify_artist_data, how="left", on="name_lower")
    df_merged.drop(columns=["name_lower", "name_y"], inplace=True)
    df_merged.rename(columns={"name_x": "name"}, inplace=True)

    return df_merged

def get_spotify_track_data_from_file(lastfm_data: pd.DataFrame) -> pd.DataFrame:
    "Read the uri codes of tracks from a file"
    with open(os.path.join("static", "all_tracks_uris.json"), "r", encoding="utf-8") as fd:
        tracks_uris = json.load(fd)

        needed_uris = [
            (name, artist, uri)
            for _, row in lastfm_data.iterrows()
            for name, artist, uri in tracks_uris
            if name.lower() == row["name"].lower() and artist.lower() == row["artist"].lower()
        ]

        print(needed_uris)

    return pd.DataFrame()

def get_overall_stats_table_predefined(
        tracks_data: pd.DataFrame,
        artists_data: pd.DataFrame
    ) -> pd.Series:
    """Return a Series of overall listening data
        based on Spotify and Last.fm data combined
    
    Keyword arguments:
    - tracks_data -- collected track data from Spotify and Last.fm
    - artists_data -- collected artist data from Spotify and Last.fm
    """

    all_scrobbles = tracks_data["scrobble count"].sum()
    all_artists = len(artists_data.index)
    tracks_data["total_duration"] = tracks_data["scrobble count"] * tracks_data["duration"]

    total_seconds = tracks_data["total_duration"].sum()
    total_hours = total_seconds // 3600
    total_minutes = (total_seconds % 3600) // 60
    total_remaining_seconds = total_seconds % 60

    total_minutes_string = f"{total_hours}:{total_minutes}:{total_remaining_seconds}"

    tracks_data["duration"] = tracks_data["duration"].\
        apply(lambda x: f"{x // 60}:{x % 60:02d}" if pd.notna(x) else None)

    average_track_popularity = tracks_data["popularity"].mean()
    average_artist_popularity = artists_data["popularity"].mean()

    stats = [
        all_scrobbles,
        all_artists,
        total_minutes_string,
        average_track_popularity,
        average_artist_popularity
    ]

    indexes = [
        "Number of scrobbles",
        "Number of artists",
        "Total track duration",
        "Average track popularity",
        "Average artist popularity"
    ]

    return pd.Series(data=stats, index=indexes)
