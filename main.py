"""
    Main module that contains all pages
    - main_page - index
    - validate_data - check form data
    - lastfm_analysis_predefined - lastfm API data for specific time periods
    - lastfm_analysis_custom - lastfm API data for custom time intervals
    - see_more - extended view of tables
    - validate_files - check uploaded json files
    - spotify_analysis - uses the Spotify Extended Listening data
"""

import os
from datetime import date

from flask import Flask, render_template, url_for, request, redirect, session
from flask_session.__init__ import Session #type: ignore

from utils import validation
from utils.lastfm import get_data, lastfm_validation
from utils.data_processing import visualize_data, extended_history

app = Flask(__name__)

SESSION_FOLDER = os.path.join(os.getcwd(), "flask_session")

if not os.path.exists(SESSION_FOLDER):
    os.makedirs(SESSION_FOLDER, exist_ok=True)

app.config["SESSION_FILE_DIR"] = SESSION_FOLDER
app.config["SESSION_TYPE"] = "filesystem"
app.config["SESSION_PERMANENT"] = False
app.config["TEMPLATES_AUTO_RELOAD"] = True

Session(app)

@app.route("/")
def main_page():
    "index page - contains two forms for lastfm data and spotify data"
    return render_template("index.html", title="Music Analyzer Index")

@app.route("/validate_data", methods=["POST"])
def validate_data():
    "validation for the lastfm form data"
    if not validation.request_method_is_post(request.method):
        return redirect(url_for("main_page"))

    for field in ["username", "time_period"]:
        if not validation.non_empty_field(field, request.form.get(field)):
            return redirect(url_for("main_page"))

    username = request.form["username"]
    time_period = request.form["time_period"]

    if not (
        lastfm_validation.check_if_user_exists(username)
        and validation.valid_time_period(time_period)
    ):
        return redirect(url_for("main_page"))

    if time_period == "custom":
        start_date = request.form.get("start_date")
        end_date = request.form.get("end_date")

        if not (
            validation.valid_date_type(start_date, end_date)
            and validation.valid_date_intervals(username, start_date, end_date)
        ):
            return redirect(url_for("main_page"))

        return redirect(url_for(
            "lastfm_analysis_custom",
            username=username,
            time_period=time_period,
            start=start_date,
            end=end_date
        ))

    return redirect(url_for(
        "lastfm_analysis_predefined",
        username=username,
        time_period=time_period
    ))

@app.route("/lastfm_analysis/<username>/<time_period>")
def lastfm_analysis_predefined(username: str, time_period: str):
    "Last.fm data visualization for a specific time period."

    if not (
        validation.username_exists_in_lastfm(username)
        and validation.valid_time_period(time_period)
        and time_period != "custom"
    ):
        return redirect(url_for("main_page"))

    graphs = {}
    full_tables = {}
    short_tables = {}
    top_data = {}

    for data_type in ["tracks", "albums", "artists"]:
        top_data[data_type] = get_data.top_data_predefined_period(username, data_type, time_period)

        if not validation.non_empty_dataframe(top_data[data_type]):
            break

        full_tables[data_type] = visualize_data.get_html_table(top_data[data_type])
        short_tables[data_type] = visualize_data.get_html_table(top_data[data_type], 15)

        chart = visualize_data.get_top_scrobbles_chart(data_type, top_data[data_type], False)

        if chart:
            script, div = chart

            graphs[data_type] = {
                "script": script,
                "div": div
            }

    overall_stats = visualize_data.get_total_stats_from_lastfm(
        username,
        top_data,
        time_period
    )
    overall_stats_html = visualize_data.get_html_table(overall_stats)

    similar_artists = get_data.all_similar_artists(top_data["artists"]["name"])
    similar_artists = similar_artists.head(10)
    similar_artists_dict = similar_artists.to_dict(orient="records")

    session["graphs"] = graphs
    session["full_tables"] = full_tables
    session["short_tables"] = short_tables
    session["overall_stats"] = overall_stats_html

    return render_template(
        "lastfm_analysis.html",
        title=f"{username} Track Analysis",
        username=username,
        time_period=time_period,
        similar_artists=similar_artists_dict
    )

