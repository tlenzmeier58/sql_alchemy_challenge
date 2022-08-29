# Import dependencies
from distutils.log import debug
from genericpath import exists
from time import strptime
import numpy as np
import sqlalchemy
import re
import datetime as dt
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import Session
from sqlalchemy import create_engine, func
from flask import Flask, jsonify

#Database setup
engine = create_engine("sqlite:///Resources/hawaii.sqlite")

# Reflect the db in a new model
Base = automap_base()
# reflect the tables
Base.prepare(engine, reflect=True)

Stn = Base.classes.station
Meas = Base.classes.measurement

#Flask setup
app = Flask(__name__)

#Define routes
@app.route("/")
def welcome():
    """A list of all available routes"""
    return (
        f"Here are the routes: <br/>"
        f"/api/v1.0/precipitation<br/>"
        f"/api/v1.0/stations<br/>"
        f"/api/v1.0/tobs<br/>"
        f"/api/v1.0/start<br/>"
        f"/api/v1.0/end (enter as YYYY-MM-DD)"

    )

# Precipitation route -- Convert query results to a dictionary using date as the key and tobs as the value.
@app.route("/api/v1.0/precipitation")
def precipitation():
    #create session
    session = Session(engine)
    #Query the measurements table
    results = (session.query(Meas.date, Meas.tobs).order_by(Meas.date))

    #Create a dictionary
    precip_date_tobs = []
    for each_row in results:
        dt_dict = {}
        dt_dict['date'] = each_row.date
        dt_dict['tobs'] = each_row.tobs
        precip_date_tobs.append(dt_dict)
    return jsonify(
        precip_date_tobs
        )

@app.route("/api/v1.0/stations") #A JSON listing of stations.
def stations():
    session = Session(engine)

    results = session.query(Stn.name).all()

    # 'tuple-ize' into a 'normal' list
    station_details = list(np.ravel(results))
    return jsonify(
        station_details
    )

@app.route("/api/v1.0/tobs") # Query the dates and temperature observations of the most active station for the last year of data
def tobs():
    session = Session(engine)

    latest_date = (
        session.query(Meas.date).order_by(Meas.date.desc()).first()
        )
    latest_date_str = str(latest_date)
    latest_date_str = re.sub("'|,", "",latest_date_str)
    latest_date_obj = dt.datetime.strptime(latest_date_str, '(%Y-%m-%d)')
    query_start_date = dt.date(latest_date_obj.year, latest_date_obj.month, latest_date_obj.day) - dt.timedelta(days=365)

    #Query station names and their observations, sorted descending, most active
    query_sta_list = (session.query(Meas.station, func.count(Meas.station)).group_by(Meas.station).order_by(func.count(Meas.station).desc()).all())

    station_list = query_sta_list[0][0]
    print(station_list)

    #Return a list of tobs for the year before the final date
    results = (
        session.query(Meas.station, Meas.date, Meas.tobs).\
        filter(Meas.date>=query_start_date).filter(Meas.station == station_list).all()
        )

    #JSON results
    tobs_list = []
    for results in results:
        line = {}
        line['Date'] = results[1]
        line['Station']=results[0]
        line['Temperature'] = int(results[2])
        tobs_list.append(line)
    return jsonify(
        tobs_list
    )

# Create function to validate input as specific date format YYYY-MM-DD
def validate(date_text):
    try:
        dt.datetime.strptime(date_text, '%Y-%m-%d')
    except ValueError:
        raise ValueError("Incorrect data format, should be YYYY-MM-DD")


# When given the start only, calculate TMIN, TAVG, and TMAX for all dates greater than and equal to the start date.
@app.route("/api/v1.0/<startDate>")
def temp_date_end(startDate):
    """Fetch the TMIN, TAVG and TMAX given a  start/end date
       variables supplied by the user, or a 404 if not."""
    
    if isinstance(startDate,str):
        print(f"One date passed - Determine agg funcs over date range")
        validate(startDate)
        
        session = Session(engine)

        results = session.query(func.min(Meas.tobs),func.avg(Meas.tobs),func.max(Meas.tobs)).filter(Meas.date >= startDate).first()
        
        session.close()

        # Convert list of tuples into normal list
        temps_agg = list(np.ravel(results))

        return jsonify(temps_agg)
    return jsonify({"error": "Dates not found."}), 404


@app.route("/api/v1.0/<startDate>/<endDate>")
def temp_date_range(startDate,endDate):
    """Fetch the TMIN, TAVG and TMAX given a  start/end date
       variables supplied by the user, or a 404 if not."""
    
    if isinstance(endDate,str):
        print(f"Both Dates passed - Determine agg funcs over date range")
        validate(startDate)
        validate(endDate)
        # Create our session (link) from Python to the DB
        session = Session(engine)

        results = session.query(func.min(Meas.tobs),func.avg(Meas.tobs), \
            func.max(Meas.tobs)).filter(Meas.date >= startDate).filter(Meas.date <= endDate).first()
        
        session.close()

        # Convert list of tuples into normal list
        temps_agg = list(np.ravel(results))

        return jsonify(temps_agg)
    return jsonify({"error": "Dates not found."}), 404


if __name__== "__main__":
    app.run(debug=True)