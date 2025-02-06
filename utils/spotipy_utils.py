import spotipy # type: ignore
from spotipy.oauth2 import SpotifyClientCredentials # type: ignore
import dotenv
import pandas as pd
import asyncio

dotenv.load_dotenv()

auth_manager = SpotifyClientCredentials()
spotify_instance = spotipy.Spotify(auth_manager=auth_manager)

WAIT_TIME = 0.5

# TODO: refine search -> some artists are not found
def get_artist_uri(artist_name: str) -> str | None:
    #spotify search apparently doesn't like special symbols
    artist_name = artist_name.strip("'")

    search_results = spotify_instance.search(q=f"artist:{artist_name}", type="artist", limit=50)

    if search_results["artists"]["items"] == []:
        return None

    search_results_filtered = [
        result["uri"]
        for result in search_results["artists"]["items"]
        if result["name"].lower() == artist_name.lower()
    ]

    return None if search_results_filtered == [] else search_results_filtered[0]

def get_track_or_album_uri(data_type: str, name: str, artist: str) -> str | None:
    if data_type not in ["track", "album"]:
        print("Invalid data type - should be track or album!")
        return None

    search_results = spotify_instance.search(q=f"{data_type}:{name} artist:{artist}", type=data_type)

    if search_results[data_type + "s"]["items"] == []:
        return None

    search_results_tuples: list[tuple[str, str]] = sorted([
        (result["uri"], result["popularity"])
        for result in search_results[data_type + "s"]["items"]
        if result["name"].lower() == name.lower()
    ], key=lambda item: item[1], reverse=True)

    search_results_filtered = list(map(lambda tup: tup[0], search_results_tuples))

    return None if not search_results_filtered else search_results_filtered[0]

# unfortunately, it doesn't return genres for most artists right now...
def get_artists_data(uri_list: list[str]) -> pd.DataFrame:
    # TODO: add error handling

    artists_data = spotify_instance.artists(uri_list)

    artists_data_clean = [
        {
            "name": artist["name"],
            "image": ([] if artist["images"] == [] else artist["images"][0]["url"]),
            "genres": artist["genres"],
            "popularity": int(artist["popularity"]), 
            "uri": artist["uri"]
        }
        for artist in artists_data["artists"]
    ]

    return pd.DataFrame(artists_data_clean)

def get_tracks_data(uri_list: list[str]) -> pd.DataFrame:
    result_data = spotify_instance.tracks(uri_list)

    search_results_clean = [
                {
                    "name": result["name"],
                    "artist": result["artists"][0]["name"],
                    "album": result["album"]["name"],
                    "image": ([] if result["album"]["images"] == [] else result["album"]["images"][0]["url"]),
                    "release_date": result["album"]["release_date"],
                    "duration": int(result["duration_ms"]),
                    "popularity": int(result["popularity"]), 
                    "uri": result["uri"]
                }
                for result in result_data["tracks"]
            ]

    return pd.DataFrame(search_results_clean)

def get_albums_data(uri_list: list[str]) -> pd.DataFrame:
    result_data = spotify_instance.albums(uri_list)

    search_results_clean = [
                {
                    "name": result["name"],
                    "artist": result["artists"][0]["name"],
                    "image": ([] if result["images"] == [] else result["images"][0]["url"]),
                    "release_date": result["release_date"],
                    "popularity": int(result["popularity"]), 
                    "uri": result["uri"]
                }
                for result in result_data["albums"]
            ]

    return pd.DataFrame(search_results_clean)

async def get_artist_uri_async(artist_name: str) -> tuple[str, str | None]:
    semaphore = asyncio.Semaphore(5)

    async with semaphore:
        result = await asyncio.to_thread(get_artist_uri, artist_name)
        await asyncio.sleep(WAIT_TIME)
    
    return (artist_name, result)

async def get_track_or_album_uri_async(data_type: str, name: str, artist: str) -> tuple[str, str, str | None]:
    semaphore = asyncio.Semaphore(5)

    async with semaphore:
        result = await asyncio.to_thread(get_track_or_album_uri, data_type, name, artist)
        await asyncio.sleep(WAIT_TIME)

    return (name, artist, result)

async def get_tracks_data_async(uri_list: list[str]) -> pd.DataFrame:
    semaphore = asyncio.Semaphore(5)

    async with semaphore:
        result = await asyncio.to_thread(get_tracks_data, uri_list)
        await asyncio.sleep(WAIT_TIME)
    return result

async def get_artists_data_async(uri_list: list[str]) -> pd.DataFrame:
    semaphore = asyncio.Semaphore(5)

    async with semaphore:
        result = await asyncio.to_thread(get_artists_data, uri_list)
        await asyncio.sleep(WAIT_TIME)
    return result
