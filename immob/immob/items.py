# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html
from itemloaders.processors import TakeFirst, MapCompose, Join
from w3lib.html import remove_tags
import re, traceback
import scrapy

def TE(func):
    def inner(x):
        try:
            return func(x)
        except:
            print(traceback.format_exc())
            return x
    return inner

def parse_price(price):
    newprice = remove_tags(price).split()[-1]
    return re.sub(r"(\.|,\d+)", "", newprice)

def parse_surface(surface):
    return remove_tags(surface).split("m")[0]

def parse_floor(floor):
    return remove_tags(floor).replace("T", "0")

def parse_date(date):
    date = remove_tags(date)
    match = re.search(r"\d{1,2}/\d{1,2}/\d{1,4}", date)
    if match:
        return date[match.start():match.end()]
    else:
        return date

def parse_digits(numfloors):
    numfloors = remove_tags(str(numfloors))
    match = re.search(r"(\d+)", numfloors)
    if match:
        return match.groups()[0]
    else:
        return numfloors

def apply_takefirst(func, defval=None):
    def inner(x):
        val = TakeFirst()(x)
        if val is None:
            val = defval
        return func(val)
    return inner

class ImmobItem(scrapy.Item):
    # define the fields for your item here like:
    id = scrapy.Field()
    url = scrapy.Field()
    title = scrapy.Field()
    zona = scrapy.Field()
    citta = scrapy.Field()
    quartiere = scrapy.Field()
    via = scrapy.Field()
    prezzo = scrapy.Field(
        input_processor=MapCompose(parse_price),
        output_processor=Join()
    )
    superficie = scrapy.Field(
        input_processor=MapCompose(parse_surface),
        output_processor=Join()
    )
    locali = scrapy.Field(
        input_processor=MapCompose(remove_tags),
        output_processor=Join()
    )
    piano = scrapy.Field(
        input_processor=MapCompose(parse_floor),
        output_processor=Join()
    )
    bagni = scrapy.Field(
        input_processor=apply_takefirst(remove_tags, defval=""),
        output_processor=Join()
    )
    numero_piani = scrapy.Field(
        input_processor=apply_takefirst(parse_digits),
        output_processor=Join()
    )
    posti_auto = scrapy.Field(
        input_processor=apply_takefirst(remove_tags, defval=""),
        output_processor=Join()
    )
    data = scrapy.Field(
        input_processor=TakeFirst(),
        output_processor=apply_takefirst(parse_date)
    )
    stato = scrapy.Field(
        input_processor=TakeFirst(),
        output_processor=apply_takefirst(remove_tags)
    )
    spese_condominio = scrapy.Field(
        input_processor=TakeFirst(),
        output_processor=apply_takefirst(parse_digits)
    )
     

def extract_value_from_feature(text, pattern=None):
    """Extract the numeric value from a feature string"""
    if text is None:
        return None
    
    if pattern:
        match = re.search(pattern, text)
        if match:
            return match.group(1)
    
    # Default extraction - get the first number
    match = re.search(r'(\d+)', text)
    if match:
        return match.group(1)
    return text

def extract_boolean_from_feature(text, true_value="Si", false_value="No"):
    """Extract a boolean value from a feature string"""
    if text is None:
        return None
    if true_value.lower() in text.lower():
        return True
    if false_value.lower() in text.lower():
        return False
    return None

