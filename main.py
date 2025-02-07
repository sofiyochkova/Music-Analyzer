import os
from datetime import date

from flask import Flask, render_template, url_for, request, redirect, session, flash
from werkzeug.utils import secure_filename
from flask_session.__init__ import Session

from utils import lastfm_utils, visualize_data, validation, analyze_data
from utils import extended_history

app = Flask(__name__)

UPLOAD_FOLDER = os.path.join(os.getcwd(), "uploads")
SESSION_FOLDER = os.path.join(os.getcwd(), "flask_session")

if not os.path.exists(SESSION_FOLDER):
    os.makedirs(SESSION_FOLDER, exist_ok=True)

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)

app.config["SESSION_FILE_DIR"] = SESSION_FOLDER
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["SESSION_TYPE"] = "filesystem"
app.config["SESSION_PERMANENT"] = False
app.config["TEMPLATES_AUTO_RELOAD"] = True

Session(app)

@app.route("/")
def main_page():
    messages = request.args.get("messages")
    return render_template("index.html", title="Music Analyzer Index", messages=messages)

@app.route("/validate_data", methods=["POST"])
def validate_data():
    has_flashed = False

    if not validation.request_method_is_post(request.method):
        flash("Invalid request method")
        has_flashed = True
        return redirect(url_for("main_page"))

    for field in ["username", "time_period"]:
        if not validation.is_not_empty(field):
            flash(f"Empty field value {field}!")
            has_flashed = True

    if has_flashed:
        return redirect(url_for("main_page"))

    username = request.form["username"]
    time_period = request.form["time_period"]

    if not lastfm_utils.check_if_user_exists(username):
        flash(f"Last.fm username {username} not found!")
        has_flashed = True

    if not validation.is_time_period_valid(time_period):
        flash(f"Invalid time period {time_period}!")
        has_flashed = True

    if has_flashed:
        return redirect(url_for("main_page"))

    if time_period == "custom":
        for field in ["start_date", "end_date"]:
            if not validation.is_not_empty(field):
                flash(f"Empty field {field}!")
                has_flashed = True
                return redirect(url_for("main_page"))

        start_date = request.form["start_date"]
        end_date = request.form["end_date"]

        registration_date = lastfm_utils.get_registration_date(username)

        if date.fromisoformat(start_date) < registration_date:
            flash(f"Start date {start_date} cannot be before the registration date!")
            has_flashed = True

        if date.fromisoformat(end_date) > date.today():
            flash(f"End date {end_date} cannot be in the future!")
            has_flashed = True
    else:
        start_date = None
        end_date = None

    if has_flashed:
        return redirect(url_for("main_page"))

    if time_period == "custom":
        return redirect(url_for(
        "lastfm_analysis_custom",
        username=username,
        time_period=time_period,
        start=start_date, end=end_date
        ))

    return redirect(url_for(
        "lastfm_analysis_predefined",
        username=username,
        time_period=time_period
    ))

@app.route("/lastfm_analysis/<username>/<time_period>")
def lastfm_analysis_predefined(username, time_period):
    has_flashed = False

    if not lastfm_utils.check_if_user_exists(username):
        flash(f"Username {username} not found!")
        has_flashed = True

    if not validation.is_time_period_valid(time_period):
        flash("Invalid time period!")
        has_flashed = True

    if has_flashed or time_period == "custom":
        return redirect(url_for("main_page"))

    graphs = {}
    # top_data = {}
    full_tables = {}
    short_tables = {}

    for data_type in ["tracks", "albums", "artists"]:
        top_data = lastfm_utils.get_top_data_predefined_period(username, data_type, time_period)
        full_tables[data_type] = visualize_data.get_html_table(top_data)
        short_tables[data_type] = visualize_data.get_html_table(top_data, 15)

        script, div = visualize_data.get_top_scrobbles_chart_predefined(data_type, top_data)

        graphs[data_type] = {
            "script": script,
            "div": div
        }

        # get stats based on my files - load them and take the spotify uris - get data based on them
        # should be in analyze_data

        session["graphs"] = graphs
        session["full_tables"] = full_tables
        session["short_tables"] = short_tables
        # session["overall_stats"] = overall_stats_html
        # session["tracks_table"] = tracks_table_html
        # session["artists_table"] = artists_table_html

        return render_template(
            "lastfm_analysis.html",
            title=f"{username} Track Analysis",
            username=username,
            time_period=time_period
        )

