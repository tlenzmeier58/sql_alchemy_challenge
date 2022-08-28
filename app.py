# Import dependencies
from distutils.log import debug
import numpy as np
import sqlalchemy
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
def home():
    print("Server requested for Home")
    return (
        f"This is the climate app! <br/><br/>"
        f"Here are the routes: <br/>"
        f"/api/v1.0/precipitation<br/>"
        f"api/v1.0/station<br/>"
        f"api/v1.0/tobs<br/>"
        f"api/v1.0/temp/start/end<br/>"

    )

# Precipitation route
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

@app.route("/api/v1.0/stations")
def stations():
    session = Session(engine)
    results = session.query(Stn).all()
    station_details = list(np.ravel(results))
    return jsonify(
        station_details
    )

@app.route("/api/v1.0/tobs")
def tobs():
    session = Session(engine)
    latest_date = (
        session.query(Meas.date).order_by(Meas.date.desc()).first()
        )
    latest_date_str = str(latest_date)
    latest_date_str = re.sub("'|,", "", latest_date_str)
    latest_date_obj = dt.datetime.strptime(latest_date_str, '(%Y-%m-%d)')
    query_start_date = dt.date(latest_date_obj.year, latest_date_obj.month, latest_date_obj.day) - dt.timedelta(days=365)

    #Query station names and their observations, sorted descending, most active
    sta_list = session.query(
        Meas.station, func.count(Meas.station).group_by(Meas.station).order_by(func.count(Meas.station).desc()).all())
    station_list = sta_list[0][0]
    print(station_list)

    #Return a list of tobs for theyear before the final date
    results = (session.query(Meas.station, Meas.date, Meas.tobs).\
        filter(Meas.date>=query_start_date).filter(Meas.station == station_list).all())
    #JSON
    tobs_list = []
    line = {}
    line['Date'] = results[1]
    line['Station']=results[0]
    line['Temperature'] = int(results[2])
    return jsonify(
        tobs_list
    )

@app.route("/api/v1.0/<start>") #Min/Avg/Max for all dates after selected date
def start_only():

    session = Session(engine)
    date_max = session.query(Meas.date).order_by(Meas.date.desc()).first()
    date_max_str = str(date_max)
    date_max = re.sub("'|,","",date_max_str)
    print(date_max_str)

    date_min = session.query(Meas.date).order_by(Meas.date).first()
    date_min_str = str(date_min)
    date_min_str = re.sub("'|,","",date_min_str)
    print(date_min_str)

    #Check for user input error
    valid_date = session.query(exist().where(Meas.date == start)).scalar()
    if valid_entry:
        results = (session.query(func.min(Meas.tobs), func.avg(Meas.tobs), func.max(Meas.tobs)).filter(Meas.date >=start).all())
        tmin = results[0][0]
        tavg = '{0:.4}'.format(results[0][1])
        tmax = results[0][2]

        printout = ( ['Entered start date: ' + start,
            'The lowest temperature was ' + str(tmin) + ' F',
            'The average temperature was ' + str(tavg) + ' F',
            'The highest temperature was ' + str(tmax) + ' F'])
        return jsonify(printout)
    return jsonify({"error": f"Input date {start} not valid. Date range is {date_min_str} to {date_max_str}"}), 404


if __name__== "__main__":
    app.run(debug=True)