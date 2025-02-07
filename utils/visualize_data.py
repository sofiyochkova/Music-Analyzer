from datetime import datetime
from math import pi

import pandas as pd
from bokeh.plotting import figure
# from bokeh.models import Range1d, FactorRange
from bokeh.embed import components

from utils import validation

TOOLS="wheel_zoom,box_zoom,reset,save"

def group_by_timeframe(df: pd.DataFrame, start_date: str, end_date: str) -> None | str:
    if not validation.is_not_empty(start_date) or not validation.is_not_empty(end_date):
        return "Invalid dates!"

    # if validation.are_dates_valid(start_date_str, end_date_str):
    start_datetime = datetime.fromisoformat(start_date)
    end_datetime = datetime.fromisoformat(end_date)

    if (end_datetime - start_datetime).days <= 7:
        df["time_group"] = df["scrobble_time"].date
    elif (end_datetime - start_datetime).days <= 31:
        df["time_group"] = df["scrobble_time"].to_period("W")
    elif (end_datetime - start_datetime).days < 365:
        df["time_group"] = df["scrobble_time"].to_period("M")
    else:
        df["time_group"] = df["scrobble_time"].to_period("Y")

    return None

def get_top_scrobbles_chart_predefined(data_type: str, top_data: pd.DataFrame, top_number: int=10) -> tuple[str, str] | str:
    if data_type not in ["tracks", "artists", "albums"]:
        return "Invalid data type!"

    top_data = top_data.head(top_number)

    if data_type != "artists":
        top_data["artist_and_name"] = top_data["artist"] + " - " + top_data["name"]
        x_range = top_data["artist_and_name"]
    else:
        x_range = top_data["name"]

    plot = figure(
        x_range=x_range,
        tools=TOOLS,
        x_axis_label=data_type[:-1] + " name",
        y_axis_label="number of scrobbles",
        title=f"Number of scrobbles for top {top_number} {data_type}",
        sizing_mode="stretch_width",
    )

    plot.vbar(x=x_range, top=top_data["playcount"], width=0.5)
    plot.xaxis.major_label_orientation = pi / 3

    script, div = components(plot)

    return script, div

def get_top_scrobbles_chart_custom(data_type: str, top_data: pd.DataFrame, top_number: int=10):
    top_data = top_data.head(top_number)

    match data_type:
        case "artists":
            x_range = top_data["artist"]
        case "albums" | "tracks":
            top_data["artist_and_name"] = top_data["artist"] + " - " + top_data[data_type[:-1]]
            x_range = top_data["artist_and_name"]

    plot = figure(
        x_range=x_range,
        tools=TOOLS,
        x_axis_label=data_type[:-1] + " name",
        y_axis_label="number of scrobbles",
        title=f"Number of scrobbles for top {top_number} {data_type}",
        sizing_mode="stretch_width",
    )

    match data_type:
        case "albums" | "tracks":
            plot.vbar(x=x_range, top=top_data["scrobbles"], width=0.5)
        case "artists":
            plot.vbar(x=x_range, top=top_data["scrobbles"], width=0.5)

    plot.xaxis.major_label_orientation = pi / 3
    script, div = components(plot)

    return script, div

def get_html_table(dataframe: pd.DataFrame, top_items: int | None=None) -> str:
    if top_items:
        dataframe = dataframe.head(top_items)

    return dataframe.to_html(classes=("table", "table-striped", "align-middle"))

def get_cumulative_scrobble_stats(dataframe: pd.DataFrame, start_date: str, end_date: str):
    group_by_timeframe(dataframe, start_date, end_date)

    plot = figure(
        tools=TOOLS,
        # x_range=dataframe["time_group"],
        x_axis_label="date",
        y_axis_label="number of scrobbles",
        title=f"Cumulatime number of scrobbles for time period {start_date} - {end_date}",
        sizing_mode="stretch_width"
    )

    plot.line(x=dataframe["time_group"], top=dataframe[["artist"]].groupby(["artist"]).count(), width=0.5)
    plot.line(x=dataframe["time_group"], top=dataframe[["name"]].groupby(["name"]).count(), width=0.5)
    plot.line(x=dataframe["time_group"], top=dataframe[["album"]].groupby(["album"]).count(), width=0.5)

    script, div = components(plot)

    return script, div
