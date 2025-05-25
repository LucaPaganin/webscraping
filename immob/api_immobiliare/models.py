from datetime import datetime
from typing import List, Dict, Optional, Any, Union
from pydantic import BaseModel, Field, field_validator  # importato field_validator invece di validator


class Phone(BaseModel):
    """Modello per rappresentare un numero di telefono."""
    type: str
    value: str


class BookableVisit(BaseModel):
    """Modello per rappresentare se una visita è prenotabile."""
    isVisitBookable: bool
    virtualVisitEnabled: bool


class ImageUrls(BaseModel):
    """Modello per rappresentare gli URL delle immagini."""
    small: Optional[str] = None
    medium: Optional[str] = None
    large: Optional[str] = None


class Agency(BaseModel):
    """Modello per rappresentare un'agenzia immobiliare."""
    id: int
    type: str
    showOnlyAgentPhone: bool
    phones: List[Phone]
    bookableVisit: BookableVisit
    isPaid: bool
    label: str
    displayName: str
    guaranteed: bool
    showAgentPhone: bool
    showLogo: bool
    imageUrls: ImageUrls
    agencyUrl: str
    showExternalLink: bool


class Supervisor(BaseModel):
    """Modello per rappresentare un supervisore (agente immobiliare)."""
    type: str
    imageGender: str
    phones: List[Phone]
    imageType: str
    displayName: str
    label: str
    imageUrl: str


class Advertiser(BaseModel):
    """Modello per rappresentare un inserzionista."""
    agency: Agency
    supervisor: Supervisor
    hasCallNumbers: bool


class Price(BaseModel):
    """Modello per rappresentare il prezzo di un immobile."""
    visible: bool
    value: int
    formattedValue: str
    minValue: str
    maxValue: Optional[str] = None
    priceRange: Optional[str] = None


class Nation(BaseModel):
    """Modello per rappresentare una nazione."""
    id: str
    name: str


class Location(BaseModel):
    """Modello per rappresentare la posizione di un immobile."""
    address: str
    latitude: float
    longitude: float
    marker: str
    region: str
    province: str
    macrozone: Optional[str] = None
    city: str
    nation: Nation


class View(BaseModel):
    """Modello per rappresentare una vista."""
    id: int
    name: str


class Typology(BaseModel):
    """Modello per rappresentare la tipologia di un immobile."""
    id: int
    name: str


class Category(BaseModel):
    """Modello per rappresentare la categoria di un immobile."""
    id: int
    name: str


class Photo(BaseModel):
    """Modello per rappresentare una foto di un immobile."""
    id: int
    caption: str
    urls: ImageUrls


class FeatureItem(BaseModel):
    """Modello per rappresentare una caratteristica."""
    type: str
    label: str
    compactLabel: Optional[str] = None


class Floor(BaseModel):
    """Modello per rappresentare il piano di un immobile."""
    abbreviation: str
    value: str
    floorOnlyValue: str
    ga4FloorValue: str


class Multimedia(BaseModel):
    """Modello per rappresentare elementi multimediali."""
    photos: List[Photo]
    virtualTours: List[Any] = []  # Nessun esempio nei dati
    hasMultimedia: bool


class PropertyDetail(BaseModel):
    """Modello per rappresentare i dettagli di una proprietà."""
    multimedia: Optional[Multimedia] = None
    bathrooms: Optional[str] = None
    floor: Optional[Floor] = None
    price: Price
    rooms: Optional[str] = None
    elevator: Optional[bool] = None
    surface: str
    typology: Typology
    typologyGA4Translation: str
    seaDistanceValue: Optional[str] = None
    views: Optional[List[View]] = None
    ga4features: List[str]
    ga4Heating: Optional[str] = None
    ga4Garage: Optional[str] = None
    caption: Optional[str] = None
    category: Optional[Category] = None
    description: Optional[str] = None
    photo: Optional[Photo] = None
    location: Optional[Location] = None
    featureList: List[FeatureItem]
    url: Optional[str] = None
    matchSearch: Optional[bool] = None


class RealEstateAd(BaseModel):
    """Modello principale per rappresentare un annuncio immobiliare."""
    visibility: str
    dataType: str
    id: int
    uuid: str
    advertiser: Advertiser
    contract: str
    isNew: bool
    luxury: bool
    price: Price
    properties: List[PropertyDetail]
    propertiesCount: int
    title: str
    type: str
    typology: Typology
    hasMainProperty: bool
    isProjectLike: bool
    isMosaic: bool


class SeoInfo(BaseModel):
    """Modello per rappresentare le informazioni SEO di un annuncio."""
    anchor: str
    url: str


class ImmobiliareListItem(BaseModel):
    """Modello per rappresentare un elemento della lista di risultati."""
    realEstate: RealEstateAd
    seo: SeoInfo
    idGeoHash: str


class ImmobiliareResponse(BaseModel):
    """Modello per rappresentare la risposta dell'API di Immobiliare.it."""
    list: Dict[str, Any]  # Struttura generica per accomodare diverse risposte API
    
    @field_validator("list", mode="before")
    def validate_list(cls, v):
        if not isinstance(v, dict):
            return {"items": []}
        return v