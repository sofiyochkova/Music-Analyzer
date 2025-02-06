from datetime import datetime
from math import pi

import pandas as pd
from bokeh.plotting import figure
from bokeh.models import Range1d, FactorRange
from bokeh.embed import components

from utils import lastfm_utils, spotipy_utils, validation

TOOLS="wheel_zoom,box_zoom,reset,save"

def get_time_divisions_for_charts(time_period: str, start_date_str: str | None=None, end_date_str: str | None=None):
    if not validation.check_time_period(time_period):
        return None

    if not start_date_str or not end_date_str:
        return None

    match time_period:
        case "7day":
            return "day"
        case "1month":
            return "week"
        case "custom":
            start_date = datetime.fromisoformat(start_date_str)
            end_date = datetime.fromisoformat(end_date_str)

            days_difference = (end_date - start_date).days
            weeks_difference = days_difference / 7
            months_difference = days_difference / 30

            if days_difference <= 7:
                return "day"
            if days_difference <= 30:
                return "week"
            
            return "month"
        case _:
            return "month"
              
def get_data_scrobbles_chart(data_type: str, top_data: pd.DataFrame, top_number: int=10) -> tuple[str, str]:
    if data_type not in ["tracks", "artists", "albums"]:
        return None

    top_data = top_data.head(top_number)

    # TODO: fix the copy warning
    if data_type != "artists":
        top_data["artist_and_name"] = top_data["artist"] + " - " + top_data["name"]
    # print(top_data["artist_and_name"])

    x_range = top_data["artist_and_name"] if data_type != "artists" else top_data["name"]

    plot = figure(
        x_range=x_range,
        tools=TOOLS,
        x_axis_label=data_type[:-1] + ' name',
        y_axis_label='number of scrobbles',
        title=f"Number of scrobbles for top {top_number} {data_type}",
        sizing_mode="stretch_width",
    )
    
    plot.vbar(x=x_range, top=top_data["playcount"], width=0.5)
    plot.xaxis.major_label_orientation = pi / 3

    script, div = components(plot)

    return script, div

def get_html_table(dataframe: pd.DataFrame, table_id: str, top_items: int | None=None):
    if top_items:
        dataframe = dataframe.head(top_items)

    return dataframe.to_html(classes=("table", "table-striped", "align-middle"), table_id=table_id)
