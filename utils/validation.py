"""
    A module containing the validation for
    various types of data within the application.
"""

from datetime import date

from flask import flash
import requests
import pandas as pd

from utils.lastfm import lastfm_validation

def request_method_is_post(request_method: str) -> bool:
    "Checks if the request method is POST."
    if request_method != "POST":
        flash("Invalid request method")
        return False

    return True

def non_empty_field(field_name: str, field_value: str) -> bool:
    "Checks if a field with the given name and value is valid."
    if field_value is None or field_value == "":
        flash(f"Empty field {field_name}!")
        return False

    return True

def username_exists_in_lastfm(username: str) -> bool:
    "Checks if a username is valid."
    if not lastfm_validation.check_if_user_exists(username):
        flash(f"Last.fm username {username} not found!")
        return False

    return True

def valid_time_period(time_period: str) -> bool:
    "Checks if a time period is valid."
    if time_period not in ["7day", "1month", "3month", "6month", "12month", "overall", "custom"]:
        flash(f"Invalid time period {time_period}")
        return False

    return True

def valid_date_type(start_date: str, end_date: str) -> bool:
    "Checks if the dates are in the right date format."
    try:
        date.fromisoformat(start_date)
    except ValueError:
        flash("Invalid start date!")
        return False

    try:
        date.fromisoformat(end_date)
    except ValueError:
        flash("Invalid end date!")
        return False

    return True

def valid_date_intervals(username: str, start_date: str, end_date: str):
    "Checks if the dates are valid time intervals."

    registration_date = lastfm_validation.get_registration_date(username)

    start = date.fromisoformat(start_date)
    end = date.fromisoformat(end_date)

    if not registration_date:
        flash("Registration date was not received!")
        return False
        
    if end < start:
        flash("End date cannot be before start date!")
        return False

    if start < registration_date:
        flash(f"Start date {start_date} cannot be before the registration date!")
        return False

    if end > date.today():
        flash(f"End date {end_date} cannot be in the future!")
        return False
        
    return True

def is_file_extension_json(filename: str) -> bool:
    "Checks the file extension of a file given its filename."
    if not ('.' in filename and filename.rsplit('.', 1)[1].lower() == "json"):
        flash(f"Invalid filename: {filename}")
        return False

    return True

def check_data_type(data_type: str) -> bool:
    "Checks if a data type is valid."
    if data_type not in ["albums", "tracks", "artists"]:
        flash(f"Invalid data type {data_type}!", "error")
        return False

    return True

def non_empty_dataframe(dataframe: pd.DataFrame) -> bool:
    "Checks if a data frame is empty."
    if dataframe.empty:
        flash("No data available for the selected time period!")
        return False

    return True

def check_spotify_data_type(data_type: str) -> bool:
    """For spotify functions: check the data type 
    with which the function is going to work"""

    if data_type not in ["track", "album"]:
        flash("Invalid data type - should be track or album!")
        return False

    return True
