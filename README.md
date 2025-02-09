# Music Analyzer

## Summary
This project is a Flask web app which fetches Last.fm listening data based 
on a predefined time period (7 days, 1 month, 3 months, 6 months, 1 year or overall)
or based on a given custom timeframe - from start date to end date, and visualizes
it as charts and tables.

## Steps To Run
1. Install Python, if you haven't (preferably Python 3.13)
2. Install all dependecies required for running the project:
```
pip install -r requrements.txt
```

3. To run, use either
```
python main.py
```
or
```
python3 -m flask --app main.py run
```
from the root folder of the project.

# TODO
The project is unfortunately still not finished but I would like to implement
more functionality in the near future:
1. Write tests
2. Spotify listening data support
3. Find a way to avoid and handle Spotify rate limits
4. More graphs and charts based on data I couldn't find because of Spotify's API constraints.