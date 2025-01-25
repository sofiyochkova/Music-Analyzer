from flask import Flask, render_template, url_for, request, redirect
import os

from lastfm_functions import check_if_user_exists, get_registration_date
from datetime import date
from validation import check_if_empty

app = Flask(__name__)
app.config["TEMPLATES_AUTO_RELOAD"] = True

@app.route("/")
def main_page():
    message = request.args.get("message")
    return render_template("index.html", title="Music Analyzer Index", message=message)

# TODO: refactor the validation to look cleaner
@app.route("/validate_data", methods=["POST"])
def validate_data():
    if request.method != "POST":
        return redirect(url_for("main_page", message="Invalid request method"))

    for field in ["username", "time_period"]:
        if not check_if_empty(field):
            return redirect(url_for("main_page", message=f"Empty field value {field}!"))
            
    username = request.form["username"]
    time_period = request.form["time_period"]

    if not check_if_user_exists(username):
        return redirect(url_for('main_page', message="Last.fm username not found!"))
    
    if time_period not in ["7day", "1month", "3month", "6month", "12month", "overall", "custom"]:
        return redirect(url_for('main_page', message="Invalid time period!"))

    if time_period == "custom":
        for field in ["start_date", "end_date"]:
            if not check_if_empty(field):
                return redirect(url_for("main_page", message=f"Empty field value {field}!"))

        start_date = request.form["start_date"]
        end_date = request.form["end_date"]
        registration_date = get_registration_date(username)

        if date.fromisoformat(start_date) < registration_date:
            return redirect(url_for("main_page", message="Invalid start date!"))

        if date.fromisoformat(end_date) > date.today():
            return redirect(url_for("main_page", message="Invalid end date!"))

        dates = (start_date, end_date)
    else:
        dates = ()

    return redirect(url_for('lastfm_analysis', username=username, time_period=time_period, dates=dates))

@app.route('/lastfm_analysis/<username>')
def lastfm_analysis(username):
    # TODO: validation
    time_period = request.args.get("time_period")

    if time_period == "custom":
        start_date, end_date = request.args.get("dates")
        return render_template('lastfm_analysis.html', title=f"{username} Track Analysis", username=username, start_date=start_date, end_date=end_date)
    else:
        return render_template('lastfm_analysis.html', title=f"{username} Track Analysis", username=username)

app.run(debug=True)