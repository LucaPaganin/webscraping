from ryanair_api.ryanair import Ryanair
from ryanair_api.airport_utils import AIRPORTS
import pandas as pd
from datetime import datetime, date, time, timedelta
from pathlib import Path
from typing import List

THISDIR = Path(__file__).parent

class FlightPriceMonitor:
    def __init__(self, 
                 source_airport, dest_airport, 
                 departure_dates: List[datetime], 
                 return_dates: List[datetime]):
        self.source_airport = source_airport
        self.dest_airport = dest_airport
        self.departure_dates = departure_dates
        self.return_dates = return_dates
        self.history_data = None
        self.currDatetime = datetime.now()
        self.ryanair = Ryanair()
        
        if len(self.departure_dates) != len(self.return_dates):
            raise ValueError(f"num of depature dates must be equal to num of return dates")
    
    def get_current_roundtrip_fares(self):
        results = []
        for depdate, retdate in zip(self.departure_dates, self.return_dates):
            res = self.ryanair.get_cheapest_roundtrip_flights(
                source_airport=self.source_airport,
                date_from=depdate,
                date_to=depdate,
                return_date_from=retdate, 
                return_date_to=retdate,
                destination_airport=self.dest_airport
            )
            results.extend([trip.to_dict() for trip in res])

        df = pd.DataFrame(results)
        df["querydatetime"] = self.currDatetime
        return df


if __name__ == '__main__':
    src = "GOA"
    dst = "NAP"
    dates = [
        (datetime(2024, 8, 2), datetime(2024, 8, 5))
    ]
    for w in range(1, 13):
        newbeg = dates[-1][0] + timedelta(days=7)
        newend = dates[-1][1] + timedelta(days=7)
        dates.append((newbeg, newend))
    
    dep_dates = [c[0] for c in dates]
    ret_dates = [c[1] for c in dates]
    
    m = FlightPriceMonitor(
        source_airport=src, dest_airport=dst, 
        departure_dates=dep_dates, return_dates=ret_dates
    )
    
    df = m.get_current_roundtrip_fares()
    
    df.to_csv("flightdata.csv", index=False)
    
    
    
    
    