@app.route("/lastfm_analysis/<username>/custom")
def lastfm_analysis_custom(username):
    if not validation.is_not_empty(request.args.get("time_period")):
        flash("Empty time_period value!")
        return url_for("main_page")

    time_period = request.args.get("time_period")
    if time_period != "custom":
        flash(f"Invalid time_period value {time_period}!")
        return url_for("main_page")

    start_date = request.args.get("start")
    end_date = request.args.get("end")

    if not start_date or not end_date:
        flash("Missing dates for custom date period!")
        return redirect(url_for("main_page"))

    # TODO: cast start and end dates to datetime before passing them to functions
    custom_data = lastfm_utils.get_recent_tracks_by_custom_dates(username, start_date, end_date)

    graphs = {}
    full_tables = {}
    short_tables = {}

    for data_type in ["tracks", "albums", "artists"]:
        match data_type:
            case "artists":
                grouped_data = custom_data.groupby("artist", as_index=False).size()
            case "albums" | "tracks":
                grouped_data = custom_data.groupby(
                    [data_type[:-1], "artist"],
                    as_index=False
                ).size()

        grouped_data.rename(columns={"size": "scrobbles"}, inplace=True)
        grouped_data.sort_values("scrobbles", ascending=False, inplace=True, ignore_index=True)
        grouped_data.index += 1

        full_tables[data_type] = visualize_data.get_html_table(grouped_data)
        short_tables[data_type] = visualize_data.get_html_table(grouped_data, 15)

        script, div = visualize_data.get_top_scrobbles_chart_custom(data_type, grouped_data)

        graphs[data_type] = {
            "script": script,
            "div": div
        }

    # script, div = visualize_data.get_cumulative_scrobble_stats(custom_data, start_date, end_date)

    # custom_graphs = {}
    # custom_graphs["cumulative"] = {
    #     "script": script,
    #     "div": div
    # }

    session["graphs"] = graphs
    session["full_tables"] = full_tables
    session["short_tables"] = short_tables
    session["custom_graphs"] = {}#custom_graphs
    # session["overall_stats"] = overall_stats_html
    # session["tracks_table"] = tracks_table_html
    # session["artists_table"] = artists_table_html

    return render_template(
        "lastfm_analysis_custom.html",
        title=f"{username} Track Analysis",
        username=username,
        start_date=start_date,
        end_date=end_date,
        time_period=time_period
    )

@app.route("/lastfm_analysis/<username>/<data_type>")
def see_more(username, data_type):
    title = request.args.get("prev_title")
    time_period = request.args.get("time_period")
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

@app.route("/validate_files", methods=["POST"])
def validate_files():
    if "file" not in request.files:
        flash("No files uploaded!")
        return redirect(url_for("main_page"))

    files = request.files.getlist("file")
    
    for file in files:
        if not validation.is_file_extension_json(file.filename):
            flash(f"Invalid file type of file {file.filename}!")
            return redirect(url_for("main_page"))
    
    for file in files:
        filename = secure_filename(file.filename)
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

    return url_for("spotify_analysis")

@app.route("/spotify_analysis")
def spotify_analysis():
    if not os.listdir(app.config["UPLOAD_FOLDER"]):
        flash("No files uploaded yet!")
        return redirect(url_for("main_page"))

    all_dataframes = extended_history.parse_file_data()    
    print(all_dataframes)

    if all_dataframes:
        return render_template("spotify_analysis.html")
app.run(debug=True)
