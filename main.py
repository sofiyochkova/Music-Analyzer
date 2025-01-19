from flask import Flask, render_template, url_for, request, redirect
import os
from spotipy_functions import search_artist_spotify
from lastfm_functions import check_if_user_exists

app = Flask(__name__)
app.config["TEMPLATES_AUTO_RELOAD"] = True

@app.route("/")
def main_page():
    return render_template("index.html", title="Music Analyzer Index")

@app.route("/validate_data", methods=["POST"])
def validate_data():
    if request.method != "POST":
        return redirect(url_for('/', message="Invalid method"))

    if not check_if_user_exists(request.form["username"]):
        return redirect(url_for('/', message="Last.fm username not found!"))

    if request.form["time_period"] not in ["7day", "1month", "3month", "6month", "12month", "overall", "custom"]:
        return redirect(url_for('/', message="Invalid time period!"))
    
    # TODO: check dates

    return redirect(url_for('/lastfm_analysis/<username>', title=f"{request.form["username"]} Track Analysis"))


@app.route('/lastfm_analysis/<username>')
def render(username, data):
    return render_template('lastfm_analysis.html', title=f"Last.fm Analysis of {username}")

app.run()