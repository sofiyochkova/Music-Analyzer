"""
    Functions which take all tracks or artists from a Last.fm user's
    listening history and write the uri codes into a file
"""

import json

from utils.spotify import non_async
from utils.lastfm import get_data

def get_all_track_uris(username: str) -> None:
    "Dumps the uri codes of all listened to tracks into a json file"
    all_data = get_data.top_data_predefined_period(username, "tracks", "overall")
    line_data: list[dict[str, str | None]] = []

    line_data = [
        {
            "name": name,
            "artist": artist,
            "uri": non_async.get_track_or_album_uri("track", name, artist)
        }
        for _, row in all_data.iterrows()
        if (name := row["name"]) and (artist := row["artist"])
    ]

    with open("all_tracks_uris.json", "w", encoding="utf-8") as fd:
        json.dump(line_data, fd, indent=2)

def get_all_artist_uris(username: str) -> None:
    "Dumps the uri codes of all listened to artists into a json file"

    all_data = get_data.top_data_predefined_period(username, "artists", "overall")
    line_data: list[dict[str, str | None]] = []

    line_data = [
        {
            "name": name,
            "uri": non_async.get_artist_uri(name)
        }
        for _, row in all_data.iterrows()
        if (name := row["name"])
    ]

    with open("all_artists_uris.json", "w", encoding="utf-8") as fd:
        json.dump(line_data, fd, indent=2)