@app.route("/lastfm_analysis/<username>/custom")
def lastfm_analysis_custom(username):
    "Last.fm data for a custom time frame - from start_date to end_date"

    if not (
        validation.username_exists_in_lastfm(username) \
        and request.args.get("time_period") == "custom"
    ):
        return url_for("main_page")

    start_date = request.args.get("start")
    end_date = request.args.get("end")

    if not (
        validation.non_empty_field("start_date", start_date)
        and validation.non_empty_field("end_date", end_date)
        and validation.valid_date_type(start_date, end_date)
        and validation.valid_date_intervals(username, start_date, end_date)
    ):
        return redirect(url_for("main_page"))

    custom_data = get_data.recent_tracks_by_custom_dates(username, start_date, end_date)

    if not validation.non_empty_dataframe(custom_data):
        return redirect(url_for("main_page"))

    graphs = {}
    full_tables = {}
    short_tables = {}
    grouped_data = {}
    custom_graphs = {}

    for data_type in ["tracks", "albums", "artists"]:
        match data_type:
            case "artists":
                grouped_data[data_type] = custom_data.groupby("artist", as_index=False).size()
            case "albums" | "tracks":
                grouped_data[data_type] = custom_data.groupby(
                    [data_type[:-1], "artist"],
                    as_index=False
                ).size()

        grouped_data[data_type].rename(columns={"size": "scrobble count"}, inplace=True)
        grouped_data[data_type].sort_values(
            "scrobble count",
            ascending=False,
            inplace=True,
            ignore_index=True
            )
        grouped_data[data_type].index += 1

        full_tables[data_type] = visualize_data.get_html_table(grouped_data[data_type])
        short_tables[data_type] = visualize_data.get_html_table(grouped_data[data_type], 15)

        script, div = visualize_data.get_top_scrobbles_chart(
            data_type,
            grouped_data[data_type],
            True
            )

        graphs[data_type] = {
            "script": script,
            "div": div
        }

    script, div = visualize_data.get_cumulative_scrobble_stats(
        custom_data,
        date.fromisoformat(start_date),
        date.fromisoformat(end_date)
        )
    custom_graphs["cumulative"] = {
        "script": script,
        "div": div
    }

    overall_stats = visualize_data.get_total_stats_from_lastfm(
        username,
        grouped_data,
        start_date=date.fromisoformat(start_date),
        end_date=date.fromisoformat(end_date)
        )
    overall_stats_html = visualize_data.get_html_table(overall_stats)

    similar_artists_dict = get_data.all_similar_artists(grouped_data["artists"]["artist"]) \
    .head(10) \
    .to_dict(orient="records")

    session["graphs"] = graphs
    session["full_tables"] = full_tables
    session["short_tables"] = short_tables
    session["custom_graphs"] = custom_graphs
    session["overall_stats"] = overall_stats_html

    return render_template(
        "lastfm_analysis_custom.html",
        title=f"{username} Track Analysis",
        username=username,
        start_date=start_date,
        end_date=end_date,
        time_period=request.args.get("time_period"),
        similar_artists=similar_artists_dict
    )

@app.route("/lastfm_analysis/<username>/<time_period>/<data_type>")
def see_more(username, time_period, data_type):
    "visualize the whole table"
    title = request.args.get("prev_title")
    full_table = session.get("full_tables", {}).get(data_type)

    return render_template(
        "see_more.html",
        username=username,
        time_period=time_period,
        prev_title=title,
        data_type=data_type,
        full_table=full_table,
        title=f"Full {data_type} table view"
    )

@app.route("/spotify_analysis", methods=["POST"])
def spotify_analysis():
    """Check if uploaded files are valid and then
        show page with data from the files."""

    if not validation.filelist_is_not_empty(request):
        return redirect(url_for("main_page"))

    files = request.files.getlist("file")

    for file in files:
        if not validation.is_file_extension_json(file.filename):
            return redirect(url_for("main_page"))

    all_dataframes = extended_history.parse_file_data(files)

    graphs = {}
    full_tables = {}
    short_tables = {}
    grouped_data = {}
    custom_graphs = {}

    for data_type in ["tracks", "albums", "artists"]:
        match data_type:
            case "artists":
                grouped_data[data_type] = all_dataframes.groupby("artist", as_index=False).size()
            case "albums" | "tracks":
                grouped_data[data_type] = all_dataframes.groupby(
                    [data_type[:-1], "artist"],
                    as_index=False
                ).size()

        grouped_data[data_type].rename(columns={"size": "scrobble count"}, inplace=True)
        grouped_data[data_type].sort_values(
            "scrobble count",
            ascending=False,
            inplace=True,
            ignore_index=True
            )
        grouped_data[data_type].index += 1

        full_tables[data_type] = visualize_data.get_html_table(grouped_data[data_type])
        short_tables[data_type] = visualize_data.get_html_table(grouped_data[data_type], 15)

        script, div = visualize_data.get_top_scrobbles_chart(
            data_type,
            grouped_data[data_type],
            True
            )

        graphs[data_type] = {
            "script": script,
            "div": div
        }

    print(all_dataframes.iloc[0]["scrobble_time"].date())
    script, div = visualize_data.get_cumulative_scrobble_stats(
        all_dataframes,
        all_dataframes["scrobble_time"].min().date(),
        all_dataframes["scrobble_time"].max().date()
        )
    custom_graphs["cumulative"] = {
        "script": script,
        "div": div
    }

    overall_stats = visualize_data.get_total_stats_from_lastfm(
        "",
        grouped_data,
        start_date=all_dataframes["scrobble_time"].min().date(),
        end_date=all_dataframes["scrobble_time"].max().date()
        )
    overall_stats_html = visualize_data.get_html_table(overall_stats)

    similar_artists_dict = get_data.all_similar_artists(grouped_data["artists"]["artist"]) \
    .head(10) \
    .to_dict(orient="records")

    session["graphs"] = graphs
    session["full_tables"] = full_tables
    session["short_tables"] = short_tables
    session["custom_graphs"] = custom_graphs
    session["overall_stats"] = overall_stats_html

    return render_template("spotify_analysis.html",
        start_date=all_dataframes["scrobble_time"].min().date(),
        end_date=all_dataframes["scrobble_time"].max().date(),
        similar_artists=similar_artists_dict
        )

@app.route("/spotify_analysis/<data_type>")
def see_more_spotify(data_type):
    "visualize the whole table"

    full_table = session.get("full_tables", {}).get(data_type)

    return render_template(
        "see_more.html",
        data_type=data_type,
        full_table=full_table,
        title=f"Full {data_type} table view"
    )

if __name__ == "__main__":
    app.run(debug=True)
