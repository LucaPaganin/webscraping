from datetime import datetime
from dataclasses import dataclass

@dataclass
class Flight:
    departureTime: datetime
    flightNumber: str
    price: float
    currency: str
    origin: str
    originFull: str
    destination: str
    destinationFull: str

    def to_dict(self):
        return {
            "departureTime": self.departureTime,
            "flightNumber": self.flightNumber,
            "price": self.price,
            "currency": self.currency,
            "origin": self.origin,
            "originFull": self.originFull,
            "destination": self.destination,
            "destinationFull": self.destinationFull,
        }


@dataclass
class Trip:
    totalPrice: float
    outbound: Flight
    inbound: Flight
    
    def to_dict(self):
        return {
            "totalPrice": self.totalPrice,
            **{f"outbound.{k}": v for k, v in self.outbound.to_dict().items()},
            **{f"inbound.{k}": v for k, v in self.inbound.to_dict().items()}
        }