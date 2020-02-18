from flask import Flask, jsonify, request, render_template
from flask_sqlalchemy import SQLAlchemy
import datetime
import sqlalchemy
from sqlalchemy import and_, func
from sqlalchemy.orm import Session

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
    return render_template("HomePage.html")


@app.route("/api/v1.0/precipitation")
def show_all():
    cols = ["date", "prcp"]
    Precipitations = Measurement.query.filter(
        and_(
            Measurement.date > datetime.datetime(2016, 8, 23),
            Measurement.date <= datetime.datetime(2017, 8, 23),
        )
    )
    result1 = [{col: getattr(Precip, col) for col in cols} for Precip in Precipitations]
    result = [{r["date"]: r["prcp"]} for r in result1]
    return jsonify(result=result)


@app.route("/api/v1.0/stations")
def show_stations():
    station_names = Station.query.all()
    cols = ["name"]
    result = [{col: getattr(name, col) for col in cols} for name in station_names]
    return jsonify(result=result)


@app.route("/api/v1.0/tobs")
def show_temperature():
    cols = ["date", "tobs"]
    Temperatures = Measurement.query.filter(
        and_(
            Measurement.date > datetime.datetime(2016, 8, 23),
            Measurement.date <= datetime.datetime(2017, 8, 23),
        )
    )
    result1 = [{col: getattr(Temp, col) for col in cols} for Temp in Temperatures]
    result = [{r["date"]: r["tobs"]} for r in result1]
    return jsonify(result=result)


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
    app.run(debug=True)
