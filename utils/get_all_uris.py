import json

import lastfm_utils
import spotipy_utils

def get_all_track_uris(username):
    all_data = lastfm_utils.get_top_data_predefined_period(username, "tracks", "overall")
    line_data: list[dict[str, str | None]] = []

    line_data = [
        {
            "name": name,
            "artist": artist,
            "uri": spotipy_utils.get_track_or_album_uri("track", name, artist)
        }
        for _, row in all_data.iterrows()
        if (name := row["name"]) and (artist := row["artist"])
    ]

    with open("all_tracks_uris.json", "w", encoding="utf-8") as fd:
        json.dump(line_data, fd, indent=2)

def get_all_artist_uris(username):
    all_data = lastfm_utils.get_top_data_predefined_period(username, "artists", "overall")
    line_data: list[dict[str, str | None]] = []

    # semaphore = asyncio.Semaphore(5)

    line_data = [
        {
            "name": name,
            "uri": spotipy_utils.get_artist_uri(name)
        }
        for _, row in all_data.iterrows()
        if (name := row["name"])
    ]

    with open("all_artists_uris.json", "w", encoding="utf-8") as fd:
        json.dump(line_data, fd, indent=2)

if __name__ == "__main__":
    get_all_track_uris("sandy1009")
    # print(spotipy_utils.get_artist_uri("The Clause"))
