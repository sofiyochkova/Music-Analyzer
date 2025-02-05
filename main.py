import json
import os
from datetime import date

from flask import Flask, render_template, url_for, request, redirect, session
from utils import lastfm_utils, spotipy_utils, visualize_data, validation
from flask_session import Session

app = Flask(__name__)

SESSION_FOLDER = os.path.join(os.getcwd(), "flask_session")

if not os.path.exists(SESSION_FOLDER):
    os.makedirs(SESSION_FOLDER, exist_ok=True)

app.config["SESSION_FILE_DIR"] = SESSION_FOLDER
app.config["SESSION_TYPE"] = "filesystem"
app.config["SESSION_PERMANENT"] = False
app.config["TEMPLATES_AUTO_RELOAD"] = True

Session(app)

# app.secret_key = os.urandom(24)

@app.route("/")
def main_page():
    messages = request.args.get("messages")
    return render_template("index.html", title="Music Analyzer Index", messages=messages)

@app.route("/validate_data", methods=["POST"])
def validate_data():
    messages = []

    if request.method != "POST":
        messages.append("Invalid request method")
        return redirect(url_for("main_page", messages=messages))

    for field in ["username", "time_period"]:
        if not validation.check_not_empty(field):
            messages += f"Empty field value {field}!"

    if messages:        
        return redirect(url_for("main_page", messages=messages))
            
    username = request.form["username"]
    time_period = request.form["time_period"]

    if not lastfm_utils.check_if_user_exists(username):
        messages.append(f"Last.fm username {username} not found!")
    
    if not validation.check_time_period(time_period):
        messages.append(f"Invalid time period {time_period}!")

    if time_period == "custom":
        for field in ["start_date", "end_date"]:
            if not check_not_empty(field):
                messages.append(f"Empty field {field}!")

            if messages:        
                return redirect(url_for("main_page", messages=messages))

        start_date = request.form["start_date"]
        end_date = request.form["end_date"]
        
        registration_date = lastfm_utils.get_registration_date(username)

        if date.fromisoformat(start_date) < registration_date:
            messages.append(f"Start date {start_date} cannot be before the registration date!")

        if date.fromisoformat(end_date) > date.today():
            messages.append(f"End date {end_date} cannot be in the future!")
    else:
        start_date = None
        end_date = None

    if messages:        
        return redirect(url_for("main_page", messages=messages))

    return redirect(url_for('lastfm_analysis', username=username, time_period=time_period, start=start_date, end=end_date))

@app.route('/lastfm_analysis/<username>')
def lastfm_analysis(username):
    time_period = request.args.get("time_period")
    messages = []

    if not lastfm_utils.check_if_user_exists(username):
        messages.append(f"Username {username} not found!")

    if not validation.check_time_period(time_period):
        messages.append("Invalid time period!")

    if messages:    
        return redirect(url_for("main_page", messages=messages))

    graphs: dict[str, pd.DataFrame] = {}
    full_tables = {}
    short_tables = {}

    # TODO: check if we receive a tuple
    for data_type in ["tracks", "albums", "artists"]: 
        top_data = lastfm_utils.get_top_data_predefined_time_period(username, data_type, time_period)
        full_tables[data_type] = visualize_data.get_html_table(top_data, data_type + "_full_table")
        short_tables[data_type] = visualize_data.get_html_table(top_data, data_type + "_short_table", 15)
        
        script, div = visualize_data.get_data_scrobbles_chart(data_type, top_data)
        
        graphs[data_type] = {
            "script": script,
            "div": div
        }

    if time_period == "custom":
        start_date = request.args.get("start")
        end_date = request.args.get("end")

        if not start_date or not end_date:
            return redirect(url_for("main_page", message="Missing dates for custom date period!"))

        return render_template(
            'lastfm_analysis.html',
            title=f"{username} Track Analysis",
            username=username,
            start_date=start_date,
            end_date=end_date,
            graphs=graphs,
            tables=tables
        )
    
    session["graphs"] = graphs
    session["full_tables"] = full_tables
    session["short_tables"] = short_tables

    return render_template(
        'lastfm_analysis.html',
        title=f"{username} Track Analysis",
        username=username,
        time_period=time_period
    )

@app.route("/lastfm_analysis/<username>/<data_type>")
def see_more(username, data_type):
    title = request.args.get("prev_title")
    time_period = request.args.get("time_period")
    full_table = session.get("full_tables", {}).get(data_type)
    # print(full_table)
    
    return render_template(
        "see_more.html",
        username=username,
        time_period=time_period,
        prev_title=title,
        data_type=data_type,
        full_table=full_table,
        title=f'Full {data_type} table view'
    )

app.run(debug=True)
