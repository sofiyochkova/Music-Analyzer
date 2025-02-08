"""
    This module contains functions that connect 
    the received data from Last.fm with data from Spotify.
"""

import os
import json
import asyncio

import pandas as pd

from utils import spotipy_utils

WAIT_TIME = 0.5

async def get_spotify_track_data_by_lastfm_data(lastm_data: pd.DataFrame) \
-> tuple[pd.DataFrame, list[tuple[str, str]]]:
    """For each track from a dataframe with Last.fm data return its Spotify data

    Keyword arguments:
    - lastfm_data -- dataframe with the data from Last.fm
    Return: A tuple of the dataframe with Spotify track data 
    and a list of the names and artists which were not found
    """

    semaphore = asyncio.Semaphore(5)
    uri_not_found: list[tuple[str, str]] = []

    async with semaphore:
        tasks = [
            spotipy_utils.get_track_or_album_uri_async("track", row["name"], row["artist"])
            for _, row in lastm_data.iterrows()
        ]

        tracks_names_and_uris = await asyncio.gather(*tasks)
        await asyncio.sleep(WAIT_TIME)

        for name, artist, uri in tracks_names_and_uris:
            if uri is None:
                uri_not_found.append((name, artist))

        tracks_uris = [
            uri
            for _, _, uri in tracks_names_and_uris
            if uri is not None
        ]

        tracks_uris_split = [
            tracks_uris[i:i + 50]
            for i in range(0, len(tracks_uris), 50)
        ]

        tasks_data = [
            spotipy_utils.get_data_async("tracks", uri_sublist)
            for uri_sublist in tracks_uris_split
        ]

        tracks_data = await asyncio.gather(*tasks_data)
        await asyncio.sleep(WAIT_TIME)

    tracks_dataframe = pd.concat(tracks_data)

    merged = lastm_data.merge(
        tracks_dataframe[["name", "artist", "duration", "popularity"]],
        on=["name", "artist"], how="left"
    )

    return merged, uri_not_found

async def get_spotify_artist_data_by_lastfm_data(lastfm_data: pd.DataFrame) \
-> tuple[pd.DataFrame, list[str]] | None:
    """For each artist from a dataframe with Last.fm data return their Spotify data

    Keyword arguments:
    - lastfm_data -- dataframe with data from Last.fm
    Return: A tuple of the dataframe with Spotify artist data 
    and a list of the names of artists which were not found
    """

    semaphore = asyncio.Semaphore(5)

    async with semaphore:
        tasks = [
            spotipy_utils.get_artist_uri_async(row["name"])
            for _, row in lastfm_data.iterrows()
        ]

        tracks_artists_and_uris = await asyncio.gather(*tasks)
        await asyncio.sleep(WAIT_TIME)

        uri_not_found: list[str] = []
        tracks_uris = []

        for artist, uri in tracks_artists_and_uris:
            if uri is None:
                uri_not_found.append(artist)
            else:
                tracks_uris.append(uri)

        tracks_uris = [
            uri
            for _, uri in tracks_artists_and_uris
            if uri is not None
        ]

        tracks_uris_split = [
            tracks_uris[i:i + 50]
            for i in range(0, len(tracks_uris), 50)
        ]

        tasks_data = [
            spotipy_utils.get_data_async("artists", uri_sublist)
            for uri_sublist in tracks_uris_split
        ]

        artists_data = await asyncio.gather(*tasks_data)
        await asyncio.sleep(WAIT_TIME)

    artists_spotify = pd.concat(artists_data)
    merged = lastfm_data.merge(artists_spotify[["name", "popularity"]], on="name", how="left")

    return merged, uri_not_found

async def collect_data(tracks_data, artists_data):
    "Collect both tracks and artists data asynchronously"

    tasks = [
        get_spotify_track_data_by_lastfm_data(tracks_data),
        get_spotify_artist_data_by_lastfm_data(artists_data)
    ]

    tracks_all, artists_all = await asyncio.gather(*tasks)

    return tracks_all, artists_all

def get_spotify_track_data_from_file(lastfm_data: pd.DataFrame) -> pd.DataFrame:
    "Read the uri codes of tracks from a file"
    with open(os.path.join("static", "all_tracks_uris.json"), "r", encoding="utf-8") as fd:
        tracks_uris = json.load(fd)

        needed_uris = [
            (name, artist, uri)
            for name, artist, uri in tracks_uris
            for _, row in lastfm_data.iterrows()
            if name == row["name"].lower() and artist.lower() == row["artist"].lower()
        ]

        print(needed_uris)

    return pd.DataFrame()

def get_overall_stats_table(
        tracks_data: pd.DataFrame,
        artists_data: pd.DataFrame
    ) -> pd.Series:
    """Return a Series of overall listening data
    
    Keyword arguments:
    - tracks_data -- collected track data from Spotify and Last.fm
    - artists_data -- collected artist data from Spotify and Last.fm
    """

    all_scrobbles = tracks_data["scrobble_count"].sum()
    all_artists = artists_data["scrobble_count"].sum()
    tracks_data["full_duration"] = tracks_data["scrobble_count"] * tracks_data["duration"].sum()

    tracks_data["weighted_popularity"] = tracks_data["popularity"] * \
        (tracks_data["playcount"] / all_scrobbles)
    artists_data["weighted_popularity"] = artists_data["popularity"] * \
        (artists_data["playcount"] / all_scrobbles)

    average_track_popularity = tracks_data["weighted_popularity"].mean()
    average_artist_popularity = artists_data["weighted_popularity"].mean()

    stats = [
        all_scrobbles,
        all_artists,
        average_track_popularity,
        average_artist_popularity
    ]

    indexes = [
        "Number of scrobbles",
        "Number of artists",
        "Average track popularity",
        "Average artist popularity"
    ]

    return pd.Series(data=stats, index=indexes)
