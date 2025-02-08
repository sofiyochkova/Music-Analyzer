"""
    A module containing the visualization
    of graphs and tables with different kinds of data.
"""

from datetime import datetime
from math import pi

import pandas as pd
from bokeh.plotting import figure
from bokeh.palettes import Spectral
from bokeh.models import ColumnDataSource
from bokeh.embed import components

from utils import validation

TOOLS="wheel_zoom,box_zoom,reset,save"

def group_by_timeframe(df: pd.DataFrame, start_date: datetime, end_date: datetime) -> pd.DataFrame:
    if (end_date - start_date).days <= 7:
        df["time_group"] = df["scrobble_time"].dt.date
    elif (end_date - start_date).days <= 31:
        df["time_group"] = df["scrobble_time"].dt.to_period("W")
    elif (end_date - start_date).days < 365:
        df["time_group"] = df["scrobble_time"].dt.to_period("M")
    else:
        df["time_group"] = df["scrobble_time"].dt.to_period("Y")

    return df

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

def get_html_table(dataframe: pd.DataFrame, top_items: int | None=None) -> str:
    """Return the html table for a dataframe.
    
    Keyword arguments:
    - dataframe -- the dataframe we want to visualize
    - top_items (optional) -- the number of items to return
    """
    if top_items:
        dataframe = dataframe.head(top_items)

    return dataframe.to_html(classes=("table", "table-striped", "align-middle"))

def get_cumulative_scrobble_stats(dataframe: pd.DataFrame, start_date: datetime, end_date: datetime) -> tuple[str, str]:
    """Return div and script of cumulative scrobbling data
    
    Keyword arguments:
    - dataframe -- the custom track data from Last.fm
    - start_date -- start date
    - end_date -- end_date 
    """

    group_by_timeframe(dataframe, start_date, end_date)
    print(dataframe)

    plot = figure(
        tools=TOOLS,
        # x_range=dataframe["time_group"],
        x_axis_label="date",
        y_axis_label="number of scrobbles",
        title=f"Cumulative number of scrobbles for period {start_date} - {end_date}",
        sizing_mode="stretch_width"
        )

    plot.line(
        x=dataframe["time_group"],
        top=dataframe[["artist"]].groupby(["artist"]).count(),
        width=0.5
        )

    plot.line(
        x=dataframe["time_group"],
        top=dataframe[["name"]].groupby(["name"]).count(),
        width=0.5
        )

    plot.line(
        x=dataframe["time_group"],
        top=dataframe[["album"]].groupby(["album"]).count(),
        width=0.5
        )

    script, div = components(plot)

    return script, div
