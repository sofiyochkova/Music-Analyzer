"""
    General Last.fm functions that don't
    depend on the chosen time period.
"""

import os
from datetime import date

import requests
from flask import flash

REQUEST_TIMEOUT = 600
LASTFM_API_KEY = os.getenv("LASTFM_API_KEY")
ROOT_URL = "http://ws.audioscrobbler.com/2.0/"

def check_lastfm_response(response: requests.Response) -> bool:
    "Checks if a response from Last.fm is valid."
    try:
        response_dict = response.json()
    except requests.exceptions.JSONDecodeError:
        flash("API is down right now...")
        return False

    if "error" in response_dict.keys():
        flash("The Last.fm API encountered an error: " + response_dict.get("message"))
        return False

    return True

def check_if_user_exists(username: str) -> bool:
    "Send a request to the Last.fm API checking if a user exists."

    params = {
        "method": "user.getinfo",
        "user": username,
        "api_key": LASTFM_API_KEY,
        "format": "json"
    }

    response = requests.get(ROOT_URL, params=params, timeout=REQUEST_TIMEOUT)

    return response.ok

def get_registration_date(username: str) -> date | None:
    "Get the registration date of a user by username."

    params = {
        "method": "user.getinfo",
        "user": username,
        "api_key": LASTFM_API_KEY,
        "format": "json"
    }

    response = requests.get(ROOT_URL, params=params, timeout=REQUEST_TIMEOUT)

    if not check_lastfm_response(response):
        return None

    return date.fromtimestamp(int(response.json()["user"]["registered"]["unixtime"]))