class ImmobAnnounceItem(scrapy.Item):
    """
    Comprehensive item class for immobiliare.it property listings.
    Contains both preview data (from listing pages) and detailed data (from property pages).
    """
    # --- BASIC IDENTIFICATION ---
    id = scrapy.Field()
    url = scrapy.Field()
    title = scrapy.Field(output_processor=TakeFirst())
    
    # --- PREVIEW FIELDS FROM LISTING PAGE ---
    prezzo_lista_preview = scrapy.Field()
    caratteristiche_lista_preview = scrapy.Field()
    immagine_lista_preview = scrapy.Field()
    
    # --- IDENTIFICATION AND META INFORMATION ---
    riferimento_annuncio = scrapy.Field(output_processor=TakeFirst())
    data_pubblicazione = scrapy.Field(
        input_processor=TakeFirst(),
        output_processor=apply_takefirst(parse_date)
    )
    data_aggiornamento = scrapy.Field(
        input_processor=TakeFirst(),
        output_processor=apply_takefirst(parse_date)
    )
    codice_immobiliare = scrapy.Field(output_processor=TakeFirst())
    
    # --- DESCRIPTION ---
    descrizione = scrapy.Field(output_processor=Join(' '))
    
    # --- LOCATION INFORMATION ---
    citta = scrapy.Field(output_processor=TakeFirst())
    provincia = scrapy.Field(output_processor=TakeFirst())
    regione = scrapy.Field(output_processor=TakeFirst())
    zona = scrapy.Field(output_processor=TakeFirst())
    indirizzo = scrapy.Field(output_processor=TakeFirst())
    cap = scrapy.Field(output_processor=TakeFirst())
    quartiere = scrapy.Field(output_processor=TakeFirst())
    distanza_dal_mare = scrapy.Field(output_processor=TakeFirst())
    latitudine = scrapy.Field(output_processor=TakeFirst())
    longitudine = scrapy.Field(output_processor=TakeFirst())
    
    # --- PROPERTY TYPE AND CONTRACT ---
    tipologia = scrapy.Field(output_processor=TakeFirst())
    categoria = scrapy.Field(output_processor=TakeFirst())
    contratto = scrapy.Field(output_processor=TakeFirst())
    tipo_contratto = scrapy.Field(output_processor=TakeFirst())
    tipo_proprieta = scrapy.Field(output_processor=TakeFirst())
    
    # --- MAIN PROPERTY CHARACTERISTICS ---
    superficie = scrapy.Field(
        input_processor=MapCompose(lambda x: extract_value_from_feature(x, r'(\d+(?:[\.,]\d+)?)\s*m²?')),
        output_processor=TakeFirst()
    )
    locali = scrapy.Field(
        input_processor=MapCompose(lambda x: extract_value_from_feature(x, r'(\d+)\s*local[ei]')),
        output_processor=TakeFirst()
    )
    camere_da_letto = scrapy.Field(
        input_processor=MapCompose(lambda x: extract_value_from_feature(x, r'(\d+)')),
        output_processor=TakeFirst()
    )
    camere = scrapy.Field(  # Alternative field name 
        input_processor=MapCompose(lambda x: extract_value_from_feature(x, r'(\d+)')),
        output_processor=TakeFirst()
    )
    bagni = scrapy.Field(
        input_processor=MapCompose(lambda x: extract_value_from_feature(x, r'(\d+)\s*bagn[oi]')),
        output_processor=TakeFirst()
    )
    piano = scrapy.Field(
        input_processor=MapCompose(lambda x: extract_value_from_feature(x, r'[Pp]iano\s+(\d+|terra|rialzato|seminterrato|attico)')),
        output_processor=TakeFirst()
    )
    piani_edificio = scrapy.Field(
        input_processor=MapCompose(lambda x: extract_value_from_feature(x, r'(\d+)')),
        output_processor=TakeFirst()
    )
    totale_piani_edificio = scrapy.Field(
        input_processor=MapCompose(lambda x: extract_value_from_feature(x, r'(\d+)')),
        output_processor=TakeFirst()
    )
    anno_costruzione = scrapy.Field(
        input_processor=MapCompose(lambda x: extract_value_from_feature(x, r'(\d{4})')),
        output_processor=TakeFirst()
    )
    stato = scrapy.Field(
        input_processor=TakeFirst(),
        output_processor=apply_takefirst(remove_tags)
    )
    stato_immobile = scrapy.Field(output_processor=TakeFirst())  # Alternative field name
    
    # --- PROPERTY FEATURES (BOOLEAN) ---
    ascensore = scrapy.Field(
        input_processor=MapCompose(lambda x: extract_boolean_from_feature(x, "Sì", "No")),
        output_processor=TakeFirst()
    )
    arredato = scrapy.Field(
        input_processor=MapCompose(lambda x: extract_boolean_from_feature(x, "Sì", "No")),
        output_processor=TakeFirst()
    )
    balcone = scrapy.Field(
        input_processor=MapCompose(lambda x: extract_boolean_from_feature(x, "Sì", "No")),
        output_processor=TakeFirst()
    )
    terrazzo = scrapy.Field(
        input_processor=MapCompose(lambda x: extract_boolean_from_feature(x, "Sì", "No")),
        output_processor=TakeFirst()
    )
    giardino = scrapy.Field(
        input_processor=MapCompose(lambda x: extract_boolean_from_feature(x, "Sì", "No")),
        output_processor=TakeFirst()
    )
    cantina = scrapy.Field(
        input_processor=MapCompose(lambda x: extract_boolean_from_feature(x, "Sì", "No")),
        output_processor=TakeFirst()
    )
    soffitta = scrapy.Field(
        input_processor=MapCompose(lambda x: extract_boolean_from_feature(x, "Sì", "No")),
        output_processor=TakeFirst()
    )
    taverna = scrapy.Field(
        input_processor=MapCompose(lambda x: extract_boolean_from_feature(x, "Sì", "No")),
        output_processor=TakeFirst()
    )
    mansarda = scrapy.Field(
        input_processor=MapCompose(lambda x: extract_boolean_from_feature(x, "Sì", "No")),
        output_processor=TakeFirst()
    )
    portineria = scrapy.Field(
        input_processor=MapCompose(lambda x: extract_boolean_from_feature(x, "Sì", "No")),
        output_processor=TakeFirst()
    )
    
    # --- ADDITIONAL PROPERTY FEATURES ---
    cucina = scrapy.Field(output_processor=TakeFirst())
    altre_stanze = scrapy.Field(output_processor=TakeFirst())
    posti_auto = scrapy.Field(
        input_processor=MapCompose(lambda x: extract_value_from_feature(x, r'(\d+)')),
        output_processor=TakeFirst()
    )
    box_auto = scrapy.Field(output_processor=TakeFirst())
    
    # --- COMFORT AND AMENITIES ---
    riscaldamento = scrapy.Field(output_processor=TakeFirst())
    tipo_riscaldamento = scrapy.Field(output_processor=TakeFirst())
    climatizzazione = scrapy.Field(output_processor=TakeFirst())
    vista = scrapy.Field(output_processor=TakeFirst())
    esposizione = scrapy.Field(output_processor=TakeFirst())
    orientamento = scrapy.Field(output_processor=TakeFirst())
    altre_caratteristiche = scrapy.Field()  # List field, no TakeFirst
    
    # --- SURFACE DETAILS ---
    dettaglio_superficie = scrapy.Field(output_processor=TakeFirst())
    coefficiente = scrapy.Field(output_processor=TakeFirst())
    tipo_superficie = scrapy.Field(output_processor=TakeFirst())
    superficie_commerciale = scrapy.Field(
        input_processor=MapCompose(lambda x: extract_value_from_feature(x, r'(\d+(?:[\.,]\d+)?)\s*m²?')),
        output_processor=TakeFirst()
    )
    superficie_coperta = scrapy.Field(
        input_processor=MapCompose(lambda x: extract_value_from_feature(x, r'(\d+(?:[\.,]\d+)?)\s*m²?')),
        output_processor=TakeFirst()
    )
    superficie_giardino = scrapy.Field(
        input_processor=MapCompose(lambda x: extract_value_from_feature(x, r'(\d+(?:[\.,]\d+)?)\s*m²?')),
        output_processor=TakeFirst()
    )
    superficie_terrazzo = scrapy.Field(
        input_processor=MapCompose(lambda x: extract_value_from_feature(x, r'(\d+(?:[\.,]\d+)?)\s*m²?')),
        output_processor=TakeFirst()
    )
    superficie_balcone = scrapy.Field(
        input_processor=MapCompose(lambda x: extract_value_from_feature(x, r'(\d+(?:[\.,]\d+)?)\s*m²?')),
        output_processor=TakeFirst()
    )
    
    # --- ECONOMIC INFORMATION ---
    prezzo = scrapy.Field(
        input_processor=MapCompose(parse_price),
        output_processor=TakeFirst()
    )
    prezzo_al_mq = scrapy.Field(output_processor=TakeFirst())
    spese_condominio = scrapy.Field(
        input_processor=TakeFirst(),
        output_processor=apply_takefirst(parse_digits)
    )
    spese_extra = scrapy.Field(output_processor=TakeFirst())
    cauzione = scrapy.Field(output_processor=TakeFirst())
    caparra = scrapy.Field(output_processor=TakeFirst())  # Alternative field
    
    # --- RENTAL SPECIFIC INFORMATION ---
    durata_contratto = scrapy.Field(output_processor=TakeFirst())
    disponibilita = scrapy.Field(output_processor=TakeFirst())
    requisiti = scrapy.Field(output_processor=TakeFirst())
    ideale_per = scrapy.Field(output_processor=TakeFirst())
    
    # --- ENERGY EFFICIENCY ---
    classe_energetica = scrapy.Field(output_processor=TakeFirst())
    indice_prestazione_energetica = scrapy.Field(output_processor=TakeFirst())
    consumo_energetico = scrapy.Field(output_processor=TakeFirst())
    ep_globale_non_rinnovabile = scrapy.Field(output_processor=TakeFirst())
    prestazione_inverno = scrapy.Field(output_processor=TakeFirst())
    prestazione_estate = scrapy.Field(output_processor=TakeFirst())
    
    # --- BUILDING INFORMATION ---
    tipo_edificio = scrapy.Field(output_processor=TakeFirst())
    num_unita = scrapy.Field(
        input_processor=MapCompose(lambda x: extract_value_from_feature(x, r'(\d+)')),
        output_processor=TakeFirst()
    )
    
    # --- AGENT INFORMATION ---
    agente = scrapy.Field(output_processor=TakeFirst())
    agenzia = scrapy.Field(output_processor=TakeFirst())
    
    # --- MEDIA ---
    immagini = scrapy.Field()  # List field, no TakeFirst
    
    # --- COMPATIBILITY WITH OLD FIELDS ---
    # These fields ensure backward compatibility with the original spider
    numero_piani = scrapy.Field(
        input_processor=apply_takefirst(parse_digits),
        output_processor=Join()
    )
    data = scrapy.Field(  # Generic date field
        input_processor=TakeFirst(),
        output_processor=apply_takefirst(parse_date)
    )