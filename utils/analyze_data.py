import asyncio

import pandas as pd

from utils import spotipy_utils, validation

WAIT_TIME = 0.5

async def get_spotify_track_data_by_lastfm_data(lastm_data: pd.DataFrame) \
-> tuple[pd.DataFrame, list[tuple[str, str]]]:
    if isinstance(lastm_data, str):
        return lastm_data

    semaphore = asyncio.Semaphore(5)

    async with semaphore:
        tasks = [
            spotipy_utils.get_track_or_album_uri_async("track", row["name"], row["artist"])
            for _, row in lastm_data.iterrows()
        ]

        tracks_names_and_uris = await asyncio.gather(*tasks)
        await asyncio.sleep(WAIT_TIME)

        uri_not_found: list[tuple[str, str]] = []

        for name, artist, uri in tracks_names_and_uris:
            if uri is None:
                uri_not_found.append((name, artist))

        tracks_uris = [
            tup[2]
            for tup in tracks_names_and_uris
            if tup[2] is not None
        ]

        tracks_uris_split = [
            tracks_uris[i:i + 50]
            for i in range(0, len(tracks_uris), 50)
        ]

        tasks_data = [
            spotipy_utils.get_tracks_data_async(uri_sublist)
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

async def get_spotify_artist_data_by_lastfm_data(lastfm_data: pd.DataFrame) -> tuple[pd.DataFrame, list[str]]:
    if isinstance(lastfm_data, str):
        print(lastfm_data)
        return None

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
            tup[1]
            for tup in tracks_artists_and_uris
            if tup[1] is not None
        ]

        tracks_uris_split = [
            tracks_uris[i:i + 50]
            for i in range(0, len(tracks_uris), 50)
        ]
    
        tasks_data = [
            spotipy_utils.get_artists_data_async(uri_sublist)
            for uri_sublist in tracks_uris_split
        ]
        
        artists_data = await asyncio.gather(*tasks_data)
        await asyncio.sleep(WAIT_TIME)

    artists_spotify = pd.concat(artists_data)
    merged = lastfm_data.merge(artists_spotify[["name", "popularity"]], on="name", how="left")

    return merged, uri_not_found

async def collect_data(tracks_data, artists_data):
    tasks = [
        get_spotify_track_data_by_lastfm_data(tracks_data), 
        get_spotify_artist_data_by_lastfm_data(artists_data)
    ]

    tracks_all, artists_all = await asyncio.gather(*tasks)

    return tracks_all, artists_all

def get_overall_stats_table(time_period: str, tracks_data: pd.DataFrame, artists_data: pd.DataFrame) \
-> pd.Series | None:
    # TODO: average scrobbles per day
    if not validation.is_time_period_valid(time_period):
        return None

    all_scrobbles = tracks_data["playcount"].sum()
    all_artists = artists_data["playcount"].sum()
    tracks_data["full_duration"] = tracks_data["playcount"] * tracks_data["duration"].sum()

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
