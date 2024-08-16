from ryanair.price_monitor import FlightPriceMonitor
import pandas as pd
from datetime import datetime
import logging, sys

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)

if __name__ == '__main__':
    src = "GOA"
    dst = "NAP"
    
    departure_dates = [
        datetime(2025, 1, 3)
    ]
    return_dates = [
        datetime(2025, 1, 6)
    ]
        
    m = FlightPriceMonitor(
        source_airport=src, dest_airport=dst,
        departure_dates=departure_dates,
        return_dates=return_dates
    )    
    
    df = m.get_current_roundtrip_fares()
    
    df.to_csv("flightdata.csv", index=False)