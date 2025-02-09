"""
    Asynchronous functions which collect
    Spotify data using spotipy and Spotify's API.
"""

import asyncio

import pandas as pd

from utils.spotify import non_async

WAIT_TIME = 0.5
SEMAPHORE_NUMBER = 3

async def get_artist_uri_async(artist_name: str) -> tuple[str, str | None]:
    "Asynchronous version of get_artist_uri."

    semaphore = asyncio.Semaphore(SEMAPHORE_NUMBER)

    async with semaphore:
        artist_uri = await asyncio.to_thread(non_async.get_artist_uri, artist_name)
        await asyncio.sleep(WAIT_TIME)

    return (artist_name, artist_uri)

async def get_track_or_album_uri_async(
        data_type: str,
        name: str,
        artist: str
        ) -> tuple[str, str, str | None]:
    "Asynchronous version of get_track_or_album_uri."

    semaphore = asyncio.Semaphore(SEMAPHORE_NUMBER)

    async with semaphore:
        uri = await asyncio.to_thread(non_async.get_track_or_album_uri, data_type, name, artist)
        await asyncio.sleep(WAIT_TIME)

    return (name, artist, uri)

async def get_spotify_track_data_by_lastfm_data(lastm_data: pd.DataFrame) \
-> tuple[pd.DataFrame, list[tuple[str, str]]]:
    """For each track from a dataframe with Last.fm data return its Spotify data

    Keyword arguments:
    - lastfm_data -- dataframe with the data from Last.fm
    Return: A tuple of the dataframe with Spotify track data 
    and a list of the names and artists which were not found
    """

    semaphore = asyncio.Semaphore(SEMAPHORE_NUMBER)
    uri_not_found: list[tuple[str, str]] = []

    async with semaphore:
        tasks = [
            get_track_or_album_uri_async("track", row["name"], row["artist"])
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
        ]

        tracks_uris_split = [
            tracks_uris[i : i + 50]
            for i in range(0, len(tracks_uris), 50)
        ]

        tasks_data = [
            get_data_async("tracks", uri_sublist)
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

    semaphore = asyncio.Semaphore(SEMAPHORE_NUMBER)

    async with semaphore:
        tasks = [
            get_artist_uri_async(row["name"])
            for _, row in lastfm_data.iterrows()
        ]

        tracks_artists_and_uris = await asyncio.gather(*tasks)
        await asyncio.sleep(WAIT_TIME)

        uri_not_found: list[str] = []
        tracks_uris: list[str | None] = []

        for artist, uri in tracks_artists_and_uris:
            if uri is None:
                uri_not_found.append(artist)
            else:
                tracks_uris.append(uri)

        tracks_uris = [
            uri
            for _, uri in tracks_artists_and_uris
        ]

        tracks_uris_split = [
            tracks_uris[i : i + 50]
            for i in range(0, len(tracks_uris), 50)
        ]

        tasks_data = [
            get_data_async("artists", uri_sublist)
            for uri_sublist in tracks_uris_split
        ]

        artists_data = await asyncio.gather(*tasks_data)
        await asyncio.sleep(WAIT_TIME)

    artists_spotify = pd.concat(artists_data)
    merged = lastfm_data.merge(artists_spotify[["name", "popularity"]], on="name", how="left")

    return merged, uri_not_found

async def get_data_async(data_type: str, uri_list: list[str | None]) -> pd.DataFrame:
    """Takes a list of uri codes and returns a dataframe with their data.
    
    Keyword arguments:
    - data_type -- tracks | albums | artists
    - uri_list -- list of uri codes
    """

    data_function = {
        "tracks": non_async.get_tracks_data,
        "artists": non_async.get_artists_data, "albums": non_async.get_albums_data
        }

    semaphore = asyncio.Semaphore(5)

    async with semaphore:
        result = await asyncio.to_thread(data_function[data_type], uri_list)
        await asyncio.sleep(WAIT_TIME)
    return result

async def collect_data(tracks_data, artists_data):
    "Collect both tracks and artists data asynchronously"

    tasks = [
        get_spotify_track_data_by_lastfm_data(tracks_data),
        get_spotify_artist_data_by_lastfm_data(artists_data)
    ]

    tracks_all, artists_all = await asyncio.gather(*tasks)

    return tracks_all, artists_all
