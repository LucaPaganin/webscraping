#!/usr/bin/env python
# coding: utf-8

# In[1]:


from bs4 import BeautifulSoup
import json # Importa la libreria json per stampare in modo leggibile

# Carica il file HTML
# Assicurati che il percorso del file sia corretto nel tuo ambiente
try:
    with open("new.html", encoding="utf-8") as f:
        soup = BeautifulSoup(f, "html.parser")
except FileNotFoundError:
    print("Errore: Il file HTML non è stato trovato.")


# In[2]:


# Trova tutti i blocchi che rappresentano un singolo annuncio nella lista
# Questo è il tuo selettore iniziale per ogni elemento lista annuncio
annunci = soup.select("li.nd-list__item.in-searchLayoutListItem")

# Estrai i dati richiesti da un sottoinsieme degli annunci (es. primi 5, come nel tuo codice originale)
estratti = []
# Utilizziamo enumerate per avere anche l'indice, utile per debug o messaggi
for i, annuncio in enumerate(annunci[:5]):
    print(f"Processando annuncio {i+1}...") # Messaggio per tracciare l'avanzamento

    # --- Estrazione dei dati principali (come nel tuo codice originale) ---
    prezzo_element = annuncio.select_one(".in-listingCardPrice")
    titolo_element = annuncio.select_one(".in-listingCardTitle")
    link_element = annuncio.select_one(".in-listingCardProperty a") # Selettore per l'elemento <a> del link
    immagine_element = annuncio.select_one("img")

    # Estrazione features usando il selettore originale (.in-featuresList li)
    # Rinominiamo la chiave per distinguere questa estrazione
    features_original_elements = annuncio.select(".in-featuresList li")
    caratteristiche_originali = [f.get_text(strip=True) for f in features_original_elements]
    # --- Fine estrazione dati principali ---


    # --- NUOVA estrazione delle caratteristiche usando .in-listingCardFeatureList__item span ---
    # Seleziona tutti gli elementi LI con la classe 'in-listingCardFeatureList__item'
    # Questi LI sono i singoli elementi della lista caratteristiche visibile nell'anteprima
    feature_list_items = annuncio.select(".in-listingCardFeatureList__item span")

    # Per ogni elemento trovato con quella classe, estrai il testo
    caratteristiche_anteprima = []
    for span_element in feature_list_items:
        if span_element: # Assicurati che lo span esista
             caratteristiche_anteprima.append(span_element.get_text(strip=True))
    # --- Fine NUOVA estrazione ---

    # Aggiungi tutti i dati estratti (originali e nuovi) al dizionario per questo annuncio
    estratti.append({
        "titolo": titolo_element.get_text(strip=True) if titolo_element else None,
        "prezzo": prezzo_element.get_text(strip=True) if prezzo_element else None,
        # Estrai l'attributo 'href' dall'elemento link
        "link": link_element["href"] if link_element and link_element.has_attr("href") else None,
        
        # Dati estratti con il selettore originale
        "caratteristiche_originali": caratteristiche_originali,
        
        # Nuovi dati estratti con il selettore .in-listingCardFeatureList__item span
        "caratteristiche_anteprima": caratteristiche_anteprima, # Aggiunto qui

        # Estrai l'attributo 'src' dall'elemento immagine
        "immagine": immagine_element["src"] if immagine_element and immagine_element.has_attr("src") else None
    })

# Stampa i risultati estratti in un formato JSON leggibile
print("\nDati estratti:")
print(json.dumps(estratti, indent=2, ensure_ascii=False))


# In[ ]:




