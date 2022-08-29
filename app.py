import json
import numpy as np
import sqlalchemy
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import Session
from sqlalchemy import create_engine, func

from flask import Flask, jsonify
import datetime as dt

#Database setup
engine = create_engine("sqlite:///Resources/hawaii.sqlite")

#Mirror mirror on the wall, can we reflect at all?
Base = automap_base()
Base.prepare(engine, reflect=True)

#Saving references to objects
Measurement = Base.classes.measurement
Station = Base.classes.station

#Flask setup
app = Flask(__name__)

#Flask routes
@app.route("/")
def welcome():
    """List availble api routes"""
    return (
        f"Available routes:<br>"
        f"/api/v1.0/precipitation</a><br>"
        f"/api/v1.0/stations</a><br>"
        f"/api/v1.0/tobs</a><br>"
        f"/api/v1.0/start<br>"
        f"/api/v1.0/start/end"
    )
@app.route("/api/v1.0/precipitation")
def precipitation():
    #Create session
    session = Session(engine)

    """Return a list of dates and precipitation"""
    #Query all precipitation
    results = session.query(Measurement.date,Measurement.prcp).all()

    session.close()

    #Convert list of tuples into normal list
    all_dates_prcp = []
    for date, precip in results:
        date_dict = {}
        date_dict[date] = precip
        all_dates_prcp.append(date_dict)
    return jsonify(all_dates_prcp)

@app.route("/api/v1.0/stations")
def stations():
    #Create session
    session = Session(engine)

    """Return a list of stations"""
    #Query all stations
    results = session.query(Station.station, Station.name).all()

    session.close()

    #Convert list of tuples into normal list.
    all_stations = list(np.ravel(results))

    return jsonify(all_stations)

#Query for dates and temps from a year from the last data point
@app.route("/api/v1.0/tobs")
def tobs():
    # Create our session (link) from Python to the DB
    session = Session(engine)

    """Return a list of tobs for the last year of data in the table"""
    query_date = dt.date(2017, 8, 23) - dt.timedelta(days=365)

    results = session.query(Measurement.station, Measurement.tobs).\
        filter(Measurement.date >= query_date).all()
        
    session.close()

    # Convert list of tuples into normal list
    all_tobs = list(np.ravel(results))

    return jsonify(all_tobs)

#Create function to validate input as a specific date format -- YYYY-MM-DD
def validate(date_text):
    try:
        dt.datetime.strptime(date_text, '%Y-%m-%d')
    except ValueError:
        raise ValueError("Oops, incorrect date format, should be YYYY-MM-DD")

#When provided the start date only, calculate the tmin, tavg, & tmax for all date greater than or equal to the start date
@app.route("/api/v1.0/<startDate>")
def temp_date_end(startDate):
    """Fetch the tmin, tavg, tmax given a start date, variables provided by the user or a 404 if not."""

    if isinstance(startDate,str):
        print(f"A date passed, determine aggregate functions over date range")
        validate(startDate)
        #Create session
        session = Session(engine)

        results = session.query(func.min(Measurement.tobs), func.avg(Measurement.tobs), \
            func.max(Measurement.tobs)).filter(Measurement.date >= startDate).first()
        
        session.close()

        #Convert to list
        agg_temps = list(np.ravel(results))
        return jsonify(agg_temps)
    return jsonify({"error": "Date(s) not found."}), 404

#When provided the start & end date -- separated by "/" -- calculate the tmin, tavg, & tmax for selected dates
@app.route("/api/v1.0/<startDate>/<endDate>")
def temp_date_range(startDate,endDate):
    """Fetch the tmin, tavg, and tmax given a date range"""

    if isinstance(endDate,str):
        print(f"Both dates passed, determine the aggregates")
        validate(startDate)
        validate(endDate)

        #Create session
        session = Session(engine)

        results = session.query(func.min(Measurement.tobs), func.avg(Measurement.tobs), \
            func.max(Measurement.tobs)).filter(Measurement.date >= startDate).filter(Measurement.date <= endDate).first()
        
        session.close()

        #Convert to list
        agg_temps = list(np.ravel(results))

        return jsonify(agg_temps)
    return jsonify({"error": "Date(s) not found."}), 404
    
if __name__ == '__main__':
    app.run(debug=True)