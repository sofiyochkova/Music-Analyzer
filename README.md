# Music Analyzer

## Summary
This project is a Flask web app which fetches Last.fm listening data based 
on a predefined time period (7 days, 1 month, 3 months, 6 months, 1 year or overall)
or based on a given custom timeframe - from start date to end date, and visualizes
it as charts and tables.

The project also supports uploading .json files from Spotify's extended streaming history
which you can get [here](https://www.spotify.com/uk/account/privacy/).

## Steps To Run
1. Install Python, if you haven't (preferably Python 3.13)
2. Clone the repository:
```
git clone https://github.com/sofiyochkova/Music-Analyzer.git
cd Music-Analyzer
```
3. Install all dependencies required for running the project:
```
pip install -r requrements.txt
```

4. If you have a [Last.fm](https://lastfm.com/) account, get an API key from https://www.last.fm/api/account/create and create a .env file in the root folder containing these values:
```
LASTFM_API_KEY="<your-public-key>"
LASTFM_API_SECRET="<your-private-key>"
```

5. To run the app, use either
```
python main.py
```
or
```
python3 -m flask --app main.py run
```
from the root folder of the project.

# TODO
The project is unfortunately still unfinished but I would like to implement
more functions in the near future:
1. Write tests
2. Find a way to avoid and handle Spotify rate limits
3. More graphs and charts based on data I couldn't find because of Spotify's API constraints.
