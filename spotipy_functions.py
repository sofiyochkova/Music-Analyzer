import spotipy # type: ignore
from spotipy.oauth2 import SpotifyClientCredentials # type: ignore
import dotenv
import requests

dotenv.load_dotenv()

auth_manager = SpotifyClientCredentials()
spotify_instance = spotipy.Spotify(auth_manager=auth_manager)

def find_artist_uri_spotify(artist_name: str) -> str | None:
    search_results = spotify_instance.search(q=f"artist:{artist_name}", type="artist")

    # TODO: empty result check
    search_results_filtered = [
        result["uri"]
        for result in search_results["artists"]["items"]
        if result["name"] == artist_name
    ]

    return search_results_filtered[0]

# TODO: validation + case when an artist as two songs with the same name
def find_track_or_album_uri_spotify(data_type: str, name: str, artist: str) -> list[str]:
    search_results = spotify_instance.search(q=f"{data_type}:{name} artist:{artist}", type=data_type)
    
    # TODO: empty result check
    search_results_filtered = [
        result["uri"]
        for result in search_results[data_type + "s"]["items"]
        if result["name"] == name
    ]

    return search_results_filtered

def get_artists_data(uri_list: list[str]) -> list[dict] | None:
    # TODO: add error handling

    artists_data = spotify_instance.artists(uri_list)

    artists_data_clean = [
        {
            "name": artist["name"],
            "image": ([] if artist["images"] == [] else artist["images"][0]["url"]),
            "genres": artist["genres"],
            "popularity": artist["popularity"], 
            "uri": artist["uri"]
        }
        for artist in artists_data["artists"]
    ]

    return artists_data_clean

def get_tracks_data(uri_list: list[str]) -> list[dict] | None:
    result_data = spotify_instance.tracks(uri_list)

    search_results_clean = [
                {
                    "name": result["name"],
                    "artist": result["artists"][0]["name"],
                    "album": result["album"]["name"],
                    "image": ([] if result["album"]["images"] == [] else result["album"]["images"][0]["url"]),
                    "release_date": result["album"]["release_date"],
                    "duration": result["duration_ms"],
                    "popularity": result["popularity"], 
                    "uri": result["uri"]
                }
                for result in result_data["tracks"]
            ]

    return search_results_clean

def get_albums_data(uri_list: list[str]) -> list[dict] | None:
    result_data = spotify_instance.albums(uri_list)

    search_results_clean = [
                {
                    "name": result["name"],
                    "artist": result["artists"][0]["name"],
                    "image": ([] if result["images"] == [] else result["images"][0]["url"]),
                    "release_date": result["release_date"],
                    "popularity": result["popularity"], 
                    "uri": result["uri"]
                }
                for result in result_data["albums"]
            ]

    return search_results_clean
