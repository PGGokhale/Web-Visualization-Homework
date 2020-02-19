
import datetime
import sqlalchemy
from sqlalchemy import and_, func, create_engine
from sqlalchemy import Column, Integer, String, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Session

import pandas as pd
import os
import json
import plotly
import plotly.graph_objects as go


engine = create_engine("sqlite:///Resources/hawaii.sqlite", echo=False)

session = Session(engine)

Base = declarative_base()

class DictMixIn:
    def to_dict(self):
        return {
            column.name: getattr(self, column.name)
            if not isinstance(getattr(self, column.name), datetime.datetime)
            else getattr(self, column.name).isoformat()
            for column in self.__table__.columns
        }


class Measurement(Base, DictMixIn):
    __tablename__ = "measurement"
    id = Column(Integer, primary_key=True)
    station = Column(String)
    date = Column(String)
    prcp = Column(Float)
    tobs = Column(Float)


class Station(Base, DictMixIn):
    __tablename__ = "station"
    id = Column(Integer, primary_key=True)
    station = Column(String)
    name = Column(String)
    latitude = Column(Float)
    longitude =Column(Float)
    elevation = Column(Float)




def load_agg_data():

    cols = ["date", "prcp"]
    Temperatures = session.query(Measurement.date, Measurement.tobs, Measurement.prcp).filter(
        and_(
            Measurement.date > datetime.datetime(2016, 8, 23),
            Measurement.date <= datetime.datetime(2017, 8, 23),
        )
    ).all()
    
    result1 = [{col: getattr(Temp, col) for col in cols} for Temp in Temperatures]
  
   
    df = pd.DataFrame(result1)
    df = df.assign(date1=pd.to_datetime(df["date"]))

    return df


def plot1():

   
    df = load_agg_data()
       

    data = [go.Scatter(x=df['date1'], y=df['prcp'],mode='markers',marker=dict(
            color='LightSkyBlue',
            size=5,
            opacity=0.5,
            line=dict(
                color='orangered',
                width=2)))
            ]

    return json.dumps(data, cls=plotly.utils.PlotlyJSONEncoder)


if __name__ == "__main__":
    print(plot1())
