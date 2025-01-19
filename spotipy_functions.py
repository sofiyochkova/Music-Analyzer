import spotipy # type: ignore
from spotipy.oauth2 import SpotifyClientCredentials # type: ignore
import dotenv

dotenv.load_dotenv()

auth_manager = SpotifyClientCredentials()
spotify_instance = spotipy.Spotify(auth_manager=auth_manager)

# TODO: return the right artist in case of artists with the same name where the first result isn't the right one
def search_artist_spotify(name: str):
    if(not name == ""):
        search_results = spotify_instance.search(q=f"artist:{name}", type="artist")
        # TODO: search results empty check
        search_results_clean = [
            {
                "name": result["name"], 
                "image": ([] if result["images"] == [] else result["images"][0]["url"]),
                "genres": result["genres"],
                "popularity": result["popularity"], 
                "uri": result["uri"]
            }
            for result in search_results["artists"]["items"]
            if result["name"] == name
        ]

    return search_results_clean
    