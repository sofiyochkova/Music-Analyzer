"""
    A module containing the visualization
    of graphs and tables with different kinds of data.
"""

from datetime import date, datetime
from math import pi

import pandas as pd
from bokeh.plotting import figure
from bokeh.palettes import Spectral
from bokeh.models import ColumnDataSource
from bokeh.embed import components

from utils import validation
from utils.lastfm import lastfm_validation

TOOLS="wheel_zoom,box_zoom,reset,save"

def get_top_scrobbles_chart(
        data_type: str,
        top_data: pd.DataFrame,
        is_custom: bool,
        top_number: int=10
    ) -> tuple[str, str] | None:
    """Return a script and div for a bokeh graph of track or artist and number of scrobbles.
    
    Keyword arguments:
    - data_type -- tracks, artists or albums
    - is_custom -- is it based on the predefined dates or on the custom dates
    - top_data -- contains the names of the tracks and scrobble count
    - top_number (optional) -- how many entries to show
    Return: the script and the div elements to embed in the html file.
    """

    if not validation.check_data_type(data_type):
        return None

    top_data = top_data.head(top_number)

    if is_custom:
        if data_type == "artists":
            x_range = top_data["artist"]
        else:
            top_data = top_data.assign(
                artist_and_name=top_data["artist"] + " - " + top_data[data_type[:-1]]
            )
            x_range = top_data["artist_and_name"]
    else:
        if data_type == "artists":
            x_range = top_data["name"]
        else:
            top_data = top_data.assign(
                artist_and_name=top_data["artist"] + " - " + top_data["name"]
            )
            x_range = top_data["artist_and_name"]

    source = ColumnDataSource(data={
            "name": x_range,
            "scrobbles": top_data["scrobble count"],
            "color": Spectral[top_number]
        })

    plot = figure(
        x_range=x_range,
        tools=TOOLS,
        x_axis_label=data_type[:-1] + " name",
        y_axis_label="number of scrobbles",
        title=f"Number of scrobbles for top {top_number} {data_type}",
        sizing_mode="stretch_width",
    )

    plot.vbar(x="name", top="scrobbles", width=0.5, color="color", source=source)
    plot.xaxis.major_label_orientation = pi / 3

    script, div = components(plot)

    return script, div

def get_html_table(dataframe: pd.DataFrame | pd.Series, top_items: int | None=None) -> str:
    """Return the html table for a dataframe.
    
    Keyword arguments:
    - dataframe -- the dataframe we want to visualize
    - top_items (optional) -- the number of items to return
    """
    if top_items:
        dataframe = dataframe.head(top_items)

    return dataframe.to_html(classes=("table", "table-striped", "align-middle"))

def group_by_timeframe(df: pd.DataFrame, start_date: date, end_date: date) -> pd.DataFrame:
    """Group dataframe into time periods for 
    further processing in line graphs.
    """

    days_difference = (end_date - start_date).days

    if days_difference <= 15:
        df["time_group"] = df["scrobble_time"].dt.date
    elif days_difference <= 31:
        df["time_group"] = df["scrobble_time"].dt.to_period("W").dt.to_timestamp()
    else:
        df["time_group"] = df["scrobble_time"].dt.to_period("M").dt.to_timestamp()

    return df

def get_cumulative_scrobble_stats(
    dataframe: pd.DataFrame,
    start_date: date,
    end_date: date
    ) -> tuple[str, str]:
    """Return div and script of cumulative scrobbling data
    
    Keyword arguments:
    - dataframe -- the custom track data from Last.fm
    - start_date -- start date
    - end_date -- end_date 
    """

    group_by_timeframe(dataframe, start_date, end_date)

    dataframe["time_group"] = pd.to_datetime(dataframe["time_group"])
    start_datetime = datetime(start_date.year, start_date.month, start_date.day)
    end_datetime = datetime(end_date.year, end_date.month, end_date.day)

    plot = figure(
        tools=TOOLS,
        x_axis_label="date",
        y_axis_label="cumulative number of scrobbles",
        title=f"Cumulative number of scrobbles for {start_date} - {end_date}",
        sizing_mode="stretch_width",
        x_axis_type="datetime",
        x_range=(start_datetime, end_datetime)
        )

    colors = {"artist": "blue", "track": "red", "album": "green"}

    for data_type, color in colors.items():
        category_df = dataframe.groupby(
                ["time_group", data_type]
            ).size().reset_index(name="scrobble_count")

        category_df = category_df.sort_values("time_group")
        category_df = category_df.groupby("time_group") \
            .size().reset_index(name="scrobbles")
        category_df["cumulative_scrobbles"] = category_df["scrobbles"].cumsum()

        source=ColumnDataSource(category_df)
        plot.line(
            x="time_group",
            y="cumulative_scrobbles",
            source=source,
            line_width=2,
            color=color,
            legend_label=data_type.capitalize()
        )

    plot.legend.title = "Category"

    script, div = components(plot)

    return script, div

def get_total_stats_from_lastfm(
        username: str,
        lastfm_data: dict[str, pd.DataFrame],
        time_period: str | None=None,
        start_date: datetime | None=None,
        end_date: datetime | None=None,
    ) -> pd.DataFrame:
    """Return a Series of overall stats only from lastfm data.
    
    Keyword arguments:
    - username -- the lastfm user
    - lastfm_data -- a dict containing dataframes of tracks, artists
    and albums data under the corresponding keys.
    - time_period - 7day | 1month | 6month | 12month | overall | custom
    - start_date (optional) - start date if time_period is custom
    - end_date (optional) - start date if time_period is custom
    """

    all_scrobbles = lastfm_data["tracks"]["scrobble count"].sum()

    all_tracks = len(lastfm_data["tracks"].index)
    all_artists = len(lastfm_data["artists"].index)
    all_albums = len(lastfm_data["albums"].index)

    days_count = 0
    
    if start_date and end_date:
        days_count = (end_date - start_date).days

    if time_period:
        match time_period:
            case "7day":
                days_count = 7
            case "1month"| "3month" | "6month":
                days_count = int(time_period[0]) * 30
            case "12month":
                days_count = 365
            case "overall":
                registration_date = lastfm_validation.get_registration_date(username)
                days_count = (date.today() - registration_date).days

    if days_count == 0:
        return pd.DataFrame()

    average_scrobbles_per_day = all_scrobbles / days_count

    data = [
        all_scrobbles,
        all_tracks,
        all_artists,
        all_albums,
        average_scrobbles_per_day
    ]

    indexes = [
        "Number of scrobbles",
        "Number of tracks",
        "Number of artists",
        "Number of albums",
        "Average scrobbles per day"
    ]

    total_data = pd.DataFrame(data=data, index=indexes, columns=["count"])
    total_data["count"] = total_data["count"].astype(int)

    return total_data
