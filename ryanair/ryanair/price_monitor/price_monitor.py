from ..ryanair_api.ryanair import Ryanair
from ..ryanair_api.airport_utils import AIRPORTS
import pandas as pd
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import List

THISDIR = Path(__file__).parent

class FlightPriceMonitor:
    def __init__(self, 
                 source_airport, dest_airport, 
                 departure_dates: List[datetime] = None, 
                 return_dates: List[datetime] = None, 
                 outbound_departure_time_from: str = "00:00",
                 outbound_departure_time_to: str = "23:59",
                 inbound_departure_time_from: str = "00:00",
                 inbound_departure_time_to: str = "23:59"):
        self.source_airport = source_airport
        self.dest_airport = dest_airport
        self.departure_dates = departure_dates
        self.return_dates = return_dates
        self.base_dir = Path.home()/"ryanair_flight_monitor"
        self.historical_file = self.base_dir/"search.csv"
        self.outbound_departure_time_from = outbound_departure_time_from
        self.outbound_departure_time_to = outbound_departure_time_to
        self.inbound_departure_time_from = inbound_departure_time_from
        self.inbound_departure_time_to = inbound_departure_time_to
        
        self.ryanair = Ryanair()
        
        self.base_dir.mkdir(exist_ok=True, parents=True)
        
        if self.departure_dates is not None and self.return_dates is not None:
            if len(self.departure_dates) != len(self.return_dates):
                raise ValueError(f"num of depature dates must be equal to num of return dates")
        elif self.departure_dates is None and self.return_dates is None:
            logging.info("no departure and return dates provided")
        else:
            raise ValueError(f"must both provide both departure and return dates")

    def set_weekends_dates(self, start_date: datetime, numweeks=24):
        now = datetime.now()
        today = datetime(now.year, now.month, now.day)
        beg = datetime(start_date.year, start_date.month, start_date.day)
        deltadays = beg.weekday() - 4
        beg = beg - timedelta(days=deltadays)
        self.departure_dates = []
        self.return_dates = []
        for w in range(numweeks):
            depdate = beg + timedelta(days=int(w*7))
            retdate = depdate + timedelta(days=3)
            if depdate > today:
                self.departure_dates.append(depdate)
                self.return_dates.append(retdate)
            else:
                logging.info(f"discarding date {depdate} since it is before todaty {today.isoformat()}")
        if self.departure_dates:
            searchbeg = self.departure_dates[0].strftime('%A %d %B %Y')
            searchend = self.departure_dates[-1].strftime('%A %d %B %Y')
            logging.info(f"configured departure dates from {searchbeg} to {searchend}")
        else:
            logging.warning(f"no departure dates set for start_date {start_date.isoformat()}")
    
    def get_current_oneway_fares(self):
        results = []
        queryDatetime = datetime.now()
        for depdate in self.departure_dates:
            res = self.ryanair.get_cheapest_oneway_flights(
                self.source_airport,
                date_from=depdate,
                date_to=depdate,
                destination_airport=self.dest_airport
            )
            results.extend([trip.to_dict() for trip in res])
        
        df = pd.DataFrame(results)
        df["queryDatetime"] = queryDatetime
        
        return df
            

    def get_current_roundtrip_fares(self):
        results = []
        queryDatetime = datetime.now()
        for depdate, retdate in zip(self.departure_dates, self.return_dates):
            res = self.ryanair.get_cheapest_roundtrip_flights(
                source_airport=self.source_airport,
                date_from=depdate,
                date_to=depdate,
                return_date_from=retdate, 
                return_date_to=retdate,
                destination_airport=self.dest_airport,
                outbound_departure_time_from=self.outbound_departure_time_from,
                outbound_departure_time_to=self.outbound_departure_time_to,
                inbound_departure_time_from=self.inbound_departure_time_from,
                inbound_departure_time_to=self.inbound_departure_time_to
            )
            results.extend([trip.to_dict() for trip in res])

        df = pd.DataFrame(results)
        df["totalPrice"] = df["totalPrice"].round(2)
        df["queryDatetime"] = queryDatetime
        
        cols = [
            "totalPrice",
            "outbound.departureTime",
            "outbound.flightNumber",
            "outbound.origin", 
            "outbound.destination",
            "inbound.departureTime", 
            "inbound.flightNumber",
            "queryDatetime"
        ]
        df = df[cols]
        df["outbound.departureTime"] = pd.to_datetime(df["outbound.departureTime"])
        df["inbound.departureTime"] = pd.to_datetime(df["inbound.departureTime"])

        return df
    
    def compare_with_last_search(self, dfnew):
        if (self.base_dir/"last_search.csv").is_file():
            df = pd.read_csv(self.base_dir/"last_search.csv")
            res = pd.merge(df, dfnew, on=["outbound.departureTime", "inbound.departureTime", "outbound.flightNumber"], suffixes=("", "_new"))

            cols = [c for c in res.columns if "_new" not in c]
            cols.insert(1, "totalPrice_new")
            cols.append("queryDatetime_new")
            res = res[cols]
            res = res[res["totalPrice_new"] < res["totalPrice"]]
            
            return res
        
    def do_search(self):
        pass
    
    def update_historical_dataframe(self, currdf):
        historical = None
        