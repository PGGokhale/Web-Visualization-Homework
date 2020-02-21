from flask import Flask, jsonify, request, render_template
from flask_sqlalchemy import SQLAlchemy
import datetime
import sqlalchemy
from sqlalchemy import and_, func
from sqlalchemy.orm import Session
from plot import plot
from plot1 import plot1
import pandas as pd

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///Resources/hawaii.sqlite"
db = SQLAlchemy(app)


class DictMixIn:
    def to_dict(self):
        return {
            column.name: getattr(self, column.name)
            if not isinstance(getattr(self, column.name), datetime.datetime)
            else getattr(self, column.name).isoformat()
            for column in self.__table__.columns
        }


class Measurement(db.Model, DictMixIn):
    __tablename__ = "measurement"
    id = db.Column(db.Integer(), primary_key=True)
    station = db.Column(db.String())
    date = db.Column(db.String())
    prcp = db.Column(db.Float())
    tobs = db.Column(db.Float())


class Station(db.Model, DictMixIn):
    __tablename__ = "station"
    id = db.Column(db.Integer(), primary_key=True)
    station = db.Column(db.String())
    name = db.Column(db.String())
    latitude = db.Column(db.Float())
    longitude = db.Column(db.Float())
    elevation = db.Column(db.Float())


def calc_temps(start_date, end_date):
    """TMIN, TAVG, and TMAX for a list of dates.
    
    Args:
        start_date (string): A date string in the format %Y-%m-%d
        end_date (string): A date string in the format %Y-%m-%d
        
    Returns:
        TMIN, TAVE, and TMAX
    """

    Temperatures = (
        db.session.query(
            func.min(Measurement.tobs),
            func.avg(Measurement.tobs),
            func.max(Measurement.tobs),
        )
        .filter(Measurement.date >= start_date)
        .filter(Measurement.date <= end_date)
        .all()
    )

    return Temperatures


@app.route("/")
def home():
    return render_template("index.html")

@app.route("/temperature")
def render_plot():
    return render_template("temperature.html", plot_data=plot())

@app.route("/precipitation")
def render_plot1():
    return render_template("precipitation.html", plot_data=plot1())

@app.route("/data")
def render_data():

    items = db.session.query(
        Measurement.prcp,
        Measurement.tobs,
        Measurement.station,
        Station.name,
        Station.latitude,
        Station.longitude,
        Station.elevation,
    ).filter(Measurement.station == Station.station)\
    .filter(
        and_(
            Measurement.date > datetime.datetime(2016, 8, 23),
            Measurement.date <= datetime.datetime(2017, 8, 23),
        )
    ).all()

    df_rainfall = pd.DataFrame(
        [
            {
                "Rainfall": item[0],
                "Temperature":item[1],
                "Station": item[2],
                "Name": item[3],
                "Latitude": item[4],
                "Longitude": item[5],
                "Elevation": item[6],
            }
            for item in items
        ]
    )
    table = df_rainfall.to_html()
    return render_template("pandas.html",table=table)


def validate(date_text):
    try:
        datetime.datetime.strptime(date_text, "%Y-%m-%d")
    except ValueError:
        raise ValueError("Incorrect date format, should be YYYY-MM-DD")


@app.route("/api/v1.0")
def filter_temp_by_date():

    request_start = request.args.get("start")
    request_end = request.args.get("end")

    try:

        if request_start:
            validate(request_start)
            start_date = request_start
        else:
            return "Please enter the start date"

        if request_end:
            validate(request_end)
            end_date = request_end

        else:
            max_date = db.session.query(func.max(Measurement.date)).all()
            end_date = [date[0] for date in max_date]
            end_date = end_date[0]
        if end_date > start_date:
            data = calc_temps(start_date, end_date)
        else:
            return "End date should be greater than start date"

        list_stat = [[temp[0], temp[1], temp[2]] for temp in data][0]
        tmin = list_stat[0]
        tavg = list_stat[1]
        tmax = list_stat[2]
        if tmin is None or tavg is None or tmax is None:
            return "Temperatures not found!", 404
        else:
            return jsonify({"Tmin": tmin, "Tavg": tavg, "Tmax": tmax})

    except Exception as e:
        return jsonify({"status": "failure", "error": str(e)})


if __name__ == "__main__":
    app.run()
