from pydantic import BaseModel
from typing import Optional

class CaratteristicheImmobile(BaseModel):
    """
    Modello Pydantic per rappresentare le caratteristiche di un immobile.
    """
    url: Optional[str] = None
    titolo: Optional[str] = None
    descrizione: Optional[str] = None
    indirizzo: Optional[str] = None
    comune: Optional[str] = None
    provincia: Optional[str] = None
    zona: Optional[str] = None
    tipologia: Optional[str] = None
    piano: Optional[str] = None
    ascensore: Optional[str] = None
    locali: Optional[str] = None
    cucina: Optional[str] = None
    arredato: Optional[str] = None
    terrazzo: Optional[str] = None
    climatizzazione: Optional[str] = None
    contratto: Optional[str] = None
    piani_edificio: Optional[str] = None
    superficie: Optional[str] = None
    camere_da_letto: Optional[str] = None
    bagni: Optional[str] = None
    balcone: Optional[str] = None
    riscaldamento: Optional[str] = None
    altre_caratteristiche: Optional[str] = None
    prezzo: Optional[str] = None
    prezzo_al_mq: Optional[str] = None # Usato mq al posto di m² per compatibilità nei nomi delle variabili
    spese_condominio: Optional[str] = None
    cauzione: Optional[str] = None
    consumo_di_energia: Optional[str] = None


class Immobili(BaseModel):
    """
    Modello Pydantic per rappresentare una lista di immobili.
    """
    immobili: list[CaratteristicheImmobile] = []